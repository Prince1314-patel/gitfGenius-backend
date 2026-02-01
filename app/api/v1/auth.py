"""
Authentication endpoints for user registration and login.

This module provides JWT-based authentication endpoints:
- POST /register - User registration with email/password
- POST /login - User authentication and token generation
- Example protected routes demonstrating JWT validation

Implementation will be completed in task 6.
"""

from fastapi import APIRouter

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Authentication endpoints will be implemented in task 6:
# - POST /register (task 6.1)
# - POST /login (task 6.3)
# - GET /profile example (task 8.2)