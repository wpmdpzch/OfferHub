"""Config Environment Variable Tests"""
import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestConfigEnvVars:
    def test_database_url_format(self):
        from app.core.config import Settings

        settings = Settings(
            JWT_SECRET_KEY="test-key",
            POSTGRES_PASSWORD="test_password",
            postgres_host="localhost",
            postgres_db="testdb",
        )
        url = settings.database_url
        assert "postgresql+asyncpg://" in url
        assert "test_password" in url
        assert "localhost" in url
        assert "testdb" in url

    def test_redis_url_format(self):
        from app.core.config import Settings

        settings = Settings(
            JWT_SECRET_KEY="test-key",
            POSTGRES_PASSWORD="test",
            redis_host="redis-host",
            redis_port=6380,
            redis_db=2,
        )
        url = settings.redis_url
        assert "redis://" in url
        assert "redis-host" in url
        assert "6380" in url
