# Product Requirements Document: Authentication & Paywall System

**Product:** Polished - AI Resume Tool for Tech Sales Professionals
**Version:** 3.0
**Date:** January 2026
**Author:** DevTeam Orchestrator
**Status:** In Development

---

## Executive Summary

Add user authentication and subscription-based paywall to Polished. This enables:
1. **User Data Isolation** - Each user sees only their own batches and resumes
2. **Subscription Tiers** - Free vs Pro users with feature gating
3. **Revenue Generation** - Stripe integration for paid subscriptions

### Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Authentication | Clerk | Fast implementation, excellent DX, social logins included |
| Payments | Stripe | Industry standard, Clerk integration, subscription management |
| Future Migration | AWS Cognito | Planned for scale (cheaper at high volume) |

---

## Goals & Success Metrics

### Business Goals
| Goal | Target | Timeline |
|------|--------|----------|
| User sign-ups | 100 users | Day 30 |
| Pro conversions | 10% conversion rate | Day 60 |
| MRR from subscriptions | $1,000 | Day 90 |

### Product Metrics
| Metric | Target |
|--------|--------|
| Sign-up completion rate | >80% |
| Free-to-Pro conversion | >10% |
| Churn rate | <5% monthly |

---

## Feature 1: User Authentication (Clerk)

### Overview
Implement Clerk authentication with sign-in, sign-up, and user management.

### User Flow

```
1. User visits app → Redirect to sign-in if not authenticated
2. Sign-in options:
   - Google OAuth (one-click)
   - Email + Password
   - Magic Link (email)
3. After sign-in → Redirect to /batches (dashboard)
4. User data scoped to their user_id
```

### Technical Requirements

#### Frontend Changes

**New Files:**
- `frontend/src/components/auth/SignInPage.tsx` - Clerk SignIn component
- `frontend/src/components/auth/SignUpPage.tsx` - Clerk SignUp component
- `frontend/src/components/auth/UserButton.tsx` - User menu in header
- `frontend/src/providers/ClerkProvider.tsx` - Clerk context wrapper

**Modified Files:**
- `frontend/src/App.tsx` - Add auth routes, protect routes
- `frontend/src/components/Layout.tsx` - Add UserButton to header
- `frontend/src/api/batchClient.ts` - Add auth token to requests
- `frontend/src/main.tsx` - Wrap with ClerkProvider

#### Backend Changes

**New Files:**
- `backend/app/middleware/auth.py` - Clerk JWT verification
- `backend/app/models/user_schemas.py` - User-related schemas

**Modified Files:**
- `backend/app/api/batch_routes.py` - Extract user_id from auth, filter by user
- `backend/app/services/aws_store.py` - Enforce user_id on all operations
- `backend/app/aws/dynamodb.py` - User-scoped queries
- `backend/requirements.txt` - Add PyJWT, cryptography

#### Environment Variables

**Frontend (Vercel):**
```
VITE_CLERK_PUBLISHABLE_KEY=pk_live_xxx
```

**Backend (Railway):**
```
CLERK_SECRET_KEY=sk_live_xxx
CLERK_PUBLISHABLE_KEY=pk_live_xxx
```

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| A.1 | Create Clerk account and configure app | 15 min | None |
| A.2 | Install Clerk packages (frontend) | 10 min | A.1 |
| A.3 | Create ClerkProvider wrapper | 20 min | A.2 |
| A.4 | Create SignInPage component | 30 min | A.3 |
| A.5 | Create SignUpPage component | 20 min | A.3 |
| A.6 | Add auth routes to App.tsx | 20 min | A.4, A.5 |
| A.7 | Create ProtectedRoute component | 30 min | A.6 |
| A.8 | Add UserButton to Layout header | 20 min | A.3 |
| A.9 | Update batchClient to include auth token | 30 min | A.3 |
| A.10 | Create backend auth middleware | 45 min | A.1 |
| A.11 | Update batch_routes.py for user isolation | 45 min | A.10 |
| A.12 | Update aws_store.py for user scoping | 30 min | A.10 |
| A.13 | Test full auth flow E2E | 30 min | All above |

**Total: ~5.5 hours**

---

## Feature 2: User Data Isolation

### Overview
Ensure users can only access their own data (batches, resumes, placements).

### Data Model Changes

**Batches Table:**
- Already has `user_id` field ✓
- Already has `user-index` GSI ✓
- Need to enforce filtering in all queries

**Implementation:**

```python
# All batch queries MUST include user_id filter
async def list_batches(self, user_id: str, limit: int = 50):
    # ALWAYS filter by user_id - never return all batches
    return self.db.list_batches(user_id=user_id, limit=limit)

# Batch access must verify ownership
async def get_batch(self, batch_id: str, user_id: str):
    batch = self.db.get_batch(batch_id)
    if batch and batch.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    return batch
```

### Security Rules

