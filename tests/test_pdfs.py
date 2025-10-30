import os
import sys
# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import aiohttp
import httpx
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import PdfTransferRequest

client = TestClient(app)


def test_pdf_transfer_invalid_url_format():
    """测试无效的URL格式"""
    response = client.post(
        "/pdfs/transfer",
        json={"url": "invalid-url", "bucket": "test-bucket"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "无效的URL格式"}


def test_pdf_transfer_empty_url():
    """测试空URL"""
    response = client.post(
        "/pdfs/transfer",
        json={"url": "", "bucket": "test-bucket"}
    )
    assert response.status_code == 400  # 无效的URL格式


@patch("aiohttp.ClientSession.get")
@patch("app.routers.pdfs.upload_bytes")
def test_pdf_transfer_success(mock_upload_bytes, mock_get):
    """测试成功转存PDF文件"""
    # Mock aiohttp response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_response.read = AsyncMock(return_value=b"%PDF-1.4...fake pdf content")
    mock_get.return_value.__aenter__.return_value = mock_response

    # Mock upload_bytes function
    mock_upload_bytes.return_value = (
        "test-bucket",
        "test-key.pdf",
        "https://example.com/test-key.pdf"
    )

    # 测试API
    url = "https://example.com/test.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url, "bucket": "test-bucket"}
    )

    assert response.status_code == 201
    assert "bucket" in response.json()
    assert "key" in response.json()
    assert "url" in response.json()
    assert response.json()["bucket"] == "test-bucket"

    # 验证aiohttp调用
    mock_get.assert_called_once_with(url, timeout=30)

    # 验证upload_bytes调用
    mock_upload_bytes.assert_called_once()
    args, kwargs = mock_upload_bytes.call_args
    assert args[0] == b"%PDF-1.4...fake pdf content"
    assert kwargs["original_filename"] == "test.pdf"
    assert kwargs["bucket_name"] == "test-bucket"


@patch("aiohttp.ClientSession.get")
def test_pdf_transfer_download_failed(mock_get):
    """测试无法下载文件"""
    # Mock aiohttp response with error status
    mock_response = Mock()
    mock_response.status = 404
    mock_response.read = AsyncMock(return_value=b"%PDF-1.4...")
    mock_get.return_value.__aenter__.return_value = mock_response

    # 测试API
    url = "https://example.com/not-found.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": f"无法下载文件，HTTP状态码: 404"}


@patch("aiohttp.ClientSession.get")
def test_pdf_transfer_non_pdf_content(mock_get):
    """测试非PDF内容"""
    # Mock aiohttp response with non-PDF content type
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "text/plain"}
    mock_response.read = AsyncMock(return_value=b"not a pdf")
    mock_get.return_value.__aenter__.return_value = mock_response

    # 测试API
    url = "https://example.com/not-pdf.txt"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "文件内容不是PDF格式"}


@patch("aiohttp.ClientSession.get")
def test_pdf_transfer_empty_content(mock_get):
    """测试空内容"""
    # Mock aiohttp response with empty content
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_response.read = AsyncMock(return_value=b"")
    mock_get.return_value.__aenter__.return_value = mock_response

    # 测试API
    url = "https://example.com/empty.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "下载的文件为空"}


@patch("aiohttp.ClientSession.get")
def test_pdf_transfer_client_error(mock_get):
    """测试网络连接错误"""
    # Mock aiohttp ClientError
    mock_get.side_effect = aiohttp.ClientError("Connection error")

    # 测试API
    url = "https://example.com/test.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": f"下载文件失败: Connection error"}


@patch("aiohttp.ClientSession.get")
@patch("app.routers.pdfs.upload_bytes")
def test_pdf_transfer_without_bucket(mock_upload_bytes, mock_get):
    """测试不指定bucket参数"""
    # Mock aiohttp response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_response.read = AsyncMock(return_value=b"%PDF-1.4...fake pdf content")
    mock_get.return_value.__aenter__.return_value = mock_response

    # Mock upload_bytes function with default bucket
    mock_upload_bytes.return_value = (
        "default-bucket",
        "test-key.pdf",
        "https://example.com/test-key.pdf"
    )

    # 测试API
    url = "https://example.com/test.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 201
    assert response.json()["bucket"] == "default-bucket"
    # 验证upload_bytes调用（使用默认bucket）
    mock_upload_bytes.assert_called_once()
    args, kwargs = mock_upload_bytes.call_args
    assert kwargs["bucket_name"] is None  # 没有传递bucket参数


@patch("aiohttp.ClientSession.get")
@patch("app.routers.pdfs.upload_bytes")
def test_pdf_transfer_oss_upload_failed(mock_upload_bytes, mock_get):
    """测试OSS上传失败"""
    # Mock aiohttp response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_response.read = AsyncMock(return_value=b"%PDF-1.4...fake pdf content")
    mock_get.return_value.__aenter__.return_value = mock_response

    # Mock upload_bytes function with error
    mock_upload_bytes.side_effect = Exception("OSS upload failed")
    # 确保mock被正确设置
    mock_upload_bytes.assert_not_called()

    # 测试API
    url = "https://example.com/test.pdf"
    response = client.post(
        "/pdfs/transfer",
        json={"url": url}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "上传文件失败: OSS upload failed"}


if __name__ == "__main__":
    pytest.main(["-v", "test_pdfs.py"])