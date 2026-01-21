# Product Requirements Document: Tech Sales Resume Optimization

**Product:** Polished - AI Resume Tool for Tech Sales Professionals
**Version:** 2.0
**Date:** January 2025
**Author:** Product Team
**Status:** In Development

---

## Executive Summary

Transform Polished from a generic resume review tool into a specialized, high-conversion resume optimization platform for tech sales professionals. This PRD covers two critical features:

1. **Role-Specific Optimization** - Tailored prompts and guidance for SDR, AE, AM, and Closer roles
2. **Job Description Matching** - Analyze resume fit against specific job postings

These features directly address the primary pain point identified with our agency partner: **weak resumes getting rejected at the screening stage**.

---

## Goals & Success Metrics

### Business Goals
| Goal | Target | Timeline |
|------|--------|----------|
| First paying agency customer | $99-149/mo | Day 30 |
| Agency pilot success rate | 20% more interviews | Day 45 |
| Total MRR | $2,500 | Day 90 |

### Product Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Resume-to-interview rate | Unknown | Track & improve by 20% |
| User satisfaction (agency) | N/A | 8+/10 |
| Time to polish resume | N/A | < 10 minutes |
| JD match accuracy | N/A | 85%+ relevance |

---

## User Personas

### Primary: Tech Sales Recruiter (Agency)
- **Name:** Alex, Recruiting Agency Owner
- **Context:** Building agency to place tech sales candidates
- **Pain:** Candidates have weak resumes, get rejected, no placement fee
- **Need:** Tool to quickly polish candidate resumes before submission
- **Workflow:** Receives candidate resume → Polishes it → Submits to client company

### Secondary: Tech Sales Job Seeker
- **Name:** Jordan, displaced AE
- **Context:** Laid off, looking for new AE role
- **Pain:** Not getting callbacks despite experience
- **Need:** Resume that highlights sales metrics and matches job requirements
- **Workflow:** Finds job posting → Tailors resume → Applies

---

## Feature 1: Role-Specific Optimization

### Overview
Add a role selector that loads specialized prompts, metrics guidance, and optimization strategies for each tech sales role level.

### Supported Roles

| Role | Experience Level | Key Metrics to Highlight |
|------|------------------|-------------------------|
| Entry SDR | 0-1 years | Activity metrics, ramp time, coachability signals |
| SDR | 1-3 years | Calls, emails, meetings booked, SQL conversion, quota % |
| Account Executive | 2-5 years | Quota %, deal count, ACV, win rate, sales cycle |
| Senior/Enterprise AE | 5+ years | Large deal sizes ($500K+), complex sales, C-suite access |
| Account Manager | 2+ years | NRR, churn rate, upsell %, expansion revenue |
| Sales Manager/Director | 5+ years | Team quota attainment, team size, revenue owned |

### User Flow

```
1. User uploads resume
2. NEW: Role selector appears
   ┌─────────────────────────────────────────┐
   │ What role is this candidate targeting?  │
   │                                         │
   │ ○ Entry-Level SDR (0-1 years)          │
   │ ○ SDR (1-3 years)                      │
   │ ○ Account Executive                     │
   │ ○ Senior/Enterprise AE                  │
   │ ○ Account Manager                       │
   │ ○ Sales Manager/Director                │
   └─────────────────────────────────────────┘
3. System loads role-specific prompt
4. Analysis highlights role-relevant strengths/gaps
5. Rewrite optimizes for that specific role
```

### Technical Requirements

#### Backend Changes

**File:** `backend/app/models/schemas.py`

Add new enum and update schemas:
```python
class SalesRole(str, Enum):
    ENTRY_SDR = "entry_sdr"
    SDR = "sdr"
    ACCOUNT_EXECUTIVE = "account_executive"
    SENIOR_AE = "senior_ae"
    ACCOUNT_MANAGER = "account_manager"
    SALES_MANAGER = "sales_manager"

class ResumeUploadRequest(BaseModel):
    role: Optional[SalesRole] = None

class SessionState(BaseModel):
    # ... existing fields ...
    target_role: Optional[SalesRole] = None
```

**File:** `backend/app/services/prompts/` (new directory)

Create role-specific prompt files:
- `base_sales_prompt.py` - Common sales resume knowledge
- `sdr_prompt.py` - SDR-specific optimization
- `ae_prompt.py` - AE-specific optimization
- `senior_ae_prompt.py` - Enterprise AE optimization
- `am_prompt.py` - Account Manager optimization
- `manager_prompt.py` - Sales leadership optimization

**File:** `backend/app/services/resume_agent.py`

