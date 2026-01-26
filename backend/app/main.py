"""
Polished Resume Ranking System - FastAPI Application
Main entry point for the backend API.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time
from datetime import datetime

from .api.batch_routes import router as batch_router
from .api.placement_routes import router as placement_router
from .api.consult_routes import router as consult_router
from .api.resume_routes import router as resume_router
from .api.stripe_routes import router as stripe_router
from .api.admin_routes import router as admin_router
from .services.batch_cache import get_cache
from .services.premium_gate import get_premium_gate


# Application metadata
APP_TITLE = "Polished Resume Ranking System"
APP_DESCRIPTION = """
A scalable resume sorting and ranking system with tiered features.

## Features

### Core (Free)
- Batch upload of resumes (PDF, DOCX, TXT)
- Quick rule-based scoring
- Resume ranking
- CSV/JSON export

### Premium Add-ons
- **JD Matching**: Match resumes against job descriptions
- **Deep Analysis**: Comprehensive LLM-powered resume analysis
- **Resume Consulting**: AI-powered rewrite suggestions
- **Resume Writing**: AI-powered resume generation with document export (PDF/DOCX)

### Revenue
- Placement tracking with $250 per verified placement

## API Sections
- **Batches**: Create and manage resume batches
- **Placements**: Track successful candidate placements
- **Consulting**: Resume improvement suggestions (premium)
"""

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {APP_TITLE} v{APP_VERSION}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Initialize services
    cache = get_cache()
    health = cache.health_check()
    print(f"Cache status: {health['status']} ({health['backend']})")

    # Initialize premium gate
    gate = get_premium_gate()
    print(f"Premium bypass mode: {gate.bypass_mode}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add request processing time header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting."""
    # Skip for health check and docs
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get client identifier
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"ip:{client_ip}"

    # Check rate limit
    cache = get_cache()
    allowed, remaining = cache.check_rate_limit(identifier, limit=100, window=60)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": "Too many requests. Please try again later.",
            },
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "60",
            }
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "Error",
            "detail": exc.detail if isinstance(exc.detail, dict) else None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    print(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "").lower() == "true" else None,
        },
    )


# Include routers
app.include_router(batch_router, prefix="/api/v1")
app.include_router(placement_router, prefix="/api/v1")
app.include_router(consult_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(stripe_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the application and its dependencies.
    """
    cache = get_cache()
    cache_health = cache.health_check()

    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "dependencies": {
            "cache": cache_health,
        },
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


# API info endpoint
@app.get("/api/v1", tags=["API"])
async def api_info():
    """API version information."""
    return {
        "version": "v1",
        "endpoints": {
            "batches": "/api/v1/batches",
            "placements": "/api/v1/placements",
            "consulting": "/api/v1/consulting",
            "resume": "/api/v1/resume",
            "config": "/api/v1/config",
        },
        "documentation": "/docs",
    }


# LLM Configuration status endpoint
@app.get("/api/v1/config/llm-status", tags=["Config"])
async def get_llm_status():
    """
    Check LLM service configuration status.

    Returns whether the Anthropic API key is configured and LLM features are available.
    Does not expose the actual API key value.
    """
    from .services.resume_writer import get_writer
    from .services.metrics_extractor import get_extractor

    writer = get_writer()
    extractor = get_extractor()

    # Check if API key is configured (without exposing it)
    api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
    api_key_prefix = None
    if api_key_set:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        # Show only the first 10 chars for verification (e.g., "sk-ant-api...")
        api_key_prefix = key[:10] + "..." if len(key) > 10 else "***"

    # Try to import anthropic to check if package is installed
    try:
        import anthropic
        anthropic_installed = True
    except ImportError:
        anthropic_installed = False

    return {
        "llm_configured": api_key_set and anthropic_installed,
        "api_key_set": api_key_set,
        "api_key_prefix": api_key_prefix,
        "anthropic_package_installed": anthropic_installed,
        "services": {
            "resume_writer": {
                "available": writer.is_available(),
                "features": {
                    "full_resume_generation": writer.is_available(),
                    "section_rewriting": True,  # Rule-based fallback available
                    "summary_generation": True,  # Rule-based fallback available
                    "bullet_enhancement": True,  # Rule-based fallback available
                }
            },
            "metrics_extraction": {
                "available": extractor.is_available(),
                "llm_enhanced": api_key_set and anthropic_installed,
            }
        },
        "configuration_help": {
            "railway": "Set ANTHROPIC_API_KEY in Railway environment variables",
            "local": "Set ANTHROPIC_API_KEY in .env file or export as environment variable",
            "get_key_url": "https://console.anthropic.com/account/keys",
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
    )
