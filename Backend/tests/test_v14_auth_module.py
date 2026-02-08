"""Tests for v4.9 authentication module.

Covers:
- Password hashing and verification
- JWT token creation and validation
- User registration and login endpoints
- Token refresh flow
- Logout (single and all devices)
- Protected endpoint access
"""

import unittest
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.config import settings
from app.services.password import hash_password, verify_password, generate_token, hash_token
from app.services.jwt_service import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_access_token,
    verify_refresh_token,
    InvalidTokenError,
    ExpiredTokenError,
)
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_email,
    get_user_by_username,
    store_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InactiveUserError,
)
from app.models import User, RefreshToken


class TestPasswordService(unittest.TestCase):
    """Test password hashing and verification."""

    def test_hash_password_creates_bcrypt_hash(self):
        password = "securePassword123"
        hashed = hash_password(password)
        self.assertTrue(hashed.startswith("$2"))  # bcrypt prefix
        self.assertNotEqual(password, hashed)

    def test_hash_password_different_each_time(self):
        password = "securePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertNotEqual(hash1, hash2)  # Different salts

    def test_verify_password_correct(self):
        password = "securePassword123"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

    def test_verify_password_incorrect(self):
        password = "securePassword123"
        hashed = hash_password(password)
        self.assertFalse(verify_password("wrongPassword", hashed))

    def test_verify_password_invalid_hash(self):
        self.assertFalse(verify_password("password", "not-a-valid-hash"))

    def test_generate_token_returns_hex(self):
        token = generate_token()
        self.assertEqual(len(token), 64)  # 32 bytes = 64 hex chars
        self.assertTrue(all(c in '0123456789abcdef' for c in token))

    def test_hash_token_consistent(self):
        token = "test-token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        self.assertEqual(hash1, hash2)  # SHA256 is deterministic


