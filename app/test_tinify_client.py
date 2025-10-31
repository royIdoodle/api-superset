import unittest
from unittest.mock import patch, MagicMock
from typing import Optional, Tuple

from app.tinify_client import compress_and_resize, is_enabled
from app.config import get_settings


class TestTinifyClient(unittest.TestCase):
    def setUp(self):
        # Save original settings
        self.original_api_key = get_settings().TINIFY_API_KEY
        
    def tearDown(self):
        # Restore original settings
        get_settings().TINIFY_API_KEY = self.original_api_key
        
    def test_is_enabled(self):
        # Test when API key is set
        get_settings().TINIFY_API_KEY = "test_key"
        self.assertTrue(is_enabled())
        
        # Test when API key is not set
        get_settings().TINIFY_API_KEY = None
        self.assertFalse(is_enabled())
        
    @patch('app.tinify_client.tinify')
    def test_compress_and_resize_with_conversion(self, mock_tinify):
        # Enable tinify
        get_settings().TINIFY_API_KEY = "test_key"
        
        # Mock the source object
        mock_source = MagicMock()
        mock_result = MagicMock()
        mock_result.to_buffer.return_value = b"compressed data"
        mock_result.width = 100
        mock_result.height = 100
        mock_source.result.return_value = mock_result
        mock_source.resize.return_value = mock_source
        mock_source.convert.return_value = mock_source
        mock_tinify.from_buffer.return_value = mock_source
        
        # Test data
        input_data = b"original data"
        
        # Call the function
        result = compress_and_resize(
            input_data,
            target_width=100,
            target_height=100,
            target_format="png"
        )
        
        # Verify the result
        self.assertEqual(result[0], b"compressed data")
        self.assertEqual(result[1], 100)
        self.assertEqual(result[2], 100)
        self.assertEqual(result[3], "png")
        
        # Verify the calls
        mock_tinify.from_buffer.assert_called_once_with(input_data)
        mock_source.resize.assert_called_once_with(method="fit", width=100, height=100)
        mock_source.convert.assert_called_once_with(type="image/png")
        mock_source.result.assert_called_once()
        mock_result.to_buffer.assert_called_once()
        
    @patch('app.tinify_client.tinify')
    def test_compress_and_resize_without_conversion(self, mock_tinify):
        # Enable tinify
        get_settings().TINIFY_API_KEY = "test_key"
        
        # Mock the source object
        mock_source = MagicMock()
        mock_result = MagicMock()
        mock_result.to_buffer.return_value = b"compressed data"
        mock_result.width = 200
        mock_result.height = 200
        mock_source.result.return_value = mock_result
        mock_source.resize.return_value = mock_source
        mock_tinify.from_buffer.return_value = mock_source
        
        # Test data
        input_data = b"original data"
        
        # Call the function without target_format
        result = compress_and_resize(
            input_data,
            target_width=200,
            target_height=200
        )
        
        # Verify the result
        self.assertEqual(result[0], b"compressed data")
        self.assertEqual(result[1], 200)
        self.assertEqual(result[2], 200)
        self.assertEqual(result[3], None)
        
        # Verify the calls - convert should not be called
        mock_tinify.from_buffer.assert_called_once_with(input_data)
        mock_source.resize.assert_called_once_with(method="fit", width=200, height=200)
        mock_source.convert.assert_not_called()
        mock_source.result.assert_called_once()
        mock_result.to_buffer.assert_called_once()
        
    @patch('app.tinify_client.tinify')
    def test_compress_and_resize_non_image(self, mock_tinify):
        # Enable tinify
        get_settings().TINIFY_API_KEY = "test_key"
        
        # Import ClientError here to avoid circular imports
        from tinify.errors import ClientError
        
        # Mock to raise ClientError for non-image file
        mock_tinify.from_buffer.side_effect = ClientError("Not an image", "not_image", 400)
        
        # Test data - non-image content
        input_data = b"not an image file"
        
        # Call the function
        result = compress_and_resize(
            input_data,
            target_width=100,
            target_height=100,
            target_format="png"
        )
        
        # Verify the result - should return original data
        self.assertEqual(result[0], input_data)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)
        self.assertEqual(result[3], None)
        
    def test_compress_and_resize_tinify_disabled(self):
        # Disable tinify
        get_settings().TINIFY_API_KEY = None
        
        # Test data
        input_data = b"original data"
        
        # Call the function
        result = compress_and_resize(
            input_data,
            target_width=100,
            target_height=100,
            target_format="png"
        )
        
        # Verify the result - should return original data
        self.assertEqual(result[0], input_data)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)
        self.assertEqual(result[3], None)


if __name__ == '__main__':
    unittest.main()
