import pytest
from app.auth import create_access_token, verify_token

SECRET_KEY = "test-secret-key"

def test_create_and_verify_valid_token():
    user_id = "user_123"
    token = create_access_token(data={"sub": user_id}, secret_key=SECRET_KEY)
    
    # Decoded token must match input user ID
    payload = verify_token(token=token, secret_key=SECRET_KEY)
    assert payload["sub"] == user_id

def test_verify_invalid_token():
    invalid_token = "invalid.jwt.structure"
    payload = verify_token(token=invalid_token, secret_key=SECRET_KEY)
    
    # Invalid token must yield None
    assert payload is None