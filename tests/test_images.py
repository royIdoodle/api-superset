import os
import sys
from unittest.mock import patch, MagicMock
from io import BytesIO
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.config import get_settings

client = TestClient(app)

def test_upload_image_no_bucket_no_default(monkeypatch):
    """测试：未提供bucket且未配置默认bucket时，返回400错误"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = ""
        settings.OSS_BUCKETS = None
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 测试上传
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", BytesIO(b"test content"), "image/png")}
    )
    
    # 验证结果
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "未提供 bucket 且未配置默认 bucket"

def test_upload_image_invalid_bucket_no_default(monkeypatch):
    """测试：提供的bucket不在允许列表中且未配置默认bucket时，返回400错误"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = ""
        settings.OSS_BUCKETS = ["allowed-bucket"]
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 测试上传
    response = client.post(
        "/images/upload",
        files={"file": ("test.png", BytesIO(b"test content"), "image/png")},
        data={"bucket": "invalid-bucket"}
    )
    
    # 验证结果
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "不支持的 bucket: invalid-bucket"

def test_upload_image_invalid_bucket_with_default(monkeypatch):
    """测试：提供的bucket不在允许列表中但配置了默认bucket时，使用默认bucket"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = "default-bucket"
        settings.OSS_BUCKETS = ["allowed-bucket"]
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 模拟tinify_enabled返回False
    monkeypatch.setattr("app.routers.images.tinify_enabled", lambda: False)
    
    # 模拟OSS上传
    with patch("app.oss.upload_bytes") as mock_upload:
        mock_upload.return_value = ("default-bucket", "test-key", "http://example.com/test.png")
        
        # 测试上传
        response = client.post(
            "/images/upload",
            files={"file": ("test.png", BytesIO(b"test content"), "image/png")},
            data={"bucket": "invalid-bucket"}
        )
        
        # 验证结果
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["bucket"] == "default-bucket"
        
        # 验证上传函数被正确调用
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs["bucket_name"] == "default-bucket"

def test_upload_image_valid_bucket(monkeypatch):
    """测试：提供的bucket在允许列表中时，使用提供的bucket"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = "default-bucket"
        settings.OSS_BUCKETS = ["allowed-bucket", "another-bucket"]
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 模拟tinify_enabled返回False
    monkeypatch.setattr("app.routers.images.tinify_enabled", lambda: False)
    
    # 模拟OSS上传
    with patch("app.oss.upload_bytes") as mock_upload:
        mock_upload.return_value = ("allowed-bucket", "test-key", "http://example.com/test.png")
        
        # 测试上传
        response = client.post(
            "/images/upload",
            files={"file": ("test.png", BytesIO(b"test content"), "image/png")},
            data={"bucket": "allowed-bucket"}
        )
        
        # 验证结果
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["bucket"] == "allowed-bucket"
        
        # 验证上传函数被正确调用
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs["bucket_name"] == "allowed-bucket"

def test_upload_image_oss_error(monkeypatch):
    """测试：OSS上传失败时，返回400错误并包含清晰的错误信息"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = "default-bucket"
        settings.OSS_BUCKETS = None
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 模拟tinify_enabled返回False
    monkeypatch.setattr("app.routers.images.tinify_enabled", lambda: False)
    
    # 模拟OSS上传失败
    with patch("app.oss.upload_bytes") as mock_upload:
        mock_upload.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OSS上传失败: 访问被拒绝 (错误码: AccessDenied)"
        )
        
        # 测试上传
        response = client.post(
            "/images/upload",
            files={"file": ("test.png", BytesIO(b"test content"), "image/png")}
        )
        
        # 验证结果
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "OSS上传失败: 访问被拒绝 (错误码: AccessDenied)"

def test_upload_image_no_bucket_with_default(monkeypatch):
    """测试：未提供bucket但配置了默认bucket时，使用默认bucket"""
    # 定义模拟的get_settings函数
    def mock_get_settings():
        settings = MagicMock()
        settings.DEFAULT_OSS_BUCKET = "default-bucket"
        settings.OSS_BUCKETS = None
        settings.OSS_ACCESS_KEY_ID = "test-key"
        settings.OSS_ACCESS_KEY_SECRET = "test-secret"
        settings.OSS_ENDPOINT = "http://oss.example.com"
        return settings
    
    # 模拟get_settings函数
    monkeypatch.setattr("app.routers.images.get_settings", mock_get_settings)
    monkeypatch.setattr("app.oss.get_settings", mock_get_settings)
    
    # 模拟tinify_enabled返回False
    monkeypatch.setattr("app.routers.images.tinify_enabled", lambda: False)
    
    # 模拟OSS上传
    with patch("app.oss.upload_bytes") as mock_upload:
        mock_upload.return_value = ("default-bucket", "test-key", "http://example.com/test.png")
        
        # 测试上传
        response = client.post(
            "/images/upload",
            files={"file": ("test.png", BytesIO(b"test content"), "image/png")}
        )
        
        # 验证结果
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["bucket"] == "default-bucket"
        
        # 验证上传函数被正确调用
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs["bucket_name"] == "default-bucket"

if __name__ == "__main__":
    # 运行所有测试
    test_upload_image_no_bucket_no_default()
    print("✓ test_upload_image_no_bucket_no_default passed")
    
    test_upload_image_invalid_bucket_no_default()
    print("✓ test_upload_image_invalid_bucket_no_default passed")
    
    test_upload_image_invalid_bucket_with_default()
    print("✓ test_upload_image_invalid_bucket_with_default passed")
    
    test_upload_image_valid_bucket()
    print("✓ test_upload_image_valid_bucket passed")
    
    test_upload_image_oss_error()
    print("✓ test_upload_image_oss_error passed")
    
    test_upload_image_no_bucket_with_default()
    print("✓ test_upload_image_no_bucket_with_default passed")
    
    print("All tests passed!")