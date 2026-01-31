"""
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.supabase import supabase


app = FastAPI(
    title="GiftGenius API",
    version="1.0.0",
    description="AI-powered gift recommendation system"
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
