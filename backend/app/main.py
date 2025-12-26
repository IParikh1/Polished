import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION, DEBUG
from app.api.routes import router

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
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://getpolished.ai",
    "https://www.getpolished.ai",
    "https://polished.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "endpoints": {
            "upload": "POST /api/upload - Upload resume for analysis",
            "chat": "POST /api/chat - Chat with the resume agent",
            "improve": "POST /api/improve - Get targeted improvements",
            "session": "GET /api/session/{id} - Get session info"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
