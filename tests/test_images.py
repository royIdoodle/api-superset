import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add the project root to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models import ImageAsset
from app.tinify_client import compress_and_resize

client = TestClient(app)


def test_upload_non_image_file():    
    # Mock the database dependency
    mock_db = MagicMock(spec=Session)
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    # Create a mock add method that sets the id and created_at values
    def mock_add_effect(record):
        record.id = 1
        record.created_at = datetime(2023, 1, 1, 0, 0, 0)
    
    mock_db.add.side_effect = mock_add_effect
    
    # Mock the OSS upload function to avoid actual API calls
    with patch('app.routers.images.upload_bytes') as mock_upload:
        mock_upload.return_value = ("test-bucket", "uploads/test.pdf", "http://example.com/uploads/test.pdf")
        
        # Mock the tinify compression function to check if it's called
        with patch('app.routers.images.compress_and_resize') as mock_compress:
            # Set up the mock to return the original data
            mock_compress.return_value = (b"test data", None, None, None)
            
            # Override the get_db dependency to use our mock
            def override_get_db():                
                yield mock_db
            
            app.dependency_overrides[get_db] = override_get_db
            
            try:
                # Upload a non-image file (PDF)
                response = client.post(
                    "/images/upload",
                    files={"file": ("document.pdf", b"%PDF-1.4...", "application/pdf")},
                    data={"tags": "document,test"}
                )
                
                # Check that the response is successful
                assert response.status_code == 201
                assert response.json()["original_filename"] == "document.pdf"
                assert response.json()["format"] == "bin"
                
                # Verify that compress_and_resize was NOT called for non-image file
                mock_compress.assert_not_called()
                
                # Verify that upload_bytes was called
                mock_upload.assert_called_once()
                
                # Verify that the database was updated
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()
                
            finally:
                # Restore the original dependency
                app.dependency_overrides.pop(get_db, None)


def test_upload_image_file():
    # Mock the database dependency
    mock_db = MagicMock(spec=Session)
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    # Create a mock add method that sets the id and created_at values
    def mock_add_effect(record):
        record.id = 2
        record.created_at = datetime(2023, 1, 1, 0, 0, 0)
    
    mock_db.add.side_effect = mock_add_effect
    
    # Mock the OSS upload function to avoid actual API calls
    with patch('app.routers.images.upload_bytes') as mock_upload:
        mock_upload.return_value = ("test-bucket", "uploads/test.jpg", "http://example.com/uploads/test.jpg")
        
        # Mock the tinify compression function to check if it's called
        with patch('app.routers.images.compress_and_resize') as mock_compress:
            # Set up the mock to return compressed data
            mock_compress.return_value = (b"compressed data", 100, 100, "jpg")
            
            # Override the get_db dependency to use our mock
            def override_get_db():                
                yield mock_db
            
            app.dependency_overrides[get_db] = override_get_db
            
            try:
                # Upload an image file (JPG)
                response = client.post(
                    "/images/upload",
                    files={"file": ("test.jpg", b"\xff\xd8\xff\xe0...", "image/jpeg")},
                    data={"tags": "image,test"}
                )
                
                # Check that the response is successful
                assert response.status_code == 201
                assert response.json()["original_filename"] == "test.jpg"
                assert response.json()["format"] == "jpg"
                assert response.json()["width"] == 100
                assert response.json()["height"] == 100
                
                # Verify that compress_and_resize was called for image file
                mock_compress.assert_called_once()
                
                # Verify that upload_bytes was called with compressed data
                mock_upload.assert_called_once_with(
                    b"compressed data",
                    original_filename="test.jpg",
                    bucket_name=None,
                    key=mock_upload.call_args.kwargs["key"],
                    content_type="image/jpeg"
                )
                
                # Verify that the database was updated
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()
                
            finally:
                # Restore the original dependency
                app.dependency_overrides.pop(get_db, None)


def test_upload_image_with_resize_and_format_conversion():
    # Mock the database dependency
    mock_db = MagicMock(spec=Session)
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    # Create a mock add method that sets the id and created_at values
    def mock_add_effect(record):
        record.id = 3
        record.created_at = datetime(2023, 1, 1, 0, 0, 0)
    
    mock_db.add.side_effect = mock_add_effect
    
    # Mock the OSS upload function to avoid actual API calls
    with patch('app.routers.images.upload_bytes') as mock_upload:
        mock_upload.return_value = ("test-bucket", "uploads/test.webp", "http://example.com/uploads/test.webp")
        
        # Mock the tinify compression function to check if it's called with correct parameters
        with patch('app.routers.images.compress_and_resize') as mock_compress:
            # Set up the mock to return compressed and converted data
            mock_compress.return_value = (b"compressed webp data", 200, 150, "webp")
            
            # Override the get_db dependency to use our mock
            def override_get_db():                
                yield mock_db
            
            app.dependency_overrides[get_db] = override_get_db
            
            try:
                # Upload an image file with resize and format conversion
                response = client.post(
                    "/images/upload",
                    files={"file": ("test.png", b"\x89PNG...", "image/png")},
                    data={
                        "tags": "image,test,converted",
                        "width": 200,
                        "height": 150,
                        "target_format": "webp"
                    }
                )
                
                # Check that the response is successful
                assert response.status_code == 201
                assert response.json()["original_filename"] == "test.png"
                assert response.json()["format"] == "webp"
                assert response.json()["width"] == 200
                assert response.json()["height"] == 150
                
                # Verify that compress_and_resize was called with correct parameters
                mock_compress.assert_called_once_with(
                    b"\x89PNG...",
                    target_width=200,
                    target_height=150,
                    target_format="webp"
                )
                
                # Verify that upload_bytes was called with the correct content type
                mock_upload.assert_called_once()
                assert mock_upload.call_args.kwargs["content_type"] == "image/webp"
                
            finally:
                # Restore the original dependency
                app.dependency_overrides.pop(get_db, None)
