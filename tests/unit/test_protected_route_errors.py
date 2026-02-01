"""
Unit tests for protected route error handling.

This module tests error handling for protected routes that require JWT authentication.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestProtectedRouteErrors:
    """Test error handling for protected routes."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_protected_route_missing_token(self, client):
        """Test protected route access without JWT token."""
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 401
        response_data = response.json()
        
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert "authentication required" in response_data["message"].lower()
        assert response_data["error_code"] == "MISSING_TOKEN"
        assert "WWW-Authenticate" in response.headers
    
    def test_protected_route_invalid_token(self, client):
        """Test protected route access with invalid JWT token."""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        assert response.status_code == 401
        response_data = response.json()
        
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert "invalid token" in response_data["message"].lower()
        assert response_data["error_code"] == "INVALID_TOKEN"
    
    def test_protected_route_malformed_token(self, client):
        """Test protected route access with malformed JWT token."""
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        assert response.status_code == 401
        response_data = response.json()
        
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        assert "invalid token" in response_data["message"].lower()
        assert response_data["error_code"] == "INVALID_TOKEN"
    
    def test_protected_route_expired_token(self, client):
        """Test protected route access with expired JWT token."""
        # Create an expired token (this is a mock expired token)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        assert response.status_code == 401
        response_data = response.json()
        
        assert response_data["status"] == "error"
        assert response_data["data"] is None
        # Could be either expired or invalid token error depending on validation order
        assert response_data["error_code"] in ["TOKEN_EXPIRED", "INVALID_TOKEN"]
    
    def test_protected_route_with_bearer_prefix_missing(self, client):
        """Test protected route access with token but missing Bearer prefix."""
        headers = {"Authorization": "some-token-without-bearer"}
        response = client.get("/api/v1/auth/profile", headers=headers)
        
        # FastAPI HTTPBearer should handle this and return 403 or similar
        # But our middleware should catch it and return standardized error
        assert response.status_code in [401, 403]
        
        if response.status_code == 401:
            response_data = response.json()
            assert response_data["status"] == "error"
            assert response_data["data"] is None
    
    def test_protected_route_error_response_format_consistency(self, client):
        """Test that all protected route errors follow the same response format."""
        test_cases = [
            # No token
            {"headers": {}, "expected_status": 401},
            # Invalid token
            {"headers": {"Authorization": "Bearer invalid"}, "expected_status": 401},
            # Malformed token
            {"headers": {"Authorization": "Bearer not.a.jwt"}, "expected_status": 401},
        ]
        
        for case in test_cases:
            response = client.get("/api/v1/auth/profile", headers=case["headers"])
            assert response.status_code == case["expected_status"]
            
            response_data = response.json()
            
            # Check standardized response format
            assert "status" in response_data
            assert "data" in response_data
            assert "message" in response_data
            assert "error_code" in response_data
            
            assert response_data["status"] == "error"
            assert response_data["data"] is None
            assert isinstance(response_data["message"], str)
            assert isinstance(response_data["error_code"], str)
            assert len(response_data["message"]) > 0
            assert len(response_data["error_code"]) > 0
