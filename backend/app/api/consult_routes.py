"""
Consulting API Routes for Polished Resume Ranking System.
Premium feature for AI-powered resume consulting and rewriting.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..services.aws_store import get_store
from ..services.premium_gate import get_premium_gate, PremiumFeature
from ..middleware.auth import get_current_user, AuthenticatedUser
from .batch_routes import verify_batch_ownership


router = APIRouter(prefix="/consulting", tags=["Consulting"])


# ==================== Request/Response Models ====================

class ConsultingSessionRequest(BaseModel):
    """Request to start a consulting session."""
    resume_id: str = Field(..., description="Resume to consult on")
    batch_id: str = Field(..., description="Batch containing the resume")
    target_role: Optional[str] = Field(None, description="Target job role")
    job_description: Optional[str] = Field(None, description="Specific JD to optimize for")


class ConsultingSessionResponse(BaseModel):
    """Response with consulting session details."""
    session_id: str
    resume_id: str
    batch_id: str
    target_role: Optional[str]
    status: str
    created_at: datetime


class AnalysisRequest(BaseModel):
    """Request for resume analysis."""
    session_id: str
    analysis_type: str = Field(
        "comprehensive",
        description="Type: comprehensive, quick, or targeted"
    )


class AnalysisResponse(BaseModel):
    """Response with resume analysis."""
    session_id: str
    analysis_type: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    section_feedback: Dict[str, str]
    overall_assessment: str
    improvement_priority: List[str]


class RewriteRequest(BaseModel):
    """Request for section rewrite."""
    session_id: str
    section: str = Field(..., description="Section to rewrite: summary, experience, skills")
    context: Optional[str] = Field(None, description="Additional context for rewrite")
    tone: str = Field("professional", description="Tone: professional, creative, technical")


class RewriteResponse(BaseModel):
    """Response with rewritten section."""
    session_id: str
    section: str
    original_text: str
    rewritten_text: str
    changes_made: List[str]
    improvement_score: float


class ChatMessage(BaseModel):
    """Chat message for consulting conversation."""
    role: str = Field(..., description="Role: user or assistant")
    content: str


class ChatRequest(BaseModel):
    """Request for consulting chat."""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response with chat reply."""
    session_id: str
    messages: List[ChatMessage]
    suggestions: List[str]


# ==================== In-memory Session Storage (for MVP) ====================

_sessions: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a consulting session."""
    return _sessions.get(session_id)


def get_owned_session(session_id: str, user_id: str) -> Dict[str, Any]:
    """Get a consulting session, enforcing ownership. Raises 404 if missing or not owned."""
    session = _sessions.get(session_id)
    # Return 404 (not 403) so session IDs can't be probed
    if not session or session.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def create_session(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new consulting session."""
    session_id = f"consult-{uuid.uuid4().hex[:12]}"
    session = {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
        "messages": [],
        **data,
    }
    _sessions[session_id] = session
    return session


# ==================== Session Management ====================