Update to accept role parameter and load appropriate prompt.

**File:** `backend/app/api/routes.py`

Update `/upload` endpoint to accept role parameter.

#### Frontend Changes

**File:** `frontend/src/components/RoleSelector.tsx` (new)

Create role selection component.

**File:** `frontend/src/components/ResumeUpload.tsx`

Add role selector before/after upload.

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| 1.1 | Create SalesRole enum in schemas.py | 30 min | None |
| 1.2 | Create prompts directory structure | 15 min | None |
| 1.3 | Write base_sales_prompt.py | 1 hour | None |
| 1.4 | Write entry_sdr_prompt.py | 45 min | 1.3 |
| 1.5 | Write sdr_prompt.py | 45 min | 1.3 |
| 1.6 | Write ae_prompt.py | 45 min | 1.3 |
| 1.7 | Write senior_ae_prompt.py | 45 min | 1.3 |
| 1.8 | Write am_prompt.py | 45 min | 1.3 |
| 1.9 | Write manager_prompt.py | 45 min | 1.3 |
| 1.10 | Update resume_agent.py to use role prompts | 1 hour | 1.2-1.9 |
| 1.11 | Update routes.py for role parameter | 30 min | 1.1, 1.10 |
| 1.12 | Create RoleSelector.tsx component | 1 hour | None |
| 1.13 | Integrate RoleSelector into ResumeUpload.tsx | 45 min | 1.12 |
| 1.14 | Update API client for role parameter | 30 min | 1.11 |
| 1.15 | Test full flow end-to-end | 1 hour | All above |

**Total Estimated Time:** ~10 hours

---

## Feature 2: Job Description Matching

