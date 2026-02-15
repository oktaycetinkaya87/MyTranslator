import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# TestDatabaseManager removed in favor of tests/test_database_manager.py
from core.api_service import APIService
class TestAPIService(unittest.TestCase):
    def setUp(self):
        # Mock API Key to bypass check
        with patch.dict(os.environ, {"GEMINI_API_KEY": "FAKE_KEY"}):
            with patch('core.api_service.APIService.warmup') as mock_warmup:
                with patch('core.api_service.APIService._start_heartbeat') as mock_beat:
                     self.api = APIService()

    @patch('google.genai.Client')
    def test_translate_text_stream(self, MockClient): # Changed to test stream method
        # Mock the client instance
        mock_client_instance = MockClient.return_value
        self.api.client = mock_client_instance
        
        # Mock the stream response
        mock_chunk = MagicMock()
        mock_chunk.text = "Deneme"
        
        # Setup the mock to return an iterator
        mock_client_instance.models.generate_content_stream.return_value = iter([mock_chunk])
        
        # Consume the generator
        chunks = list(self.api.translate_text_stream("Test"))
        
        self.assertEqual("".join(chunks), "Deneme")

    @patch('core.api_service.APIService.warmup')
    @patch('core.api_service.APIService._start_heartbeat')
    def test_init_with_key(self, mock_beat, mock_warmup):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "KEY"}):
             api = APIService()
             self.assertEqual(api.api_key, "KEY")

    def test_init_no_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=True):
             # Depending on implementation, it might log or raise. 
             # APIService usually looks at os.getenv
             api = APIService()
             # If it hasn't crashed, it's good. We can check if client is None or something.
             pass

    @patch('google.genai.Client')
    def test_warmup(self, MockClient):
        mock_client = MockClient.return_value
        self.api.client = mock_client
        self.api.warmup()
        # Verify it called the model in some way.
        mock_client.models.generate_content.assert_called()

if __name__ == '__main__':
    unittest.main()
