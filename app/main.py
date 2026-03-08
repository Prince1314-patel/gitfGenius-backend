"""
Main FastAPI application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import logging

from app.core.config import settings
from app.database import engine
from app.core.database_init import init_database
from app.core.middleware import (
    ErrorHandlingMiddleware,
    authentication_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.core.exceptions import AuthenticationError
from app.api.v1.auth import router as auth_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.memories import router as memories_router

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
        init_database(engine)
        logger.info("Application startup complete")
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

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add exception handlers for specific error types (HTTPException before Exception)
app.add_exception_handler(AuthenticationError, authentication_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API versioning (calendar before contacts so /calendar is not matched as /contacts/{id})
app.include_router(auth_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(memories_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")


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
    """Detailed health check (PostgreSQL connection)."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
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