### Overview
Allow users to paste a job description and receive:
1. Match score (how well resume fits the JD)
2. Gap analysis (what's missing)
3. Keyword recommendations
4. Tailored rewrite suggestions

### User Flow

```
1. User has uploaded resume (with role selected)
2. User clicks "Match to Job Description"
3. Modal/panel appears:
   ┌─────────────────────────────────────────┐
   │ Paste the job description:             │
   │ ┌─────────────────────────────────────┐ │
   │ │                                     │ │
   │ │  [Large text area]                  │ │
   │ │                                     │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │ Optional: Job URL (we'll extract it)   │
   │ ┌─────────────────────────────────────┐ │
   │ │ https://...                         │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │         [Analyze Match]                │
   └─────────────────────────────────────────┘
4. System analyzes and returns:
   ┌─────────────────────────────────────────┐
   │ MATCH SCORE: 72/100                    │
   │ ━━━━━━━━━━━━━━━━━━━━━━░░░░░░░░         │
   │                                         │
   │ ✅ MATCHING REQUIREMENTS               │
   │ • 3+ years sales experience            │
   │ • Salesforce proficiency               │
   │ • SaaS sales background                │
   │                                         │
   │ ❌ GAPS TO ADDRESS                     │
   │ • No mention of MEDDIC methodology     │
   │ • Missing enterprise experience        │
   │ • Quota attainment not quantified      │
   │                                         │
   │ 📝 KEYWORDS TO ADD                     │
   │ • "MEDDIC" • "Enterprise" • "ARR"      │
   │                                         │
   │ [Generate Tailored Resume]             │
   └─────────────────────────────────────────┘
5. User clicks "Generate Tailored Resume"
6. System produces optimized version matching JD
```

### Technical Requirements

#### Backend Changes

**File:** `backend/app/models/schemas.py`

Add new schemas:
```python
class JDMatchRequest(BaseModel):
    session_id: str
    job_description: str
    job_url: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None

class JDMatchResult(BaseModel):
    match_score: int  # 0-100
    matching_requirements: List[str]
    gaps: List[str]
    keywords_to_add: List[str]
    keywords_present: List[str]
    tailored_suggestions: List[str]

class TailoredResumeRequest(BaseModel):
    session_id: str
    job_description: str
    prioritize_gaps: bool = True
```

**File:** `backend/app/services/jd_matcher.py` (new)

Create JD matching service:
- `extract_requirements(jd_text)` - Parse JD for requirements
- `analyze_match(resume_text, jd_text, role)` - Score match
- `identify_gaps(resume_text, requirements)` - Find missing elements
- `suggest_keywords(jd_text, resume_text)` - Keyword recommendations
- `generate_tailored_resume(resume_text, jd_text, role)` - Produce optimized version

**File:** `backend/app/services/prompts/jd_matching_prompt.py` (new)

Specialized prompt for JD analysis.

**File:** `backend/app/api/routes.py`

Add new endpoints:
- `POST /match-jd` - Analyze resume against JD
- `POST /tailor-resume` - Generate JD-tailored version

#### Frontend Changes

**File:** `frontend/src/components/JDMatcher.tsx` (new)

Create JD input and results display component.

**File:** `frontend/src/components/MatchResults.tsx` (new)

Display match score, gaps, and recommendations.

**File:** `frontend/src/pages/AppPage.tsx`

Integrate JD matching into main flow.

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| 2.1 | Create JD-related schemas in schemas.py | 30 min | None |
| 2.2 | Write jd_matching_prompt.py | 1.5 hours | None |
| 2.3 | Create jd_matcher.py service | 2 hours | 2.2 |
| 2.4 | Add /match-jd endpoint | 45 min | 2.1, 2.3 |
| 2.5 | Add /tailor-resume endpoint | 45 min | 2.3 |
| 2.6 | Create JDMatcher.tsx component | 1.5 hours | None |
| 2.7 | Create MatchResults.tsx component | 1.5 hours | None |
| 2.8 | Integrate into AppPage.tsx | 1 hour | 2.6, 2.7 |
| 2.9 | Update API client for new endpoints | 30 min | 2.4, 2.5 |
| 2.10 | Test JD matching flow | 1 hour | All above |
| 2.11 | Test tailored resume generation | 1 hour | All above |

**Total Estimated Time:** ~12 hours

---

## Feature 3: Metrics Extraction & Enhancement

### Overview
Proactively identify missing sales metrics and prompt user to provide them, then weave them into the resume.

### Metrics by Role

| Role | Critical Metrics | Nice-to-Have Metrics |
|------|------------------|---------------------|
| SDR | Meetings booked/month, SQL conversion %, quota % | Calls/day, emails/day, ramp time |
| AE | Quota attainment %, deal count, ACV | Win rate, sales cycle, pipeline generated |
| Senior AE | Deal sizes, quota %, complex sale indicators | Multi-threading, C-suite meetings |
| AM | NRR %, churn %, upsell % | CSAT, expansion revenue, logo retention |

### User Flow

```
1. After initial analysis, if metrics are missing:
   ┌─────────────────────────────────────────┐
   │ ⚠️ MISSING METRICS DETECTED            │
   │                                         │
   │ Strong sales resumes quantify results. │
   │ Help me strengthen yours:              │
   │                                         │
   │ At [Company X] as [Role]:              │
   │                                         │
   │ What was your quota?                   │
   │ ┌─────────────────────────────────────┐ │
   │ │ $ ___________                       │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │ What % of quota did you achieve?       │
   │ ┌─────────────────────────────────────┐ │
   │ │ _____ %                             │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │ How many deals did you close?          │
   │ ┌─────────────────────────────────────┐ │
   │ │ _____                               │ │
   │ └─────────────────────────────────────┘ │
   │                                         │
   │ [Skip] [Apply to Resume]               │
   └─────────────────────────────────────────┘
2. System incorporates metrics into rewrite
```

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| 3.1 | Define metrics schema per role | 30 min | None |
| 3.2 | Create metrics detection prompt | 1 hour | None |
| 3.3 | Build MetricsExtractor.tsx component | 1.5 hours | None |
| 3.4 | Create metrics integration prompt | 1 hour | 3.2 |
| 3.5 | Add metrics to session state | 30 min | 3.1 |
| 3.6 | Integrate into resume rewrite flow | 1 hour | 3.4, 3.5 |
| 3.7 | Test metrics flow | 1 hour | All above |

**Total Estimated Time:** ~6.5 hours

---

## Prompt Engineering Specifications

### Base Tech Sales System Prompt

See `PROMPT-SPECS.md` for full prompt text.

Key elements:
1. Tech sales domain expertise
2. Role-specific career ladder knowledge
3. Metrics vocabulary (ARR, MRR, ACV, NRR, etc.)
4. Sales methodology awareness (MEDDIC, BANT, Challenger, SPIN)
5. Tech stack knowledge (Salesforce, HubSpot, Outreach, Gong, etc.)
6. Strict factual accuracy rules (inherited from current system)

### Role-Specific Prompt Additions

Each role prompt extends the base with:
- Role-specific metrics priorities
- Common job requirements for that level
- Typical career progression context
- Red flags to avoid
- Power phrases that work

### JD Matching Prompt

Specialized prompt for:
- Extracting requirements from JD text
- Categorizing must-have vs nice-to-have
- Identifying keyword gaps
- Scoring match objectively
- Generating actionable recommendations

---

## API Specification

### Updated Endpoints

#### POST /upload
```json
// Request
{
  "file": "<binary>",
  "role": "account_executive"  // NEW: optional
}

// Response (unchanged)
{
  "session_id": "uuid",
  "message": "Resume uploaded and analyzed successfully",
  "resume_text": "...",
  "initial_analysis": "..."
}
```

#### POST /match-jd (NEW)
```json
// Request
{
  "session_id": "uuid",
  "job_description": "We are looking for an AE with 3+ years...",
  "job_title": "Account Executive",  // optional
  "company": "Acme Corp"  // optional
}

// Response
{
  "match_score": 72,
  "matching_requirements": [
    "3+ years sales experience",
    "Salesforce proficiency"
  ],
  "gaps": [
    "No MEDDIC methodology mentioned",
    "Enterprise experience not highlighted"
  ],
  "keywords_to_add": ["MEDDIC", "enterprise", "ARR"],
  "keywords_present": ["quota", "pipeline", "Salesforce"],
  "suggestions": [
    "Add your quota attainment percentage",
    "Mention deal sizes to show enterprise capability"
  ]
}
```

#### POST /tailor-resume (NEW)
```json
// Request
{
  "session_id": "uuid",
  "job_description": "...",
  "include_metrics_prompts": true
}

// Response
{
  "tailored_resume": "...",
  "changes_made": [
    "Added MEDDIC keyword in methodology section",
    "Reframed deal experience to emphasize enterprise scale"
  ],
  "metrics_needed": [
    {
      "company": "Previous Corp",
      "role": "AE",
      "questions": [
        "What was your annual quota?",
        "What % did you achieve?"
      ]
    }
  ]
}
```

#### POST /set-role (NEW)
```json
// Request
{
  "session_id": "uuid",
  "role": "senior_ae"
}

// Response
{
  "message": "Role updated",
  "role": "senior_ae"
}
```

---

## Data Models

### Updated SessionState
```python
class SessionState(BaseModel):
    session_id: str
    resume_text: Optional[str] = None
    resume_analysis: Optional[ResumeAnalysis] = None
    conversation_history: List[Message] = []
    user_info: Dict[str, Any] = {}
    user_corrections: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # NEW FIELDS
    target_role: Optional[SalesRole] = None
    job_description: Optional[str] = None
    jd_match_result: Optional[JDMatchResult] = None
    collected_metrics: Dict[str, Dict[str, Any]] = {}  # company -> metrics
```

---

## Testing Plan

### Unit Tests
- [ ] Role prompt loading
- [ ] JD parsing/extraction
- [ ] Match scoring algorithm
- [ ] Metrics detection

### Integration Tests
- [ ] Full upload → role select → analyze flow
- [ ] JD match → tailor resume flow
- [ ] Metrics collection → rewrite flow

### User Acceptance Tests
- [ ] Agency partner tests with 10 real resumes
- [ ] Compare interview rates before/after
- [ ] Time to complete polish < 10 min

---

## Rollout Plan

### Phase 1: Internal Testing (Days 1-7)
- Complete all development tasks
- Internal QA with test resumes
- Fix bugs and edge cases

### Phase 2: Agency Pilot (Days 8-21)
- Deploy to production
- Give agency partner access
- Collect feedback on 10-20 real candidates
- Iterate based on feedback

### Phase 3: Paid Launch (Days 22-30)
- Finalize pricing with agency
- Enable payment processing
- Launch B2C landing page updates
- Begin content marketing

---

## Dependencies & Risks

### Dependencies
| Dependency | Owner | Status |
|------------|-------|--------|
| Anthropic API access | Infra | ✅ Ready |
| Agency partner availability | Business | ✅ Confirmed |
| Frontend deployment | DevOps | ✅ Ready |

### Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt quality insufficient | High | Iterate with real resumes, get agency feedback |
| JD parsing unreliable | Medium | Use structured extraction, handle edge cases |
| API costs higher than expected | Medium | Monitor usage, implement caching |
| Agency partner churns | High | Deliver clear ROI in pilot phase |

---

## Appendix

### Competitor Analysis

| Competitor | JD Matching | Role-Specific | Sales Focus |
|------------|-------------|---------------|-------------|
| Jobscan | ✅ Strong | ❌ Generic | ❌ No |
| Teal | ✅ Basic | ❌ Generic | ❌ No |
| Resume.io | ❌ No | ❌ Generic | ❌ No |
| ChatGPT | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| **Polished** | ✅ Planned | ✅ Planned | ✅ Yes |

### References
- Current codebase: `/Users/ishan/secureagent/Polished`
- Live product: https://getpolished.ai
- GitHub: https://github.com/IParikh1/Polished
