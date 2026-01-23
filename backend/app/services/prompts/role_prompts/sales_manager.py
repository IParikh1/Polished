"""
Sales Manager / Director prompt for tech sales resume optimization.
Target: Sales leadership roles managing teams and revenue
"""

SALES_MANAGER_PROMPT = """
## Role Context: Sales Manager / Director (Leadership)

This candidate leads sales teams. They should demonstrate:
- Team performance and quota attainment
- Hiring and developing talent
- Revenue responsibility
- Strategic planning and execution

### What Sales Leadership Hiring Managers Want to See

**Must-Have Metrics:**
- Team quota attainment %
- Team size managed
- Total revenue responsibility
- Rep productivity improvement

**Leadership Differentiators:**
- Consistent team performance (multi-quarter/year)
- Hiring track record (quality and retention)
- Rep development (promotions, career growth)
- Process improvement impact
- Territory/segment expansion
- Cross-functional leadership

**Strategic Leadership Signals:**
- Sales strategy development
- Go-to-market execution
- Pipeline management at scale
- Forecasting accuracy
- Comp plan design input
- Cross-departmental alignment (marketing, product, CS)

### Optimization Strategy for This Role

1. **Summary Section**:
   - Lead with team performance and revenue
   - Mention team size and scope
   - Highlight leadership achievements

   Example: "Sales Director leading team of 12 AEs to 108% quota attainment, responsible for $18M ARR. Track record of building high-performing teams with 85% rep retention and 6 promotions to leadership."

2. **Experience Section**:
   - Team quota attainment for every leadership role
   - Team size and revenue responsibility
   - Rep development outcomes
   - Process improvements and their impact
   - Key strategic initiatives led

3. **Leadership Achievements to Highlight**:
   - Best team performance quarter/year
   - Successful hires and their outcomes
   - Reps promoted under your leadership
   - Process improvements with measurable results
   - Territory or segment growth

### Bullet Point Transformations for Sales Leadership

WEAK: "Managed a team of sales representatives"
STRONG: "Led team of 12 AEs generating $18M ARR, achieving 108% team quota with 10 of 12 reps at 100%+ attainment"

WEAK: "Hired and trained new sales reps"
STRONG: "Recruited 8 AEs with 90% retention rate, reducing average ramp time from 6 months to 4 months through structured onboarding program"

WEAK: "Improved sales processes"
STRONG: "Redesigned sales process increasing win rate from 22% to 31% and reducing sales cycle from 45 to 32 days, adding $2.4M incremental revenue"

WEAK: "Responsible for sales forecasting"
STRONG: "Implemented forecasting methodology achieving 94% accuracy within 5%, enabling executive team to make confident growth investments"

WEAK: "Developed sales team"
STRONG: "Promoted 6 reps to senior roles and 2 to management within 18 months, building leadership bench while maintaining 115% team quota attainment"

WEAK: "Collaborated with marketing"
STRONG: "Partnered with marketing to launch outbound program generating $4.2M pipeline in Q1, with 28% conversion rate to qualified opportunity"

### Metrics to Ask For (if missing)
- "What was your team's quota attainment?"
- "How large was your team?"
- "What was your total revenue responsibility?"
- "How many reps have you promoted or developed?"
- "What's your team retention rate?"
- "What process improvements have you implemented and what was the impact?"
"""


def get_sales_manager_prompt() -> str:
    """Return the Sales Manager/Director prompt."""
    return SALES_MANAGER_PROMPT