| Operation | Rule |
|-----------|------|
| List batches | Only return user's batches |
| Get batch | Verify user owns batch |
| Create batch | Set user_id from auth token |
| Update batch | Verify user owns batch |
| Delete batch | Verify user owns batch |
| All resume operations | Verify user owns parent batch |
| All placement operations | Verify user owns parent batch |

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| D.1 | Add user ownership check helper | 20 min | A.10 |
| D.2 | Update list_batches endpoint | 20 min | D.1 |
| D.3 | Update get_batch endpoint | 15 min | D.1 |
| D.4 | Update create_batch endpoint | 15 min | D.1 |
| D.5 | Update delete_batch endpoint | 15 min | D.1 |
| D.6 | Update all resume endpoints | 30 min | D.1 |
| D.7 | Update rankings endpoint | 15 min | D.1 |
| D.8 | Update placement endpoints | 20 min | D.1 |
| D.9 | Test data isolation E2E | 30 min | All above |

**Total: ~3 hours**

---

## Feature 3: Subscription Paywall (Stripe)

### Overview
Implement Stripe subscriptions with Free and Pro tiers. Pro features are grayed out for Free users.

### Subscription Tiers

| Feature | Free | Pro ($29/mo) |
|---------|------|--------------|
| Batches per month | 5 | Unlimited |
| Resumes per batch | 50 | 500 |
| Basic scoring | ✓ | ✓ |
| Role-specific optimization | ✓ | ✓ |
| JD Matching | ✗ (grayed) | ✓ |
| Deep Analysis | ✗ (grayed) | ✓ |
| Resume Writing | ✗ (grayed) | ✓ |
| Export to PDF/DOCX | ✗ (grayed) | ✓ |
| Priority processing | ✗ | ✓ |

### User Flow

```
1. Free user clicks grayed-out Pro feature
2. Upgrade modal appears with feature benefits
3. User clicks "Upgrade to Pro"
4. Redirect to Stripe Checkout
5. After payment → Webhook updates user tier
6. User returns to app with Pro features unlocked
```

### Technical Requirements

#### Frontend Changes

**New Files:**
- `frontend/src/components/paywall/UpgradeModal.tsx` - Upgrade prompt
- `frontend/src/components/paywall/PricingPage.tsx` - Pricing comparison
- `frontend/src/components/paywall/ProBadge.tsx` - "Pro" feature indicator
- `frontend/src/components/paywall/FeatureGate.tsx` - Wrapper to gate features
- `frontend/src/hooks/useSubscription.ts` - Subscription status hook

**Modified Files:**
- `frontend/src/pages/BatchDashboard.tsx` - Gate Pro features
- `frontend/src/components/batch/JDMatcher.tsx` - Gate with FeatureGate
- `frontend/src/components/writing/ResumeWriter.tsx` - Gate with FeatureGate
- `frontend/src/pages/WritingPage.tsx` - Gate Pro features
- `frontend/src/components/Layout.tsx` - Show subscription status

#### Backend Changes

**New Files:**
- `backend/app/api/stripe_routes.py` - Checkout, webhooks, portal
- `backend/app/services/subscription_service.py` - Subscription logic
- `backend/app/models/subscription_schemas.py` - Subscription models

**Modified Files:**
- `backend/app/services/premium_gate.py` - Connect to real user tiers
- `backend/app/aws/dynamodb.py` - Add users table operations
- `backend/app/main.py` - Register stripe routes

#### New DynamoDB Table

**Table: polished-users**
```
{
  "user_id": "user_clerk_xxx",        // Clerk user ID (PK)
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "free",         // free, pro, enterprise
  "stripe_customer_id": "cus_xxx",
  "stripe_subscription_id": "sub_xxx",
  "subscription_status": "active",     // active, canceled, past_due
  "created_at": "2026-01-24T...",
  "updated_at": "2026-01-24T..."
}
```

#### Stripe Webhook Events

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create/update user tier to Pro |
| `customer.subscription.updated` | Sync subscription status |
| `customer.subscription.deleted` | Downgrade to Free |
| `invoice.payment_failed` | Mark subscription past_due |

#### Environment Variables

**Backend (Railway):**
```
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRO_PRICE_ID=price_xxx
```

