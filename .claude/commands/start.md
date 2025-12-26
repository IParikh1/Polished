---
allowed-tools: Bash(*)
description: Start the Polished frontend and backend servers
---

# Start Polished Servers

Start both the Polished backend (FastAPI) and frontend (React/Vite) servers.

## Steps

1. Start the FastAPI backend on port 8001:
   ```bash
   cd /tmp/ResumeAgent/backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ```
   Run this in the background.

2. Start the React frontend on port 5173:
   ```bash
   cd /tmp/ResumeAgent/frontend && npm run dev
   ```
   Run this in the background.

3. Report the URLs to the user:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

Both servers should be started as background tasks so the user can continue working.
