"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.supabase import supabase
from app.core.database_init import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database tables
    logger.info("🚀 Starting GiftGenius API...")
    try:
        init_database(supabase)
        logger.info("✅ Application startup complete")
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        # Continue anyway - the app can still run, just database might have issues
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down GiftGenius API...")


app = FastAPI(
    title="GiftGenius API",
    version="1.0.0",
    description="AI-powered gift recommendation system",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "success",
        "data": {
            "message": "GiftGenius API is running",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        }
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    try:
        # Test Supabase connection
        response = supabase.table("users").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "success",
        "data": {
            "api": "healthy",
            "database": db_status,
            "environment": settings.ENVIRONMENT
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
