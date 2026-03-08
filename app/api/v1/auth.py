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
from app.core.security import password_manager, jwt_manager, get_current_user
from app.core.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    SystemError,
    SecureLogger
)
import uuid

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/profile", response_model=StandardResponse[UserInfo])
async def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> StandardResponse[UserInfo]:
    """
    Get current user profile information.
    
    This is an example protected endpoint that demonstrates JWT authentication
    and error handling. It requires a valid JWT token in the Authorization header.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        StandardResponse[UserInfo]: User profile information
        
    Raises:
        MissingTokenError: If no JWT token provided
        InvalidTokenError: If JWT token is malformed
        TokenExpiredError: If JWT token has expired
        UserNotFoundError: If user in token not found in database
    """
    user_info = UserInfo(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at.isoformat()
    )
    
    return StandardResponse[UserInfo](
        status="success",
        data=user_info,
        message="Profile retrieved successfully."
    )


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
        DuplicateEmailError: If email already exists
        SystemError: For database or system errors
        
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
            # Log registration attempt with duplicate email
            SecureLogger.log_registration_attempt(
                email=user_data.email,
                success=False,
                error_type="DUPLICATE_EMAIL"
            )
            raise DuplicateEmailError()
        
        # Hash the password
        hashed_password = password_manager.hash_password(user_data.password)
        
        # Create new user (full_name optional per frontend contract; default to "")
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name or "",
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
        
        # Create user info for response (full_name may be "" if omitted at registration)
        user_info = UserInfo(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name or "",
            created_at=new_user.created_at.isoformat(),
        )
        
        # Create authentication response
        auth_response = AuthenticationResponse(
            user=user_info,
            access_token=access_token,
            token_type="bearer"
        )
        
        # Log successful registration
        SecureLogger.log_registration_attempt(
            email=user_data.email,
            success=True
        )
        
        return StandardResponse[AuthenticationResponse](
            status="success",
            data=auth_response,
            message="User registered successfully."
        )
        
    except DuplicateEmailError:
        # Re-raise custom authentication errors
        raise
        
    except Exception as e:
        # Handle any unexpected errors
        db.rollback()
        SecureLogger.log_system_error(
            error_message=str(e),
            context="user_registration"
        )
        raise SystemError("An error occurred during registration. Please try again.")


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
        InvalidCredentialsError: For invalid email or password
        SystemError: For database or system errors
        
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
            # Log failed authentication attempt
            SecureLogger.log_authentication_attempt(
                email=credentials.email,
                success=False
            )
            raise InvalidCredentialsError()
        
        # Verify password
        if not password_manager.verify_password(credentials.password, user.password_hash):
            # Log failed authentication attempt
            SecureLogger.log_authentication_attempt(
                email=credentials.email,
                success=False
            )
            raise InvalidCredentialsError()
        
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
        
        # Log successful authentication
        SecureLogger.log_authentication_attempt(
            email=credentials.email,
            success=True
        )
        
        return StandardResponse[AuthenticationResponse](
            status="success",
            data=auth_response,
            message="Login successful."
        )
        
    except InvalidCredentialsError:
        # Re-raise custom authentication errors
        raise
        
    except Exception as e:
        # Handle any unexpected errors
        SecureLogger.log_system_error(
            error_message=str(e),
            context="user_login"
        )
        raise SystemError("An error occurred during login. Please try again.")