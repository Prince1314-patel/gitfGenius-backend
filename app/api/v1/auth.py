"""
Authentication endpoints for user registration and login.

This module provides JWT-based authentication endpoints:
- POST /register - User registration with email/password
- POST /login - User authentication and token generation
- Example protected routes demonstrating JWT validation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.schemas import (
    UserRegistrationRequest, 
    UserLoginRequest, 
    AuthenticationResponse, 
    StandardResponse,
    UserInfo
)
from app.core.security import password_manager, jwt_manager
import uuid

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=StandardResponse[AuthenticationResponse])
async def register_user(
    user_data: UserRegistrationRequest,
    db: Session = Depends(get_session)
) -> StandardResponse[AuthenticationResponse]:
    """
    Register a new user with email and password.
    
    This endpoint creates a new user account with comprehensive validation:
    - Email format validation and uniqueness check
    - Password length validation (minimum 8 characters)
    - Secure password hashing using bcrypt
    - JWT token generation for immediate authentication
    
    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session dependency
        
    Returns:
        StandardResponse[AuthenticationResponse]: Success response with user info and JWT token
        
    Raises:
        HTTPException: 409 if email already exists, 400 for validation errors
        
    Requirements implemented:
    - 1.1: Creates new user account with valid email and password
    - 1.2: Prevents duplicate email registration
    - 1.3: Validates email format
    - 1.4: Enforces password length requirements
    - 1.5: Hashes password using bcrypt before storage
    - 1.6: Returns standardized response format
    - 6.1, 6.2, 6.3: Database integration and response formatting
    """
    
    try:
        # Check if user with this email already exists
        statement = select(User).where(User.email == user_data.email)
        existing_user = db.exec(statement).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "An account with this email address already exists."
                }
            )
        
        # Hash the password
        hashed_password = password_manager.hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name
        )
        
        # Add to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate JWT token
        token_data = {
            "user_id": str(new_user.id),
            "email": new_user.email
        }
        access_token = jwt_manager.create_access_token(token_data)
        
        # Create user info for response
        user_info = UserInfo(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            created_at=new_user.created_at.isoformat()
        )
        
        # Create authentication response
        auth_response = AuthenticationResponse(
            user=user_info,
            access_token=access_token,
            token_type="bearer"
        )
        
        return StandardResponse[AuthenticationResponse](
            status="success",
            data=auth_response,
            message="User registered successfully."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate email)
        raise
        
    except Exception as e:
        # Handle any unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": None,
                "message": "An error occurred during registration. Please try again."
            }
        )


@router.post("/login", response_model=StandardResponse[AuthenticationResponse])
async def login_user(
    credentials: UserLoginRequest,
    db: Session = Depends(get_session)
) -> StandardResponse[AuthenticationResponse]:
    """
    Authenticate user and return JWT token.
    
    This endpoint authenticates a user with email and password:
    - Validates email format and finds user in database
    - Verifies password using bcrypt
    - Generates JWT token for successful authentication
    - Returns user info and token in standardized format
    
    Args:
        credentials: User login credentials (email, password)
        db: Database session dependency
        
    Returns:
        StandardResponse[AuthenticationResponse]: Success response with user info and JWT token
        
    Raises:
        HTTPException: 401 for invalid credentials, 400 for validation errors
        
    Requirements implemented:
    - 2.1: Authenticates user with valid email and password
    - 2.2: Returns authentication failure for incorrect credentials
    - 2.3: Generates JWT token with 24-hour expiration
    - 2.4: Includes user identification in token payload
    - 2.5: Returns success response in standardized format
    - 2.6: Returns error response in standardized format
    """
    
    try:
        # Find user by email
        statement = select(User).where(User.email == credentials.email)
        user = db.exec(statement).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "Invalid email or password."
                }
            )
        
        # Verify password
        if not password_manager.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": "error",
                    "data": None,
                    "message": "Invalid email or password."
                }
            )
        
        # Generate JWT token
        token_data = {
            "user_id": str(user.id),
            "email": user.email
        }
        access_token = jwt_manager.create_access_token(token_data)
        
        # Create user info for response
        user_info = UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat()
        )
        
        # Create authentication response
        auth_response = AuthenticationResponse(
            user=user_info,
            access_token=access_token,
            token_type="bearer"
        )
        
        return StandardResponse[AuthenticationResponse](
            status="success",
            data=auth_response,
            message="Login successful."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like authentication failures)
        raise
        
    except Exception as e:
        # Handle any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "data": None,
                "message": "An error occurred during login. Please try again."
            }
        )