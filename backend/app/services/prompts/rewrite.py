"""
Resume Rewrite prompt for generating optimized tech sales resumes.
"""

REWRITE_PROMPT = """You are rewriting a tech sales resume to maximize interview chances for the target role.

## Current Context
- **Target Role:** {role}
- **Job Description:** {job_description}
- **Original Resume:** {resume_text}
- **Collected Metrics:** {metrics}

## Rewrite Guidelines

### Structure
1. **Contact Info** - Name, location (city only), phone, email, LinkedIn
2. **Summary** - 2-3 sentences, lead with strongest metric
3. **Experience** - Reverse chronological, metrics-first bullets
4. **Education** - School, degree, graduation year, relevant honors
5. **Skills** - Tools, methodologies, certifications

### For Each Experience Entry
Format:
```
**Company Name** | Location
**Job Title** | Start Date - End Date

- [Metric-first achievement bullet]
- [Metric-first achievement bullet]
- [Metric-first achievement bullet]
```

### Bullet Point Formula
Lead with the RESULT, then context:
- "Achieved [X metric] by [action], resulting in [business impact]"
- "Generated [$ amount] in [revenue type] through [method]"
- "Ranked #[X] of [Y] by [metric], earning [recognition]"

### Keywords to Incorporate
Based on target role, ensure these appear naturally:
{role_specific_keywords}

## Critical Rules
1. NEVER invent facts - only use information from original resume + provided metrics
2. NEVER change company names, titles, or dates
3. DO reword for impact and clarity
4. DO add provided metrics in appropriate context
5. DO optimize keyword placement for ATS
6. DO maintain consistent formatting
7. Keep to appropriate length (1 page for <7 years, 2 max for senior)

## Output Format

Provide the complete rewritten resume in clean, formatted text.

Then provide:

**CHANGES MADE:**
1. [Specific change and why]
2. [Specific change and why]

**KEYWORDS ADDED:**
- [keyword]: [where placed]

**SUGGESTIONS FOR FURTHER IMPROVEMENT:**
- [What else could strengthen this resume if candidate provides more info]
"""


def get_rewrite_prompt(
    role: str = "",
    job_description: str = "",
    resume_text: str = "",
    metrics: str = "",
    role_specific_keywords: str = ""
) -> str:
    """
    Return the rewrite prompt with context filled in.

    Args:
        role: Target role
        job_description: JD text if provided
        resume_text: Original resume
        metrics: Collected metrics from user
        role_specific_keywords: Keywords relevant to the target role

    Returns:
        Formatted rewrite prompt
    """
    return REWRITE_PROMPT.format(
        role=role or "Not specified",
        job_description=job_description or "Not provided",
        resume_text=resume_text or "Not provided",
        metrics=metrics or "None collected",
        role_specific_keywords=role_specific_keywords or "Standard sales terminology"
    )
