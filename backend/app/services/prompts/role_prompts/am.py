"""
Account Manager / Customer Success Manager prompt for tech sales resume optimization.
Target: Post-sale relationship management, revenue retention and growth
"""

AM_PROMPT = """
## Role Context: Account Manager / Customer Success Manager

This candidate focuses on post-sale relationships. They should demonstrate:
- Revenue retention and growth
- Customer relationship management
- Upsell/cross-sell success
- Churn prevention

### What AM/CSM Hiring Managers Want to See

**Must-Have Metrics:**
- Net Revenue Retention (NRR) - target >100%, ideally >110%
- Gross Revenue Retention (GRR) - target >85%
- Churn rate - lower is better
- Expansion revenue generated
- Book of business size (ARR managed)

**Strong Differentiators:**
- Consistent NRR above company average
- Large book of business managed
- Complex enterprise account management
- Cross-functional coordination
- Customer advocacy program success
- Strategic account planning

**Customer Success Signals:**
- NPS or CSAT improvements
- QBR/EBR leadership
- Renewal rate
- Logo retention
- Reference customers generated
- Product adoption metrics

### Optimization Strategy for This Role

1. **Summary Section**:
   - Lead with NRR or retention metrics
   - Mention book of business size
   - Highlight expansion revenue

   Example: "Senior Account Manager with track record of 115% NRR managing $8M ARR across 45 enterprise accounts. Expert in strategic account planning and executive relationship management."

2. **Experience Section**:
   - NRR/GRR for every AM role
   - Book of business size
   - Expansion revenue generated
   - Churn rate vs company average
   - Notable saves or expansions

3. **Key Achievements to Highlight**:
   - Best NRR/GRR performance
   - Largest expansion deal
   - Most successful churn save
   - Customer advocacy wins
   - Cross-sell/upsell success stories

### Bullet Point Transformations for AM

WEAK: "Managed customer relationships"
STRONG: "Managed $6.2M ARR across 38 enterprise accounts, achieving 122% NRR through strategic upselling and 97% logo retention"

WEAK: "Prevented customer churn"
STRONG: "Reduced churn rate from 18% to 8% through proactive health monitoring and executive engagement, saving $1.4M in at-risk ARR"

WEAK: "Upsold customers on new products"
STRONG: "Generated $2.1M in expansion revenue (145% of target) by identifying cross-sell opportunities and building business cases for platform adoption"

WEAK: "Conducted quarterly business reviews"
STRONG: "Led 120+ executive QBRs annually, achieving 94% renewal rate and generating 15 customer references for sales team"

WEAK: "Worked with customer success team"
STRONG: "Coordinated cross-functional team of 8 (support, product, engineering) to resolve critical account issues, maintaining 100% logo retention in enterprise segment"

### Metrics to Ask For (if missing)
- "What was your NRR or retention rate?"
- "How large was your book of business (ARR)?"
- "How much expansion revenue did you generate?"
- "What was the churn rate in your portfolio?"
- "How many accounts did you manage?"
- "What was your renewal rate?"
"""


def get_am_prompt() -> str:
    """Return the Account Manager prompt."""
    return AM_PROMPT
