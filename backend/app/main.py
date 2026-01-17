import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION, DEBUG, ALLOWED_ORIGINS
from app.api.routes import router
from app.api.billing_routes import router as billing_router
from app.api.auth_routes import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered Resume Review Agent with 20 years of hiring expertise"
)

# CORS middleware - allow frontend domains
default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://getpolished.ai",
    "https://www.getpolished.ai",
    "https://polished-caml6stlq-polisheds-projects-2e1afa87.vercel.app",
    "https://polished-polisheds-projects-2e1afa87.vercel.app",
    "https://polished.vercel.app",
]
# Merge with any additional origins from config
allowed_origins = list(set(default_origins + ALLOWED_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")
app.include_router(billing_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "features": ["streaming", "caching", "rate_limiting", "cognito_auth"],
        "endpoints": {
            "auth": {
                "login": "GET /api/auth/login - Redirect to Cognito login",
                "logout": "GET /api/auth/logout - Logout and clear session",
                "callback": "GET /api/auth/callback - OAuth callback (exchange code for tokens)",
                "refresh": "POST /api/auth/refresh - Refresh access token",
                "me": "GET /api/auth/me - Get current user info (requires auth)",
                "verify": "GET /api/auth/verify - Verify token validity",
                "config": "GET /api/auth/config - Get Cognito config for frontend"
            },
            "resume": {
                "upload": "POST /api/upload - Upload resume for analysis",
                "upload_stream": "POST /api/upload/stream - Upload with streaming (SSE)",
                "chat": "POST /api/chat - Chat with the resume agent",
                "chat_stream": "POST /api/chat/stream - Chat with streaming (SSE)",
                "improve": "POST /api/improve - Get targeted improvements",
                "improve_stream": "POST /api/improve/stream - Improvements with streaming (SSE)"
            },
            "session": {
                "get": "GET /api/session/{id} - Get session info",
                "delete": "DELETE /api/session/{id} - Delete session data",
                "usage": "GET /api/usage - Get rate limit usage"
            },
            "billing": {
                "checkout": "POST /api/billing/checkout - Create Pro subscription",
                "portal": "POST /api/billing/portal - Manage subscription"
            }
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
