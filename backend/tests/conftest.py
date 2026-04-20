"""Shared pytest fixtures"""
import pytest
import os

# Set required env vars for testing before importing app modules
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB", "offerhub_test")
os.environ.setdefault("POSTGRES_USER", "test_user")
