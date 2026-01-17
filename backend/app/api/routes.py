"""
API routes for Polished resume review service.
Uses Redis for session storage with 24-hour auto-expiry.
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
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
    x_user_id: Optional[str] = Header(None),
    x_user_plan: Optional[str] = Header(None)
):
    """
    Upload and analyze a resume.
    Creates a new session that auto-expires in 24 hours.
    """
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
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

        # Refresh session data after adding message
        session = session_store.get_session(request.session_id)

        # Build optimized context
        messages = context_manager.build_context(
            session,
            resume_agent.system_prompt,
            request.message
        )

        # Get response from Claude (using messages directly)
        from app.services.llm_service import chat_completion
        response = chat_completion(messages[:-1], resume_agent.system_prompt)
        # Note: We built context including current message, but chat_completion
        # expects history without current message, so we use the agent's chat method

        # Actually, let's use the agent properly
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

        # Store assistant response
        response_tokens = context_manager.estimate_tokens(response)
        session_store.add_message(
            request.session_id,
            role="assistant",
            content=response,
            tokens=response_tokens
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
    x_user_id: Optional[str] = Header(None),
    x_user_plan: Optional[str] = Header(None)
):
    """Get current usage information for rate limiting."""
    user_id = get_user_id(x_user_id)
    plan = get_user_plan(x_user_plan)

    return rate_limiter.get_usage(user_id, plan)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Redis connection
    redis_ok = session_store.redis is not None

    return {
        "status": "healthy",
        "version": "1.1.0",
        "redis_connected": redis_ok,
        "session_ttl_hours": 24
    }