**Frontend (Vercel):**
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
```

### Task Breakdown

| ID | Task | Estimate | Dependencies |
|----|------|----------|--------------|
| S.1 | Create Stripe account and configure products | 20 min | None |
| S.2 | Create polished-users DynamoDB table | 15 min | None |
| S.3 | Add user table operations to dynamodb.py | 30 min | S.2 |
| S.4 | Create subscription_service.py | 45 min | S.3 |
| S.5 | Create stripe_routes.py (checkout, webhook, portal) | 1 hour | S.4 |
| S.6 | Update premium_gate.py to use real user tiers | 30 min | S.4 |
| S.7 | Create useSubscription hook (frontend) | 30 min | A.3 |
| S.8 | Create FeatureGate component | 30 min | S.7 |
| S.9 | Create UpgradeModal component | 45 min | S.7 |
| S.10 | Create ProBadge component | 15 min | None |
| S.11 | Gate JD Matching features | 20 min | S.8 |
| S.12 | Gate Resume Writing features | 20 min | S.8 |
| S.13 | Gate Export features | 20 min | S.8 |
| S.14 | Add subscription status to Layout | 20 min | S.7 |
| S.15 | Create PricingPage | 45 min | S.7 |
| S.16 | Test Stripe checkout flow E2E | 30 min | All above |
| S.17 | Test webhook handling | 30 min | S.5 |

**Total: ~8.5 hours**

---

## Implementation Order

### Phase 1: Authentication (Day 1)
1. Set up Clerk account
2. Implement frontend auth (A.1-A.9)
3. Implement backend auth middleware (A.10-A.12)
4. Test E2E (A.13)

### Phase 2: Data Isolation (Day 1-2)
1. Add ownership checks (D.1)
2. Update all endpoints (D.2-D.8)
3. Test isolation (D.9)

### Phase 3: Stripe Integration (Day 2-3)
1. Set up Stripe (S.1-S.2)
2. Backend subscription service (S.3-S.6)
3. Frontend subscription hooks (S.7-S.10)
4. Gate Pro features (S.11-S.13)
5. Test payment flow (S.16-S.17)

---

## UI/UX Specifications

### Grayed-Out Pro Features

```tsx
// Pro feature appears grayed with lock icon
<FeatureGate feature="jd_matching">
  <JDMatcher />
</FeatureGate>

// When clicked by Free user:
// - Shows UpgradeModal with feature benefits
// - "Upgrade to Pro - $29/mo" button
// - Links to full pricing page
```

### Visual Treatment

| State | Appearance |
|-------|------------|
| Pro feature (Free user) | 50% opacity, lock icon overlay, "Pro" badge |
| Pro feature (Pro user) | Normal appearance, no badge |
| Upgrade modal | Feature screenshot, benefits list, CTA button |

### Upgrade Modal Content

```
┌─────────────────────────────────────────┐
│ 🔒 Unlock JD Matching                   │
│                                         │
│ Match resumes against job descriptions  │
│ to find the best candidates faster.     │
│                                         │
│ ✓ AI-powered skill matching             │
│ ✓ Gap analysis & recommendations        │
│ ✓ Keyword optimization suggestions      │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │    Upgrade to Pro - $29/month      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│         View all Pro features →         │
└─────────────────────────────────────────┘
```

---

## Testing Plan

### Authentication Tests
- [ ] Sign up with email/password
- [ ] Sign up with Google OAuth
- [ ] Sign in with existing account
- [ ] Sign out
- [ ] Protected routes redirect to sign-in
- [ ] Auth token included in API requests
- [ ] Backend validates JWT correctly

### Data Isolation Tests
- [ ] User A cannot see User B's batches
- [ ] User A cannot access User B's batch by ID
- [ ] User A cannot delete User B's batch
- [ ] New batches have correct user_id
- [ ] Resume operations check parent batch ownership

### Subscription Tests
- [ ] Free user sees grayed Pro features
- [ ] Clicking grayed feature shows upgrade modal
- [ ] Stripe Checkout completes successfully
- [ ] Webhook updates user tier to Pro
- [ ] Pro user can access all features
- [ ] Subscription cancellation downgrades to Free
- [ ] Usage limits enforced per tier

---

## Rollout Plan

### Phase 1: Internal Testing (Day 1-3)
- Complete implementation
- Test all flows internally
- Fix bugs

### Phase 2: Soft Launch (Day 4-7)
- Enable for existing pilot users
- Monitor for issues
- Gather feedback

### Phase 3: Public Launch (Day 8+)
- Enable sign-up for all
- Marketing push
- Monitor conversion rates

---

## Future Considerations

### AWS Cognito Migration
When to migrate:
- >10,000 MAU (cost savings significant)
- Need advanced features (MFA, adaptive auth)

Migration path:
1. Export Clerk users
2. Import to Cognito
3. Update frontend/backend auth
4. Redirect existing sessions

### Enterprise Tier
Future tier with:
- Team management
- SSO/SAML
- Custom scoring rules
- Dedicated support
- SLA guarantees

---

## Appendix

### Clerk vs Cognito Cost Comparison

| MAU | Clerk Cost | Cognito Cost |
|-----|------------|--------------|
| 1,000 | $0 | $0 |
| 10,000 | $0 | $0 |
| 50,000 | $800/mo | $0 |
| 100,000 | $1,800/mo | $275/mo |
| 500,000 | $9,800/mo | $2,475/mo |

Migration break-even: ~50,000 MAU
