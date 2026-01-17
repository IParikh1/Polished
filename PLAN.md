# Polished - Updated Product Plan

## Session-Only Privacy-First Architecture

**Version**: 1.1
**Last Updated**: January 2026
**Status**: Ready for Implementation

---

## Executive Summary

Polished is an AI-powered resume review tool using Claude AI. This plan adopts a **session-only architecture** that auto-deletes all resume data within 24 hours, minimizing GDPR/PII compliance burden while maintaining core functionality.

**Key Decision**: No long-term resume storage = 75% reduction in development time and legal costs.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SESSION-ONLY PRIVACY-FIRST ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌────────────┐         ┌────────────────┐         ┌─────────────────┐   │
│    │  Frontend  │────────►│    Backend     │────────►│      Redis      │   │
│    │  (Vercel)  │         │   (Railway)    │         │   (Upstash)     │   │
│    │            │◄────────│   Stateless    │◄────────│                 │   │
│    └────────────┘         └────────────────┘         │  TTL: 24 hours  │   │
│          │                        │                  │                 │   │
│          │                        │                  │  session:{id}   │   │
│          ▼                        ▼                  │  ├─ resume      │   │
│    ┌────────────┐         ┌────────────────┐         │  ├─ messages[]  │   │
│    │ localStorage│         │   Claude API   │         │  ├─ corrections │   │
│    │ (optional)  │         │                │         │  └─ token_count │   │
│    │ User's data │         │  Context mgmt  │         │                 │   │
│    └────────────┘         └────────────────┘         │  AUTO-EXPIRES   │   │
│                                   │                  └─────────────────┘   │
│                                   │                                        │
│                                   ▼                                        │
│                           ┌────────────────┐                               │
│                           │   PostgreSQL   │                               │
│                           │   (Neon.tech)  │                               │
│                           │                │                               │
│                           │  users         │                               │
│                           │  ├─ id         │                               │
│                           │  ├─ email      │                               │
│                           │  ├─ plan       │                               │
│                           │  ├─ usage_count│                               │
│                           │  └─ stripe_id  │                               │
│                           │                │                               │
│                           │  NO RESUMES    │                               │
│                           │  NO CHAT LOGS  │                               │
│                           └────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SESSION LIFECYCLE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   START                                                                     │
│     │                                                                       │
│     ▼                                                                       │
│   ┌─────────────────┐                                                       │
│   │ User uploads    │                                                       │
│   │ resume          │                                                       │
│   └────────┬────────┘                                                       │
│            │                                                                │
│            ▼                                                                │
│   ┌─────────────────┐     ┌─────────────────┐                              │
│   │ Generate        │────►│ Store in Redis  │                              │
│   │ session_id      │     │ TTL: 24 hours   │                              │
│   └─────────────────┘     └────────┬────────┘                              │
│                                    │                                        │
│            ┌───────────────────────┴───────────────────────┐               │
│            │                                               │               │
│            ▼                                               ▼               │
│   ┌─────────────────┐                             ┌─────────────────┐      │
│   │ User chats      │                             │ 24 hours pass   │      │
│   │ (messages added │                             │                 │      │
│   │  to session)    │                             └────────┬────────┘      │
│   └────────┬────────┘                                      │               │
│            │                                               ▼               │
│            │                                      ┌─────────────────┐      │
│            │                                      │ Redis auto-     │      │
│            │                                      │ deletes session │      │
│            │                                      │                 │      │
│            │                                      │ ALL DATA GONE   │      │
│            ▼                                      └─────────────────┘      │
│   ┌─────────────────┐                                                      │
│   │ User closes tab │──────────────────────────────────────┐               │
│   └─────────────────┘                                      │               │
│            │                                               │               │
│            ▼                                               ▼               │
│   ┌─────────────────┐                             ┌─────────────────┐      │
│   │ Optional: Save  │                             │ Session persists│      │
│   │ to localStorage │                             │ in Redis until  │      │
│   │ (user's device) │                             │ TTL expires     │      │
│   └─────────────────┘                             └─────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What We Store (and Don't Store)

| Data | Where | Duration | GDPR Status |
|------|-------|----------|-------------|
| Resume content | Redis | 24 hours (auto-delete) | Minimal risk |
| Chat history | Redis | 24 hours (auto-delete) | Minimal risk |
| User corrections | Redis | 24 hours (auto-delete) | Minimal risk |
| Email address | PostgreSQL | Until account deleted | Standard consent |
| Subscription status | PostgreSQL | Until account deleted | Legitimate interest |
| Usage count | PostgreSQL | Until account deleted | Legitimate interest |
| Stripe customer ID | PostgreSQL | Until account deleted | Contract necessity |

### What We Do NOT Store Long-Term
- ❌ Resume content
- ❌ Chat conversations
- ❌ Personal details from resumes
- ❌ Employment history
- ❌ Any resume-derived data

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

**Total Effort: 4 days**

#### Day 1: Redis Session Storage

```python
# backend/app/session_store.py

import redis
import json
from datetime import timedelta
from typing import Optional
import os

class SessionStore:
    """Redis-backed session storage with 24-hour TTL."""

    TTL = timedelta(hours=24)

    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("REDIS_URL"),
            decode_responses=True
        )

    def create_session(self, session_id: str, resume_text: str) -> dict:
        """Create new session with resume."""
        session_data = {
            "resume_text": resume_text,
            "messages": [],
            "corrections": [],
            "token_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        self.redis.setex(
            f"session:{session_id}",
            self.TTL,
            json.dumps(session_data)
        )
        return session_data

    def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session (returns None if expired/missing)."""
        data = self.redis.get(f"session:{session_id}")
        if data:
            # Refresh TTL on access (sliding expiration)
            self.redis.expire(f"session:{session_id}", self.TTL)
            return json.loads(data)
        return None

    def add_message(self, session_id: str, role: str, content: str, tokens: int):
        """Append message to session history."""
        session = self.get_session(session_id)
        if session:
            session["messages"].append({
                "role": role,
                "content": content,
                "tokens": tokens
            })
            session["token_count"] += tokens
            self.redis.setex(
                f"session:{session_id}",
                self.TTL,
                json.dumps(session)
            )

    def add_correction(self, session_id: str, correction: str):
        """Track user corrections to prevent repeated mistakes."""
        session = self.get_session(session_id)
        if session:
            session["corrections"].append(correction)
            self.redis.setex(
                f"session:{session_id}",
                self.TTL,
                json.dumps(session)
            )

    def delete_session(self, session_id: str):
        """Explicitly delete session (user request)."""
        self.redis.delete(f"session:{session_id}")
```

#### Day 2: Context Window Management

```python
# backend/app/context_manager.py

from typing import List, Dict
import tiktoken

class ContextManager:
    """Manages Claude context window to control costs."""

    MAX_CONTEXT_TOKENS = 8000  # Leave room for response
    SUMMARY_THRESHOLD = 6000   # Summarize when we hit this

    def __init__(self):
        self.encoder = tiktoken.encoding_for_model("gpt-4")  # Compatible with Claude

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))

    def build_context(self, session: dict, system_prompt: str) -> List[Dict]:
        """Build optimized context for Claude API call."""

        # Base context (always included)
        base_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume to review:\n\n{session['resume_text']}"}
        ]

        # Add corrections if any
        if session["corrections"]:
            corrections_text = "\n".join(f"- {c}" for c in session["corrections"])
            base_messages.append({
                "role": "system",
                "content": f"User corrections (DO NOT repeat these mistakes):\n{corrections_text}"
            })

        base_tokens = sum(self.count_tokens(m["content"]) for m in base_messages)
        available_tokens = self.MAX_CONTEXT_TOKENS - base_tokens

        # Add recent messages (newest first until we hit limit)
        recent_messages = []
        current_tokens = 0

        for msg in reversed(session["messages"]):
            msg_tokens = msg.get("tokens", self.count_tokens(msg["content"]))
            if current_tokens + msg_tokens > available_tokens:
                break
            recent_messages.insert(0, {
                "role": msg["role"],
                "content": msg["content"]
            })
            current_tokens += msg_tokens

        return base_messages + recent_messages

    def should_summarize(self, session: dict) -> bool:
        """Check if conversation should be summarized."""
        return session["token_count"] > self.SUMMARY_THRESHOLD
```

#### Day 3: PostgreSQL User/Billing Schema

```python
# backend/app/models.py

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class User(SQLModel, table=True):
    """Minimal user record - NO resume data."""

    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)

    # Subscription
    plan: PlanType = Field(default=PlanType.FREE)
    stripe_customer_id: Optional[str] = None

    # Usage tracking (for rate limiting)
    usage_this_month: int = Field(default=0)
    usage_reset_at: datetime = Field(default_factory=datetime.utcnow)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)

class UsageLimits:
    """Plan-based usage limits."""

    LIMITS = {
        PlanType.FREE: 3,        # 3 reviews per month
        PlanType.PRO: 999999,    # Unlimited
        PlanType.ENTERPRISE: 999999
    }

    @classmethod
    def get_limit(cls, plan: PlanType) -> int:
        return cls.LIMITS.get(plan, 3)

    @classmethod
    def check_usage(cls, user: User) -> tuple[bool, int]:
        """Returns (allowed, remaining)."""
        limit = cls.get_limit(user.plan)
        remaining = limit - user.usage_this_month
        return remaining > 0, max(0, remaining)
```

#### Day 4: Privacy Policy & Rate Limiting

```python
# backend/app/rate_limiter.py

from datetime import datetime, timedelta
from .models import User, UsageLimits, PlanType
from .database import get_db

class RateLimiter:
    """Enforce usage limits per plan."""

    async def check_and_increment(self, user_id: str) -> tuple[bool, dict]:
        """
        Check if user can make request, increment if yes.
        Returns (allowed, usage_info)
        """
        async with get_db() as db:
            user = await db.get(User, user_id)

            if not user:
                # Anonymous user - use session-based limiting
                return await self._check_anonymous(user_id)

            # Reset monthly counter if needed
            if user.usage_reset_at < datetime.utcnow() - timedelta(days=30):
                user.usage_this_month = 0
                user.usage_reset_at = datetime.utcnow()

            allowed, remaining = UsageLimits.check_usage(user)

            if allowed:
                user.usage_this_month += 1
                user.last_active = datetime.utcnow()
                await db.commit()

            return allowed, {
                "plan": user.plan,
                "used": user.usage_this_month,
                "limit": UsageLimits.get_limit(user.plan),
                "remaining": remaining - 1 if allowed else remaining,
                "resets_at": (user.usage_reset_at + timedelta(days=30)).isoformat()
            }

    async def _check_anonymous(self, session_id: str) -> tuple[bool, dict]:
        """Rate limit anonymous users by session."""
        # Anonymous gets 1 free review per session
        # Must sign up for more
        return True, {
            "plan": "anonymous",
            "used": 1,
            "limit": 1,
            "remaining": 0,
            "message": "Sign up for 3 free reviews per month"
        }
```

---

### Phase 2: Monetization (Week 2)

**Total Effort: 3 days**

#### Day 5-6: Stripe Integration

```python
# backend/app/billing.py

import stripe
from .models import User, PlanType
from .config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_IDS = {
    PlanType.PRO: "price_xxxxx",  # $9/month
    PlanType.ENTERPRISE: "price_yyyyy"  # $49/month
}

class BillingService:

    async def create_checkout_session(self, user: User, plan: PlanType) -> str:
        """Create Stripe checkout session."""

        if not user.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            # Save to DB

        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_IDS[plan],
                "quantity": 1
            }],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing"
        )

        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """Process Stripe webhooks."""
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event.type == "checkout.session.completed":
            session = event.data.object
            await self._activate_subscription(session)

        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            await self._cancel_subscription(subscription)

    async def _activate_subscription(self, session):
        """Upgrade user to paid plan."""
        # Find user by stripe_customer_id, update plan
        pass

    async def _cancel_subscription(self, subscription):
        """Downgrade user to free plan."""
        # Find user, set plan = FREE
        pass
```

#### Day 7: Paywall UI

```typescript
// frontend/src/components/Paywall.tsx

import React from 'react';

interface PaywallProps {
  usageInfo: {
    used: number;
    limit: number;
    remaining: number;
    plan: string;
  };
  onUpgrade: () => void;
}

export const Paywall: React.FC<PaywallProps> = ({ usageInfo, onUpgrade }) => {
  if (usageInfo.remaining > 0) return null;

  return (
    <div className="paywall-overlay">
      <div className="paywall-modal">
        <h2>You've used all {usageInfo.limit} free reviews this month</h2>

        <div className="plans">
          <div className="plan free">
            <h3>Free</h3>
            <p className="price">$0</p>
            <ul>
              <li>3 resume reviews/month</li>
              <li>AI-powered feedback</li>
              <li>Basic ATS tips</li>
            </ul>
            <p className="current">Current Plan</p>
          </div>

          <div className="plan pro featured">
            <div className="badge">Most Popular</div>
            <h3>Pro</h3>
            <p className="price">$9<span>/month</span></p>
            <ul>
              <li>Unlimited reviews</li>
              <li>PDF export</li>
              <li>Priority support</li>
              <li>Advanced ATS optimization</li>
            </ul>
            <button onClick={onUpgrade} className="upgrade-btn">
              Upgrade to Pro
            </button>
          </div>
        </div>

        <p className="privacy-note">
          🔒 We never store your resume. All data deleted within 24 hours.
        </p>
      </div>
    </div>
  );
};
```

---

### Phase 3: Launch Preparation (Week 3)

**Total Effort: 3 days**

#### Day 8: Testing

```python
# tests/test_session_store.py

import pytest
from app.session_store import SessionStore

@pytest.fixture
def store():
    return SessionStore()

def test_create_session(store):
    session = store.create_session("test-123", "John Doe\nSoftware Engineer")
    assert session["resume_text"] == "John Doe\nSoftware Engineer"
    assert session["messages"] == []
    assert session["corrections"] == []

def test_session_expiry(store, freezer):
    store.create_session("test-456", "Resume content")

    # Fast forward 25 hours
    freezer.move_to(datetime.utcnow() + timedelta(hours=25))

    # Session should be gone
    assert store.get_session("test-456") is None

def test_add_message(store):
    store.create_session("test-789", "Resume")
    store.add_message("test-789", "user", "Review my resume", 10)

    session = store.get_session("test-789")
    assert len(session["messages"]) == 1
    assert session["messages"][0]["role"] == "user"

def test_rate_limiting():
    # Test free tier limits
    pass

def test_context_window_management():
    # Test that old messages are dropped
    pass
```

#### Day 9: Privacy Policy & Legal

```markdown
# Privacy Policy (Simplified)

## What We Collect

**Temporary Data (Auto-deleted in 24 hours):**
- Your uploaded resume
- Chat conversation with our AI
- No human ever sees this data

**Account Data (If you sign up):**
- Email address
- Subscription status
- Usage count

## What We DON'T Do

- ❌ Store your resume permanently
- ❌ Share your data with third parties
- ❌ Use your resume to train AI models
- ❌ Sell your information

## Your Rights

- Delete your account anytime
- Request all stored data (email + subscription only)
- No resume data to request (already auto-deleted)

## Contact

privacy@polished.com
```

#### Day 10: Analytics & Monitoring

```python
# backend/app/analytics.py

from datetime import datetime
import posthog  # or mixpanel, amplitude

class Analytics:
    """Privacy-respecting analytics - no PII."""

    def __init__(self):
        posthog.api_key = os.getenv("POSTHOG_KEY")

    def track_session_start(self, session_id: str, plan: str):
        """Track new session (no resume content)."""
        posthog.capture(
            session_id,  # Anonymous ID
            "session_started",
            {"plan": plan}
        )

    def track_message_sent(self, session_id: str, message_num: int):
        """Track engagement depth."""
        posthog.capture(
            session_id,
            "message_sent",
            {"message_number": message_num}
        )

    def track_conversion(self, user_id: str, from_plan: str, to_plan: str):
        """Track upgrades."""
        posthog.capture(
            user_id,
            "plan_upgraded",
            {"from": from_plan, "to": to_plan}
        )

    def track_pdf_download(self, session_id: str):
        """Track PDF exports."""
        posthog.capture(session_id, "pdf_downloaded")
```

---

## GTM Strategy

### Launch Channels (Zero Cost)

| Channel | Action | Expected Impact |
|---------|--------|-----------------|
| **Product Hunt** | Launch post with demo video | 500-2000 visitors day 1 |
| **Hacker News** | "Show HN" post | 200-1000 visitors |
| **Reddit** | r/cscareerquestions, r/resumes, r/jobs | 100-500/week ongoing |
| **Twitter/X** | Before/after resume tips thread | 50-200 followers |
| **LinkedIn** | Personal post + resume tips content | 100-300 views |

### Launch Week Timeline

```
Day 1 (Tuesday):  Product Hunt launch
Day 2 (Wednesday): Hacker News "Show HN"
Day 3 (Thursday):  Reddit posts (staggered)
Day 4 (Friday):    Twitter thread
Day 5-7:           Engage with comments, iterate on feedback
```

### Conversion Funnel

```
Visitors (1000)
    │
    ▼ 40% upload resume
Resume Uploaded (400)
    │
    ▼ 70% complete 1 chat
First Chat (280)
    │
    ▼ 50% hit paywall (use 3 free)
Hit Paywall (140)
    │
    ▼ 10% convert to Pro
Paid Users (14)
    │
    ▼ $9/month
Revenue: $126/month per 1000 visitors
```

---

## Cost Summary

### One-Time Costs

| Item | Cost |
|------|------|
| Development (10 days) | $0 (founder time) |
| Privacy policy template | $200-500 |
| Domain + branding | $100 |
| **Total** | **$300-600** |

### Monthly Operating Costs

| Item | Free Tier | At 1K Users | At 10K Users |
|------|-----------|-------------|--------------|
| Vercel (frontend) | $0 | $0 | $20 |
| Railway (backend) | $5 | $20 | $50 |
| Upstash Redis | $0 | $10 | $30 |
| Neon PostgreSQL | $0 | $0 | $25 |
| Claude API | $0 | $150 | $1,500 |
| **Total** | **$5** | **$180** | **$1,625** |

### Revenue Projection

| Users | Free (90%) | Paid (10%) | MRR | Profit |
|-------|------------|------------|-----|--------|
| 100 | 90 | 10 | $90 | -$90 |
| 500 | 450 | 50 | $450 | +$200 |
| 1,000 | 900 | 100 | $900 | +$720 |
| 5,000 | 4,500 | 500 | $4,500 | +$3,500 |
| 10,000 | 9,000 | 1,000 | $9,000 | +$7,375 |

**Break-even: ~200 paying users ($1,800 MRR)**

---

## Feature Roadmap

### Now (MVP+)
- [x] AI resume review
- [x] Chat interface
- [x] PDF parsing
- [ ] Redis session storage (24h TTL)
- [ ] User accounts (email only)
- [ ] Stripe billing
- [ ] Rate limiting (3 free/month)

### Next (Month 2)
- [ ] PDF export of polished resume
- [ ] Job-specific tailoring ("Optimize for Google SWE")
- [ ] ATS score display
- [ ] Email notifications

### Later (Month 3+)
- [ ] Cover letter generation
- [ ] LinkedIn profile review
- [ ] Chrome extension
- [ ] Team/enterprise features

### Not Planned (Privacy Reasons)
- ~~Resume storage/history~~
- ~~Cross-device sync~~
- ~~"Remember my resume"~~
- ~~Returning user personalization~~

---

## Success Metrics

### Week 1
- [ ] 500+ Product Hunt upvotes
- [ ] 100+ signups
- [ ] 10+ paid conversions

### Month 1
- [ ] 1,000 registered users
- [ ] 100 paying users ($900 MRR)
- [ ] <5% churn rate

### Month 3
- [ ] 5,000 registered users
- [ ] 500 paying users ($4,500 MRR)
- [ ] Profitable

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Claude API costs spike | Implement aggressive caching, context limits |
| Low conversion rate | A/B test paywall timing, pricing |
| Competition | Focus on privacy angle as differentiator |
| API rate limits | Queue system for high traffic |

---

## Privacy as Marketing

### Key Messages

> "We delete your resume in 24 hours. Because your career is your business, not ours."

> "No signup required. No data stored. Just expert feedback."

> "The resume tool that forgets you exist."

### Trust Badges
- 🔒 Auto-delete in 24 hours
- 🚫 No data sharing
- ✅ GDPR compliant
- 🤖 AI-powered, human-free

---

## Next Steps

1. **This Week**: Implement Redis session storage + rate limiting
2. **Next Week**: Stripe integration + paywall UI
3. **Week 3**: Testing + privacy policy + launch prep
4. **Week 4**: Product Hunt launch

**Total Time to Launch: 3-4 weeks**
**Total Cost to Launch: ~$500**
**Break-even Target: 200 paying users**