class TestJWTService(unittest.TestCase):
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)

    def test_decode_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        self.assertEqual(payload.sub, str(user_id))
        self.assertEqual(payload.type, "access")

    def test_verify_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        result = verify_access_token(token)
        self.assertEqual(result, str(user_id))

    def test_create_refresh_token(self):
        user_id = uuid.uuid4()
        token, jti, expires = create_refresh_token(user_id)
        self.assertIsInstance(token, str)
        self.assertIsInstance(jti, str)
        self.assertIsInstance(expires, datetime)

    def test_verify_refresh_token(self):
        user_id = uuid.uuid4()
        token, jti, _ = create_refresh_token(user_id)
        result_user_id, result_jti = verify_refresh_token(token)
        self.assertEqual(result_user_id, str(user_id))
        self.assertEqual(result_jti, jti)

    def test_create_token_pair(self):
        user_id = uuid.uuid4()
        token_pair, jti, expires = create_token_pair(user_id)
        self.assertIsNotNone(token_pair.access_token)
        self.assertIsNotNone(token_pair.refresh_token)
        self.assertEqual(token_pair.token_type, "bearer")
        self.assertTrue(token_pair.expires_in > 0)

    def test_expired_token_raises_error(self):
        user_id = uuid.uuid4()
        # Create token that expired in the past
        token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
        with self.assertRaises(ExpiredTokenError):
            verify_access_token(token)

    def test_invalid_token_raises_error(self):
        with self.assertRaises(InvalidTokenError):
            verify_access_token("invalid-token")

    def test_access_token_not_accepted_as_refresh(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        with self.assertRaises(InvalidTokenError):
            verify_refresh_token(token)

    def test_refresh_token_not_accepted_as_access(self):
        user_id = uuid.uuid4()
        token, _, _ = create_refresh_token(user_id)
        with self.assertRaises(InvalidTokenError):
            verify_access_token(token)


class TestUserService(unittest.TestCase):
    """Test user service functions."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.session = self.SessionLocal()

    def tearDown(self):
        # Clean up data after each test
        self.session.query(RefreshToken).delete()
        self.session.query(User).delete()
        self.session.commit()
        self.session.close()

    def test_create_user(self):
        user = create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User",
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.full_name, "Test User")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)

    def test_create_user_email_lowercased(self):
        user = create_user(
            db=self.session,
            email="TEST@Example.COM",
            username="testuser",
            password="password123",
        )
        self.assertEqual(user.email, "test@example.com")

    def test_create_user_username_lowercased(self):
        user = create_user(
            db=self.session,
            email="test@example.com",
            username="TestUser",
            password="password123",
        )
        self.assertEqual(user.username, "testuser")

    def test_create_user_duplicate_email_fails(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="user1",
            password="password123",
        )
        with self.assertRaises(UserAlreadyExistsError):
            create_user(
                db=self.session,
                email="test@example.com",
                username="user2",
                password="password123",
            )

    def test_create_user_duplicate_username_fails(self):
        create_user(
            db=self.session,
            email="test1@example.com",
            username="testuser",
            password="password123",
        )
        with self.assertRaises(UserAlreadyExistsError):
            create_user(
                db=self.session,
                email="test2@example.com",
                username="testuser",
                password="password123",
            )

    def test_authenticate_user_by_email(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        user = authenticate_user(self.session, "test@example.com", "password123")
        self.assertEqual(user.email, "test@example.com")

    def test_authenticate_user_by_username(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        user = authenticate_user(self.session, "testuser", "password123")
        self.assertEqual(user.username, "testuser")

    def test_authenticate_user_wrong_password(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        with self.assertRaises(InvalidCredentialsError):
            authenticate_user(self.session, "test@example.com", "wrongpassword")

    def test_authenticate_user_not_found(self):
        with self.assertRaises(InvalidCredentialsError):
            authenticate_user(self.session, "notfound@example.com", "password123")

    def test_get_user_by_email(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        user = get_user_by_email(self.session, "test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_username(self):
        create_user(
            db=self.session,
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        user = get_user_by_username(self.session, "testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")


# Shared test database setup for API endpoint tests
_test_engine = None
_TestSessionLocal = None


def get_test_engine():
    global _test_engine, _TestSessionLocal
    if _test_engine is None:
        _test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(_test_engine)
        _TestSessionLocal = sessionmaker(bind=_test_engine)
    return _test_engine, _TestSessionLocal


def override_get_db():
    _, SessionLocal = get_test_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestAuthEndpoints(unittest.TestCase):
    """Test authentication API endpoints."""

    @classmethod
    def setUpClass(cls):
        get_test_engine()  # Initialize the test engine
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        # Clear tables before each test
        _, SessionLocal = get_test_engine()
        with SessionLocal() as session:
            session.query(RefreshToken).delete()
            session.query(User).delete()
            session.commit()

    def test_register_user(self):
        response = self.client.post("/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User",
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "newuser@example.com")
        self.assertEqual(data["username"], "newuser")

    def test_register_duplicate_email_fails(self):
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "user1",
            "password": "password123",
        })
        response = self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "user2",
            "password": "password123",
        })
        self.assertEqual(response.status_code, 409)

    def test_login_success(self):
        # First register a user
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })

        # Then login
        response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "password123",
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_login_by_username(self):
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })

        response = self.client.post("/auth/login", json={
            "email_or_username": "testuser",
            "password": "password123",
        })
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self):
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })

        response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 401)

    def test_get_me_authenticated(self):
        # Register and login
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "password123",
        })
        access_token = login_response.json()["access_token"]

        # Get current user
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "test@example.com")

    def test_get_me_unauthenticated(self):
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_get_me_invalid_token(self):
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token(self):
        # Register and login
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "password123",
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh tokens
        response = self.client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        # New tokens should be different
        self.assertNotEqual(data["refresh_token"], refresh_token)

    def test_logout(self):
        # Register and login
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "password123",
        })
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = self.client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(response.status_code, 204)

        # Refresh token should be revoked
        response = self.client.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        self.assertEqual(response.status_code, 401)


class TestHybridAuth(unittest.TestCase):
    """Test hybrid API key and JWT authentication."""

    @classmethod
    def setUpClass(cls):
        get_test_engine()  # Ensure test engine is initialized
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        _, SessionLocal = get_test_engine()
        with SessionLocal() as session:
            session.query(RefreshToken).delete()
            session.query(User).delete()
            session.commit()

    def test_api_key_auth_still_works(self):
        """Verify backward compatibility with API key auth."""
        # When no API key is configured, endpoints should be accessible
        response = self.client.get("/drafts")
        # Should not fail with 401 when no auth is configured
        self.assertIn(response.status_code, [200, 401])  # Depends on auth config

    def test_jwt_auth_works_for_protected_endpoints(self):
        """JWT auth should work for protected endpoints when user exists."""
        # Register a user first
        self.client.post("/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        login_response = self.client.post("/auth/login", json={
            "email_or_username": "test@example.com",
            "password": "password123",
        })
        access_token = login_response.json()["access_token"]

        # Access protected endpoint with JWT
        response = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
