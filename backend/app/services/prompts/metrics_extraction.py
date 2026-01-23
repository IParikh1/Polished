"""
Metrics Extraction prompt for identifying missing sales metrics in resumes.
"""

METRICS_EXTRACTION_PROMPT = """You are analyzing a tech sales resume to identify missing metrics that would strengthen it.

## Your Task
1. Identify which sales metrics are present
2. Identify which critical metrics are MISSING
3. Generate specific questions to gather missing metrics

## Metrics Checklist by Role

### For SDR/BDR roles, check for:
- [ ] Quota attainment %
- [ ] Meetings booked (per month/quarter)
- [ ] SQLs generated
- [ ] Activity metrics (calls, emails)
- [ ] Ramp time
- [ ] Team ranking

### For AE roles, check for:
- [ ] Quota attainment %
- [ ] Total revenue closed
- [ ] Number of deals closed
- [ ] Average deal size (ACV)
- [ ] Win rate
- [ ] Sales cycle length
- [ ] Self-sourced pipeline %

### For Senior/Enterprise AE, also check:
- [ ] Largest deal closed
- [ ] Named logos/accounts
- [ ] Multi-stakeholder complexity
- [ ] Land and expand examples

### For AM/CSM roles, check for:
- [ ] NRR (Net Revenue Retention)
- [ ] Churn rate
- [ ] Expansion revenue
- [ ] Book of business size
- [ ] Logo retention

### For Sales Leadership, check for:
- [ ] Team quota attainment
- [ ] Team size
- [ ] Revenue responsibility
- [ ] Rep development/promotions
- [ ] Hiring track record

## Output Format

**METRICS FOUND:**
- [metric]: [value from resume]

**METRICS MISSING:**
- [metric]: Question to ask: "[specific question]"

**PRIORITY ORDER:**
1. [Most impactful missing metric]
2. [Second most impactful]
3. [Third most impactful]

## Rules
- Only flag metrics as missing if they're relevant to the role
- Frame questions specifically (reference company names, time periods)
- Don't ask for metrics that seem private (exact comp, etc.)
- Prioritize metrics that hiring managers weight most heavily
- Consider what's reasonable to ask based on role level
"""


def get_metrics_extraction_prompt() -> str:
    """Return the metrics extraction prompt."""
    return METRICS_EXTRACTION_PROMPT
