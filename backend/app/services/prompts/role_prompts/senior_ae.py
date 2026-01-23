"""
Senior/Enterprise AE prompt for tech sales resume optimization.
Target: 5+ years experience, $100K+ deals
"""

SENIOR_AE_PROMPT = """
## Role Context: Senior/Enterprise AE (5+ years, $100K+ deals)

This candidate sells large, complex deals. They should demonstrate:
- Large deal sizes ($100K-$1M+ ACV)
- Complex, multi-stakeholder sales
- Strategic account management
- Executive presence and C-suite access
- Long sales cycle management

### What Enterprise AE Hiring Managers Want to See

**Must-Have Metrics:**
- Quota attainment (ideally multi-year track record)
- Deal sizes (looking for $100K+ average, ideally some $500K+)
- Total revenue closed ($2M+/year expected)
- Sales cycle management (6-18 month cycles)

**Enterprise-Specific Differentiators:**
- Named account success (Fortune 500, target logos)
- Multi-threading depth (10+ stakeholders)
- C-suite relationships built
- Land and expand motion ($50K -> $500K)
- Competitive enterprise displacements
- Multi-year contract negotiation
- Cross-functional deal coordination (legal, security, procurement)

**Strategic Selling Signals:**
- Business case development
- ROI/value selling
- Executive business reviews
- Account planning sophistication
- Partner/channel involvement

### Optimization Strategy for This Role

1. **Summary Section**:
   - Lead with deal size and total revenue
   - Mention named accounts or industries
   - Highlight strategic selling capability

   Example: "Enterprise Account Executive with 8 years closing complex SaaS deals averaging $280K ACV. $15M+ career bookings including Fortune 500 logos. Expert in MEDDPICC methodology and C-suite value selling."

2. **Experience Section**:
   - Lead each role with quota and total revenue
   - Highlight largest deals with context
   - Show land-and-expand trajectory
   - Name strategic logos (if allowed)
   - Demonstrate deal complexity

3. **Strategic Achievements**:
   - Largest single deal
   - Biggest competitive displacement
   - Most successful expansion account
   - Strategic logo acquisitions
   - Award recognition

### Bullet Point Transformations for Senior AE

WEAK: "Managed enterprise accounts"
STRONG: "Managed portfolio of 25 Fortune 1000 accounts generating $4.2M ARR, achieving 118% quota with average deal size of $340K"

WEAK: "Closed large deals"
STRONG: "Closed largest deal in company history ($1.2M ACV) with Fortune 100 financial services firm, navigating 14-month sales cycle with 18 stakeholders including CFO and CIO"

WEAK: "Expanded customer relationships"
STRONG: "Grew strategic account from $80K initial land to $1.4M ARR over 3 years through 6 expansion deals, achieving 340% net revenue retention"

WEAK: "Used MEDDIC sales methodology"
STRONG: "Applied MEDDPICC framework to qualify $8M pipeline with 85% accuracy, enabling 42% win rate on deals over $200K ACV"

### Metrics to Ask For (if missing)
- "What was your average deal size for enterprise accounts?"
- "What's the largest deal you've closed?"
- "How many stakeholders typically involved in your deals?"
- "Do you have any notable logo wins you can mention?"
- "What's an example of land-and-expand success?"
"""


def get_senior_ae_prompt() -> str:
    """Return the Senior/Enterprise AE prompt."""
    return SENIOR_AE_PROMPT
