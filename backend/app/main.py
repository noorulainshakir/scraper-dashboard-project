"""
FastAPI application entry point
"""
import sys
import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import get_settings
from app.core.logging import setup_logging
from app.api.v1.routes import wink_sync
from app.api.websocket import router as websocket_router

settings = get_settings()

# Setup logging
setup_logging(log_level="INFO" if not settings.debug else "DEBUG")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with v1 prefix
app.include_router(
    wink_sync.router,
    prefix=settings.api_v1_prefix
)

# Also include without v1 prefix for backward compatibility
app.include_router(
    wink_sync.router,
    prefix="/api"
)

# Include WebSocket router
app.include_router(websocket_router)

# Middleware to add no-cache headers for JS files
@app.middleware("http")
async def no_cache_js_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith('.js'):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Mount frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

