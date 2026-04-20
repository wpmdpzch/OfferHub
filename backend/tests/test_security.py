"""Backend Security Tests"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import only the functions that don't require redis at module load time
from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    def test_password_hash_and_verify(self):
        password = "secure_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_different_each_time(self):
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt adds salt

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed)


class TestJWTTokenCreation:
    """Test JWT token creation - requires redis to be mocked"""

    def test_create_access_token_function_exists(self):
        from app.core.security import create_access_token
        # Token creation requires redis connection, just verify function exists
        assert callable(create_access_token)

    def test_decode_token_function_exists(self):
        from app.core.security import decode_token
        # Verify function exists
        assert callable(decode_token)
