# Polished Roadmap

## Planned Features

---

### GitHub Skills Analyzer

**Status:** Planned
**Priority:** Medium
**Complexity:** Medium-High

#### Overview
Allow users to connect their GitHub account and select repositories. The tool analyzes the code to extract technical skills that can be highlighted on their resume.

#### User Flow
1. User clicks "Connect GitHub" button in the app
2. OAuth popup redirects to GitHub for authorization
3. User grants read access to public repos (optionally private)
4. User sees list of their repos and selects which to analyze
5. Tool analyzes selected repos and returns a list of skills/technologies
6. Skills are presented for the user to add to their resume

#### Scope (What It Does)
- Reads repository code, dependency files, and structure
- Identifies technologies, frameworks, libraries, and tools used
- Returns a list of skills extracted from the repos
- **No other assessment** - just skills extraction

#### Scope (What It Does NOT Do)
- Does not rate or score the code quality
- Does not provide feedback on coding style
- Does not analyze commit history for productivity metrics
- Does not make judgments about skill level

#### Technical Components

**Frontend:**
- "Connect GitHub" button in UI
- GitHub OAuth popup/redirect flow
- Repo selection modal (checkboxes for each repo)
- Skills display component

**Backend:**
- GitHub OAuth endpoints (authorize, callback, token exchange)
- GitHub API integration (fetch repos, files, dependency manifests)
- Dependency file parsers:
  - `package.json` (Node.js/JavaScript)
  - `requirements.txt` / `pyproject.toml` (Python)
  - `Cargo.toml` (Rust)
  - `go.mod` (Go)
  - `pom.xml` / `build.gradle` (Java)
  - `Gemfile` (Ruby)
  - `Dockerfile`, `.github/workflows/*` (DevOps)
- Claude prompt for analyzing code structure → skills
- Skills taxonomy/mapping to resume-friendly terms

**Data Flow:**
```
User selects repos
    → Backend fetches file trees + key files via GitHub API
    → Extract dependencies from manifest files
    → Send code structure + README to Claude
    → Claude returns identified skills
    → Return skills list to frontend
```

#### API Endpoints (Planned)
- `GET /api/github/auth` - Initiate OAuth flow
- `GET /api/github/callback` - OAuth callback, exchange code for token
- `GET /api/github/repos` - List user's repos
- `POST /api/github/analyze` - Analyze selected repos, return skills

#### Environment Variables Needed
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GITHUB_CALLBACK_URL`

#### Rate Limiting Considerations
- GitHub API: 60 req/hr (unauthenticated), 5000 req/hr (with user token)
- Cache repo analysis results to avoid re-fetching
- Limit number of repos that can be analyzed at once

#### Privacy & Security
- Only request minimum scopes needed (`public_repo` or `repo` for private)
- User explicitly chooses which repos to analyze
- Do not store GitHub tokens long-term (session only)
- Do not store analyzed code

---

## Completed Features

- Resume upload and AI analysis
- Chat-based resume improvement
- PDF preview with Original/Improved toggle
- PDF export
- Word document export
- STAR method for gathering metrics
- No-hallucination guardrails
- EST timezone awareness
- Session keep-alive for long pauses

---

## Ideas (Not Yet Planned)

- LinkedIn profile import
- Job description matching (paste JD, get tailored resume)
- Cover letter generation
- Interview prep based on resume
- Resume templates/themes