@router.post("/sessions", response_model=ConsultingSessionResponse)
async def create_consulting_session(
    request: ConsultingSessionRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Start a new consulting session for a resume.

    Premium feature - requires consulting access.
    """
    gate = get_premium_gate()
    store = get_store()

    # Check premium access
    if not gate.has_feature(user.user_id, PremiumFeature.CONSULTING):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Premium feature required",
                "feature": "consulting",
                "upgrade_options": gate.get_upgrade_options(user.user_id),
            }
        )

    # Verify the caller owns the batch containing the resume
    await verify_batch_ownership(request.batch_id, user.user_id)

    # Verify resume exists
    resume = await store.get_resume(request.batch_id, request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Create session
    session = create_session({
        "user_id": user.user_id,
        "resume_id": request.resume_id,
        "batch_id": request.batch_id,
        "target_role": request.target_role,
        "job_description": request.job_description,
        "resume_data": resume,
    })

    return ConsultingSessionResponse(
        session_id=session["session_id"],
        resume_id=session["resume_id"],
        batch_id=session["batch_id"],
        target_role=session.get("target_role"),
        status=session["status"],
        created_at=datetime.fromisoformat(session["created_at"]),
    )


@router.get("/sessions/{session_id}")
async def get_consulting_session(
    session_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get consulting session details."""
    session = get_owned_session(session_id, user.user_id)

    return {
        "session_id": session["session_id"],
        "resume_id": session["resume_id"],
        "batch_id": session["batch_id"],
        "target_role": session.get("target_role"),
        "status": session["status"],
        "created_at": session["created_at"],
        "message_count": len(session.get("messages", [])),
    }


# ==================== Analysis Operations ====================

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    request: AnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get comprehensive analysis of a resume.

    Provides:
    - Strengths and weaknesses
    - Section-by-section feedback
    - Prioritized recommendations
    """
    session = get_owned_session(request.session_id, user.user_id)

    resume_data = session.get("resume_data", {})
    extracted = resume_data.get("extracted_data", {})
    target_role = session.get("target_role", "software engineer")

    # Generate analysis (rule-based for MVP, can be enhanced with LLM)
    strengths = _analyze_strengths(extracted)
    weaknesses = _analyze_weaknesses(extracted)
    recommendations = _generate_recommendations(extracted, target_role)
    section_feedback = _analyze_sections(extracted)

    return AnalysisResponse(
        session_id=request.session_id,
        analysis_type=request.analysis_type,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        section_feedback=section_feedback,
        overall_assessment=_generate_overall_assessment(strengths, weaknesses),
        improvement_priority=recommendations[:3],
    )


def _analyze_strengths(extracted: Dict) -> List[str]:
    """Analyze resume strengths."""
    strengths = []

    skills = extracted.get("skills", [])
    if len(skills) >= 10:
        strengths.append(f"Strong technical skill set with {len(skills)} identified skills")
    elif len(skills) >= 5:
        strengths.append("Good variety of technical skills")

    years = extracted.get("years_of_experience", 0)
    if years and years >= 5:
        strengths.append(f"Solid experience with {years}+ years in the field")
    elif years and years >= 2:
        strengths.append("Relevant work experience")

    education = extracted.get("education", [])
    if education:
        strengths.append("Educational background included")

    if extracted.get("email") and extracted.get("phone"):
        strengths.append("Complete contact information")

    if extracted.get("summary"):
        strengths.append("Professional summary present")

    if not strengths:
        strengths.append("Resume structure is readable")

    return strengths


def _analyze_weaknesses(extracted: Dict) -> List[str]:
    """Analyze resume weaknesses."""
    weaknesses = []

    if not extracted.get("summary"):
        weaknesses.append("Missing professional summary section")

    skills = extracted.get("skills", [])
    if len(skills) < 5:
        weaknesses.append("Limited skills section - consider adding more relevant technologies")

    if not extracted.get("years_of_experience"):
        weaknesses.append("Years of experience not clearly stated")

    if not extracted.get("education"):
        weaknesses.append("Education section may need enhancement")

    if not extracted.get("email"):
        weaknesses.append("Email address not detected - ensure it's clearly visible")

    return weaknesses if weaknesses else ["No major weaknesses identified"]


def _generate_recommendations(extracted: Dict, target_role: str) -> List[str]:
    """Generate improvement recommendations."""
    recommendations = []

    if not extracted.get("summary"):
        recommendations.append(
            f"Add a compelling professional summary tailored for {target_role} roles"
        )

    skills = extracted.get("skills", [])
    if len(skills) < 8:
        recommendations.append(
            "Expand your skills section with specific technologies and tools you've used"
        )

    recommendations.append(
        "Quantify your achievements with specific metrics (e.g., 'Improved performance by 40%')"
    )

    recommendations.append(
        "Use strong action verbs to describe your accomplishments (Led, Developed, Implemented)"
    )

    if target_role:
        recommendations.append(
            f"Customize your resume keywords to match {target_role} job descriptions"
        )

    return recommendations


def _analyze_sections(extracted: Dict) -> Dict[str, str]:
    """Provide feedback on each section."""
    feedback = {}

    # Summary feedback
    if extracted.get("summary"):
        feedback["summary"] = "Good - Summary is present. Consider making it more impactful."
    else:
        feedback["summary"] = "Missing - Add a 2-3 sentence professional summary."

    # Skills feedback
    skills = extracted.get("skills", [])
    if len(skills) >= 10:
        feedback["skills"] = "Strong - Good variety of skills listed."
    elif len(skills) >= 5:
        feedback["skills"] = "Adequate - Consider adding more specific technologies."
    else:
        feedback["skills"] = "Needs work - Expand with relevant technical skills."

    # Experience feedback
    if extracted.get("years_of_experience"):
        feedback["experience"] = "Present - Ensure each role has measurable achievements."
    else:
        feedback["experience"] = "Unclear - Make your experience timeline clearer."

    # Education feedback
    if extracted.get("education"):
        feedback["education"] = "Present - Consider adding relevant coursework or projects."
    else:
        feedback["education"] = "Missing or unclear - Add your educational background."

    # Contact feedback
    contact_complete = extracted.get("email") and extracted.get("phone")
    if contact_complete:
        feedback["contact"] = "Complete - All key contact information present."
    else:
        feedback["contact"] = "Incomplete - Ensure email and phone are clearly visible."

    return feedback


def _generate_overall_assessment(strengths: List[str], weaknesses: List[str]) -> str:
    """Generate overall assessment."""
    strength_count = len(strengths)
    weakness_count = len([w for w in weaknesses if "No major" not in w])

    if weakness_count == 0:
        return "Excellent resume with strong fundamentals. Minor optimizations can make it even better."
    elif strength_count > weakness_count:
        return "Good resume with solid foundation. Address the identified weaknesses to strengthen your application."
    elif strength_count == weakness_count:
        return "Resume has potential but needs improvement in several areas. Focus on the priority recommendations."
    else:
        return "Resume needs significant improvement. Start with the top priority recommendations."


# ==================== Rewrite Operations ====================

@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_section(
    request: RewriteRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Get a rewritten version of a resume section.

    Supports: summary, experience, skills
    """
    session = get_owned_session(request.session_id, user.user_id)

    resume_data = session.get("resume_data", {})
    extracted = resume_data.get("extracted_data", {})
    target_role = session.get("target_role", "software engineer")

    # Get original text
    original = _get_section_text(extracted, request.section)

    # Generate rewrite
    rewritten, changes = _rewrite_section(
        original,
        request.section,
        target_role,
        request.tone,
        extracted,
    )

    return RewriteResponse(
        session_id=request.session_id,
        section=request.section,
        original_text=original,
        rewritten_text=rewritten,
        changes_made=changes,
        improvement_score=_calculate_improvement_score(original, rewritten),
    )


def _get_section_text(extracted: Dict, section: str) -> str:
    """Get original text for a section."""
    if section == "summary":
        return extracted.get("summary", "No summary available")
    elif section == "skills":
        skills = extracted.get("skills", [])
        return ", ".join(skills) if skills else "No skills listed"
    elif section == "experience":
        return f"{extracted.get('years_of_experience', 'Unknown')} years of experience"
    return "Section not found"


def _rewrite_section(
    original: str,
    section: str,
    target_role: str,
    tone: str,
    extracted: Dict,
) -> tuple[str, List[str]]:
    """Generate rewritten section text."""
    changes = []

    if section == "summary":
        name = extracted.get("name", "Professional")
        years = extracted.get("years_of_experience", 5)
        skills = extracted.get("skills", ["software development"])[:3]
        skill_text = ", ".join(skills)

        rewritten = (
            f"Results-driven {target_role} with {years}+ years of experience "
            f"specializing in {skill_text}. Proven track record of delivering "
            f"high-quality solutions and driving technical excellence. "
            f"Passionate about innovation and continuous improvement."
        )
        changes = [
            "Added quantifiable experience",
            "Highlighted key technical skills",
            "Included value proposition",
            "Used action-oriented language",
        ]

    elif section == "skills":
        skills = extracted.get("skills", [])

        # Categorize skills
        categories = {
            "Languages": [],
            "Frameworks": [],
            "Tools": [],
            "Other": [],
        }

        lang_keywords = ["python", "javascript", "java", "c++", "go", "rust"]
        framework_keywords = ["react", "django", "flask", "node", "angular"]

        for skill in skills:
            skill_lower = skill.lower()
            if any(lang in skill_lower for lang in lang_keywords):
                categories["Languages"].append(skill)
            elif any(fw in skill_lower for fw in framework_keywords):
                categories["Frameworks"].append(skill)
            else:
                categories["Other"].append(skill)

        rewritten_parts = []
        for cat, cat_skills in categories.items():
            if cat_skills:
                rewritten_parts.append(f"{cat}: {', '.join(cat_skills)}")

        rewritten = "\n".join(rewritten_parts) if rewritten_parts else original

        changes = [
            "Organized skills by category",
            "Improved readability",
            "Professional formatting",
        ]

    else:
        rewritten = original
        changes = ["No changes suggested for this section"]

    return rewritten, changes


def _calculate_improvement_score(original: str, rewritten: str) -> float:
    """Calculate improvement score."""
    if original == rewritten:
        return 0.0

    # Simple heuristic based on length and content
    orig_words = len(original.split())
    new_words = len(rewritten.split())

    # More words usually means more detail
    length_score = min(new_words / max(orig_words, 1), 2) * 25

    # Check for action words
    action_words = ["proven", "driven", "delivered", "achieved", "led"]
    action_score = sum(10 for w in action_words if w in rewritten.lower())

    return min(length_score + action_score, 100)


# ==================== Chat Operations ====================

@router.post("/chat", response_model=ChatResponse)
async def consulting_chat(
    request: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Chat with the consulting AI about resume improvements.
    """
    session = get_owned_session(request.session_id, user.user_id)

    # Add user message
    user_message = ChatMessage(role="user", content=request.message)
    session["messages"].append(user_message.model_dump())

    # Generate response
    response_content = _generate_chat_response(
        request.message,
        session.get("resume_data", {}),
        session.get("target_role"),
    )

    assistant_message = ChatMessage(role="assistant", content=response_content)
    session["messages"].append(assistant_message.model_dump())

    # Generate suggestions
    suggestions = _generate_suggestions(request.message)

    return ChatResponse(
        session_id=request.session_id,
        messages=[
            ChatMessage(**m) for m in session["messages"][-10:]  # Last 10 messages
        ],
        suggestions=suggestions,
    )


def _generate_chat_response(message: str, resume_data: Dict, target_role: Optional[str]) -> str:
    """Generate chat response based on user message."""
    message_lower = message.lower()
    extracted = resume_data.get("extracted_data", {})

    if "summary" in message_lower:
        return (
            "For a strong professional summary, focus on three key elements:\n\n"
            "1. Your experience level and specialty\n"
            "2. Your key technical strengths\n"
            "3. The value you bring to employers\n\n"
            "Would you like me to draft a summary for you?"
        )

    elif "skills" in message_lower:
        skills = extracted.get("skills", [])
        return (
            f"I found {len(skills)} skills in your resume. "
            "To optimize your skills section:\n\n"
            "- Group skills by category (Languages, Frameworks, Tools)\n"
            "- Put most relevant skills first\n"
            "- Include proficiency levels if appropriate\n\n"
            "Would you like suggestions for additional skills to add?"
        )

    elif "experience" in message_lower:
        return (
            "To strengthen your experience section:\n\n"
            "- Start each bullet with an action verb\n"
            "- Include quantifiable results (%, $, time saved)\n"
            "- Focus on impact, not just responsibilities\n"
            "- Tailor content to your target role\n\n"
            "Would you like help rewriting specific experience entries?"
        )

    elif "improve" in message_lower or "better" in message_lower:
        return (
            "Based on my analysis, here are the top ways to improve your resume:\n\n"
            "1. Add measurable achievements to each role\n"
            "2. Optimize keywords for ATS systems\n"
            "3. Strengthen your professional summary\n"
            "4. Ensure consistent formatting throughout\n\n"
            "Which area would you like to focus on first?"
        )

    else:
        return (
            "I'm here to help improve your resume! I can assist with:\n\n"
            "- Analyzing and improving your summary\n"
            "- Optimizing your skills section\n"
            "- Strengthening experience descriptions\n"
            "- Tailoring content for specific roles\n\n"
            "What would you like to work on?"
        )


def _generate_suggestions(message: str) -> List[str]:
    """Generate follow-up suggestions."""
    message_lower = message.lower()

    if "summary" in message_lower:
        return [
            "Write a summary for me",
            "What makes a good summary?",
            "How long should my summary be?",
        ]
    elif "skills" in message_lower:
        return [
            "What skills should I add?",
            "How do I organize my skills?",
            "What skills are most in-demand?",
        ]
    else:
        return [
            "Analyze my resume",
            "Help with my summary",
            "Improve my experience section",
            "What skills should I highlight?",
        ]


@router.get("/chat/{session_id}/history")
async def get_chat_history(
    session_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get chat history for a session."""
    session = get_owned_session(session_id, user.user_id)

    return {
        "session_id": session_id,
        "messages": session.get("messages", []),
        "message_count": len(session.get("messages", [])),
    }
