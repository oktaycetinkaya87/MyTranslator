import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from core.api_service import APIService

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # DatabaseManager expects db_name, not db_path
        self.test_db_name = "test_suite.db"
        self.db = DatabaseManager(db_name=self.test_db_name)
    
    def tearDown(self):
        # Cleanup test DB
        if os.path.exists(self.db.db_path):
            os.remove(self.db.db_path)

    def test_add_and_get_history(self):
        self.db.add_history("Hello", "Merhaba", "Academic")
        history = self.db.get_last_history(limit=1) # get_history -> get_last_history
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['original_text'], "Hello")
        self.assertEqual(history[0]['translation'], "Merhaba") # translated_text -> translation

    def test_cache_hit(self):
        self.db.add_history("Cache Me", "Önbellek", "Academic")
        result = self.db.get_translation("Cache Me", "Academic")
        self.assertIsNotNone(result)
        self.assertEqual(result['translation'], "Önbellek")

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

if __name__ == '__main__':
    unittest.main()
