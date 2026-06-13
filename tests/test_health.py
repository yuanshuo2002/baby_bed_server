"""
健康检查测试
测试 /api/v1/health 端点
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthCheck:
    """健康检查测试类"""

    def test_root_health_check(self):
        """测试根路径健康检查"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Baby Bed Server is running" in data["message"]

    def test_api_v1_health_check(self):
        """测试API v1健康检查端点"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Baby Bed Server is running" in data["message"]

    def test_docs_available(self):
        """测试Swagger文档可访问"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        """测试ReDoc文档可访问"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        """测试OpenAPI Schema可访问"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Baby Bed Server"
        assert "/api/v1/health" in data["paths"]
