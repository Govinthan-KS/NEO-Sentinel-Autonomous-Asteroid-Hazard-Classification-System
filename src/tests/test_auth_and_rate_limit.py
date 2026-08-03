import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Ensure src is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from asteroid_classifier.api.main import app
from asteroid_classifier.api.auth import RATE_LIMIT_STATE
from unittest.mock import MagicMock

class MockPrediction:
    is_hazardous = True
    confidence = 0.99
    is_anomaly = False
    anomaly_score = 0.1

app.state.predictor = MagicMock()
app.state.predictor.predict.return_value = MockPrediction()

client = TestClient(app)

# Dummy payload matching features
DUMMY_FEATURES = {
    "absolute_magnitude_h": 20.0,
    "estimated_diameter_min_km": 0.1,
    "estimated_diameter_max_km": 0.3,
    "relative_velocity_kmph": 10000.0,
    "miss_distance_km": 5000000.0
}

@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    """Reset the in-memory rate limit state before each test."""
    RATE_LIMIT_STATE.clear()
    yield

def test_unauthenticated_request():
    """Test that a request without an Authorization header is rejected."""
    response = client.post("/predict", json=DUMMY_FEATURES)
    assert response.status_code == 403 or response.status_code == 401
    # HTTPBearer returns 403 by default if no header is present, but our custom exception handles invalid tokens.

@patch('asteroid_classifier.api.auth.jwks_client.get_signing_key_from_jwt')
@patch('asteroid_classifier.api.auth.jwt.decode')
def test_authenticated_request(mock_jwt_decode, mock_get_signing_key):
    """Test that a request with a valid (mocked) JWT is accepted."""
    # Setup the mock to return a valid payload
    mock_jwt_decode.return_value = {
        "sub": "test_user_123",
        "email": "test@example.com",
        "role": "authenticated"
    }
    
    headers = {"Authorization": "Bearer fake-jwt-token"}
    response = client.post("/predict", json=DUMMY_FEATURES, headers=headers)
    
    # We should get a 200 OK since the JWT is mocked to be valid
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert "is_hazardous" in response.json()

@patch('asteroid_classifier.api.auth.jwks_client.get_signing_key_from_jwt')
@patch('asteroid_classifier.api.auth.jwt.decode')
def test_rate_limiting(mock_jwt_decode, mock_get_signing_key):
    """Test that a user can only make 10 requests per minute."""
    mock_jwt_decode.return_value = {
        "sub": "test_user_rate_limit",
        "email": "test@example.com",
        "role": "authenticated"
    }
    
    headers = {"Authorization": "Bearer fake-jwt-token"}
    
    # Send 10 rapid requests (should all succeed)
    for i in range(10):
        response = client.post("/predict", json=DUMMY_FEATURES, headers=headers)
        assert response.status_code == 200, f"Request {i+1} failed with {response.status_code}"
        
    # The 11th request should hit the rate limit
    response = client.post("/predict", json=DUMMY_FEATURES, headers=headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
