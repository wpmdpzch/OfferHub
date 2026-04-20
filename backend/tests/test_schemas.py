"""Backend API Schema 验证测试"""
import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.schemas_user import UserRegister, UserLogin, UserUpdate
from app.services.schemas_article import ArticleCreate, ArticleUpdate
from app.services.schemas_comment import CommentCreate


class TestUserSchemas:
    def test_user_register_valid(self):
        data = UserRegister(username="testuser", email="test@example.com", password="password123")
        assert data.username == "testuser"
        assert data.email == "test@example.com"

    def test_user_register_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegister(username="test", email="not-an-email", password="password123")

    def test_user_register_short_password(self):
        with pytest.raises(ValidationError):
            UserRegister(username="test", email="test@example.com", password="12345")

    def test_user_login_valid(self):
        data = UserLogin(email="test@example.com", password="password123")
        assert data.email == "test@example.com"

    def test_user_register_missing_fields(self):
        with pytest.raises(ValidationError):
            UserRegister(username="test")  # missing email and password


class TestArticleSchemas:
    def test_article_create_valid(self):
        data = ArticleCreate(
            title="字节跳动前端面经",
            content="## 一面\n- 手写 Promise\n- 事件循环",
            category="面经分享",
        )
        assert data.title == "字节跳动前端面经"
        assert data.category == "面经分享"

    def test_article_create_minimal(self):
        data = ArticleCreate(title="Test", content="Test content")
        assert data.title == "Test"

    def test_article_update_partial(self):
        data = ArticleUpdate(title="Updated Title")
        assert data.title == "Updated Title"

    def test_article_update_empty(self):
        data = ArticleUpdate()
        assert data.title is None

    def test_article_create_with_tags(self):
        data = ArticleCreate(
            title="Test",
            content="Content",
            tag_names=["前端", "字节"],
        )
        assert data.tag_names == ["前端", "字节"]


class TestCommentSchemas:
    def test_comment_create_valid(self):
        data = CommentCreate(content="这是一条评论")
        assert data.content == "这是一条评论"

    def test_comment_create_with_parent(self):
        import uuid
        parent = uuid.uuid4()
        data = CommentCreate(content="Reply", parent_id=parent)
        assert data.parent_id == parent

    def test_comment_create_missing_content(self):
        with pytest.raises(ValidationError):
            CommentCreate()
