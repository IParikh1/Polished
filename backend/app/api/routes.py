"""
API routes for Polished resume review service.
Uses Redis for session storage with 24-hour auto-expiry.
Supports both authenticated (Cognito) and anonymous users.
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    ChatRequest, ChatResponse, ResumeUploadResponse,
    Message, MessageRole, UsageInfo
)
from app.services.resume_parser import parse_resume
from app.services.resume_agent import resume_agent
from app.services.session_store import session_store
from app.services.context_manager import context_manager
from app.services.rate_limiter import rate_limiter, PlanType
from app.services.response_cache import response_cache, get_generic_advice
from app.core.auth import get_auth_context, AuthContext

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_id(x_user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Get user ID for rate limiting. Falls back to session ID for anonymous users."""
    return x_user_id or session_id or "anonymous"


def get_user_plan(x_user_plan: Optional[str] = None) -> PlanType:
    """Get user plan from header. Defaults to FREE."""
    if x_user_plan:
        try:
            return PlanType(x_user_plan.lower())
        except ValueError:
            pass
    return PlanType.FREE


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    auth: AuthContext = Depends(get_auth_context),
    x_user_id: Optional[str] = Header(None),
    x_user_plan: Optional[str] = Header(None)
):
    """
    Upload and analyze a resume.
    Creates a new session that auto-expires in 24 hours.
    Supports both authenticated (Cognito JWT) and anonymous users.
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())

        # Use auth context if authenticated, otherwise fall back to headers
        if auth.is_authenticated:
            user_id = auth.user_id
            plan = auth.plan
            logger.info(f"Authenticated upload by user {user_id[:8]}... (plan: {plan.value})")
        else:
            user_id = get_user_id(x_user_id, session_id)
            plan = get_user_plan(x_user_plan)

        # Check rate limit
        allowed, usage_info = rate_limiter.check_and_increment(user_id, plan)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Rate limit exceeded",
                    "usage": usage_info
                }
            )

        # Read and parse file
        content = await file.read()
        resume_text = parse_resume(content, file.filename or "resume.txt")

        # Create session in Redis (24h TTL)
        session_store.create_session(session_id, resume_text)

        # Get initial analysis
        initial_analysis = resume_agent.analyze_resume(resume_text)

        # Store initial analysis in session
        session_store.add_message(
            session_id,
            role="assistant",
            content=initial_analysis,
            tokens=context_manager.estimate_tokens(initial_analysis)
        )

        logger.info(f"Created session {session_id[:8]}... for resume upload")

        return ResumeUploadResponse(
            session_id=session_id,
            message="Resume uploaded and analyzed successfully. Session expires in 24 hours.",
            resume_text=resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
            initial_analysis=initial_analysis,
            usage=usage_info
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process resume")


def detect_correction(message: str) -> bool:
    """Detect if user message contains a correction."""
    correction_indicators = [
        "i did not", "i didn't", "that's wrong", "that's incorrect", "not correct",
        "actually,", "correction:", "wrong", "incorrect", "i never", "not true",
        "that's not right", "i don't have", "i haven't", "my actual", "the correct",
        "should be", "is actually", "isn't right", "was not", "wasn't",
        "i do not", "not accurate", "mistake", "error", "fix that"
    ]
    message_lower = message.lower()
    return any(indicator in message_lower for indicator in correction_indicators)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Continue conversation with the resume agent.
    Session must exist and not be expired.
    Uses response caching for generic questions to reduce API costs.
    """
    try:
        # Get session from Redis
        session = session_store.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired. Please upload your resume again."
            )

        # Detect and store corrections
        if detect_correction(request.message):
            session_store.add_correction(request.session_id, request.message)
            logger.info(f"User correction detected in session {request.session_id[:8]}...")

        # Add user message to session
        user_tokens = context_manager.estimate_tokens(request.message)
        session_store.add_message(
            request.session_id,
            role="user",
            content=request.message,
            tokens=user_tokens
        )

        # Check for generic advice first (no API call needed)
        generic_response = get_generic_advice(request.message)
        if generic_response:
            logger.info(f"Serving generic advice for: {request.message[:50]}...")
            response = generic_response
        else:
            # Check response cache for similar questions
            cached_response = response_cache.get_cached_response(request.message)
            if cached_response:
                logger.info(f"Cache hit for: {request.message[:50]}...")
                response = cached_response
            else:
                # Refresh session data after adding message
                session = session_store.get_session(request.session_id)

                # Get response from Claude
                history_messages = [
                    Message(role=MessageRole(m["role"]), content=m["content"])
                    for m in session.get("messages", [])[:-1]  # Exclude message we just added
                ]

                response = resume_agent.chat(
                    request.message,
                    history_messages,
                    session.get("resume_text"),
                    session.get("corrections", [])
                )

                # Cache cacheable responses for future use
                response_cache.cache_response(request.message, response)

        # Store assistant response
        response_tokens = context_manager.estimate_tokens(response)
        session_store.add_message(
            request.session_id,
            role="assistant",
            content=response,
            tokens=response_tokens
        )

        # Track token usage for cost monitoring
        context_manager.track_usage(
            request.session_id,
            user_tokens,
            response_tokens
        )

        return ChatResponse(
            response=response,
            session_id=request.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response")


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get session information.
    Returns metadata only, not full resume content.
    """
    info = session_store.get_session_info(session_id)
    if not info:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )

    # Add TTL info
    ttl = session_store.get_ttl(session_id)
    if ttl:
        info["ttl_seconds"] = ttl
        info["ttl_hours"] = round(ttl / 3600, 1)

    return info


@router.post("/improve")
async def suggest_improvements(
    session_id: str,
    target_role: str,
    target_company: Optional[str] = None
):
    """Get targeted improvement suggestions."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )

    resume_text = session.get("resume_text")
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume found in session"
        )

    suggestions = resume_agent.suggest_improvements(
        resume_text,
        target_role,
        target_company
    )

    return {"suggestions": suggestions}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Explicitly delete a session.
    Users can delete their data before the 24h auto-expiry.
    """
    if session_store.session_exists(session_id):
        session_store.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    return {"message": "Session not found (may have already expired)"}


@router.get("/usage")
async def get_usage(
    auth: AuthContext = Depends(get_auth_context),
    x_user_id: Optional[str] = Header(None),
    x_user_plan: Optional[str] = Header(None)
):
    """Get current usage information for rate limiting."""
    if auth.is_authenticated:
        user_id = auth.user_id
        plan = auth.plan
    else:
        user_id = get_user_id(x_user_id)
        plan = get_user_plan(x_user_plan)

    usage = rate_limiter.get_usage(user_id, plan)
    usage["authenticated"] = auth.is_authenticated
    if auth.user:
        usage["email"] = auth.user.email
    return usage


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Redis connection
    redis_ok = session_store.redis is not None

    return {
        "status": "healthy",
        "version": "1.2.0",
        "redis_connected": redis_ok,
        "session_ttl_hours": 24,
        "features": ["streaming", "caching"]
    }


# =============================================================================
# STREAMING ENDPOINTS
# =============================================================================

from app.services.llm_service import format_sse, format_sse_json


@router.post("/upload/stream")
async def upload_resume_stream(
    file: UploadFile = File(...),
    auth: AuthContext = Depends(get_auth_context),
    x_user_id: Optional[str] = Header(None),
    x_user_plan: Optional[str] = Header(None)
):
    """
    Upload and analyze a resume with streaming response.
    Returns SSE stream with real-time analysis.
    Supports both authenticated (Cognito JWT) and anonymous users.
    """
    # Generate session ID and check rate limit first
    session_id = str(uuid.uuid4())

    # Use auth context if authenticated, otherwise fall back to headers
    if auth.is_authenticated:
        user_id = auth.user_id
        plan = auth.plan
    else:
        user_id = get_user_id(x_user_id, session_id)
        plan = get_user_plan(x_user_plan)

    allowed, usage_info = rate_limiter.check_and_increment(user_id, plan)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={"message": "Rate limit exceeded", "usage": usage_info}
        )

    # Read and parse file
    content = await file.read()
    try:
        resume_text = parse_resume(content, file.filename or "resume.txt")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create session
    session_store.create_session(session_id, resume_text)

    async def generate():
        """Generate SSE stream for resume analysis."""
        full_response = []

        # Send session info first
        yield format_sse_json({
            "type": "session",
            "session_id": session_id,
            "resume_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
        }, event="meta")

        # Stream the analysis
        try:
            for chunk in resume_agent.analyze_resume_stream(resume_text):
                full_response.append(chunk)
                yield format_sse_json({"type": "content", "text": chunk}, event="content")

            # Store complete response
            complete_response = "".join(full_response)
            session_store.add_message(
                session_id,
                role="assistant",
                content=complete_response,
                tokens=context_manager.estimate_tokens(complete_response)
            )

            # Send completion event
            yield format_sse_json({
                "type": "done",
                "session_id": session_id,
                "usage": usage_info
            }, event="done")

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield format_sse_json({"type": "error", "message": str(e)}, event="error")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat with streaming response.
    Returns SSE stream with real-time response.
    """
    # Get session
    session = session_store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please upload your resume again."
        )

    # Detect corrections
    if detect_correction(request.message):
        session_store.add_correction(request.session_id, request.message)
        logger.info(f"User correction detected in session {request.session_id[:8]}...")

    # Add user message
    user_tokens = context_manager.estimate_tokens(request.message)
    session_store.add_message(
        request.session_id,
        role="user",
        content=request.message,
        tokens=user_tokens
    )

    # Check for cached/generic response first
    generic_response = get_generic_advice(request.message)
    cached_response = response_cache.get_cached_response(request.message) if not generic_response else None

    async def generate():
        """Generate SSE stream for chat response."""
        full_response = []

        if generic_response:
            # Stream generic advice character by character for consistent UX
            for char in generic_response:
                full_response.append(char)
                yield format_sse_json({"type": "content", "text": char}, event="content")

        elif cached_response:
            # Stream cached response
            for char in cached_response:
                full_response.append(char)
                yield format_sse_json({"type": "content", "text": char}, event="content")

        else:
            # Refresh session and stream from Claude
            session = session_store.get_session(request.session_id)
            history_messages = [
                Message(role=MessageRole(m["role"]), content=m["content"])
                for m in session.get("messages", [])[:-1]
            ]

            try:
                for chunk, usage in resume_agent.chat_stream_with_usage(
                    request.message,
                    history_messages,
                    session.get("resume_text"),
                    session.get("corrections", [])
                ):
                    if chunk:
                        full_response.append(chunk)
                        yield format_sse_json({"type": "content", "text": chunk}, event="content")

                    if usage:
                        # Track actual usage from API
                        context_manager.track_usage(
                            request.session_id,
                            usage["input_tokens"],
                            usage["output_tokens"]
                        )
                        yield format_sse_json({"type": "usage", **usage}, event="usage")

                # Cache response if applicable
                complete_response = "".join(full_response)
                response_cache.cache_response(request.message, complete_response)

            except Exception as e:
                logger.error(f"Chat streaming error: {e}")
                yield format_sse_json({"type": "error", "message": str(e)}, event="error")
                return

        # Store complete response
        complete_response = "".join(full_response)
        response_tokens = context_manager.estimate_tokens(complete_response)
        session_store.add_message(
            request.session_id,
            role="assistant",
            content=complete_response,
            tokens=response_tokens
        )

        yield format_sse_json({
            "type": "done",
            "session_id": request.session_id
        }, event="done")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/improve/stream")
async def suggest_improvements_stream(
    session_id: str,
    target_role: str,
    target_company: Optional[str] = None
):
    """Get targeted improvement suggestions with streaming."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )

    resume_text = session.get("resume_text")
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume found in session"
        )

    async def generate():
        """Generate SSE stream for improvements."""
        try:
            for chunk in resume_agent.suggest_improvements_stream(
                resume_text,
                target_role,
                target_company
            ):
                yield format_sse_json({"type": "content", "text": chunk}, event="content")

            yield format_sse_json({"type": "done"}, event="done")

        except Exception as e:
            logger.error(f"Improvements streaming error: {e}")
            yield format_sse_json({"type": "error", "message": str(e)}, event="error")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
