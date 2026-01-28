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
        # Use in-memory DB for testing (fast & safe)
        self.db = DatabaseManager(db_path=":memory:")
    
    def test_add_and_get_history(self):
        self.db.add_history("Hello", "Merhaba", "Academic")
        history = self.db.get_history(limit=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['original_text'], "Hello")
        self.assertEqual(history[0]['translated_text'], "Merhaba")

    def test_cache_hit(self):
        self.db.add_history("Cache Me", "Önbellek", "Academic")
        result = self.db.get_translation("Cache Me", "Academic")
        self.assertIsNotNone(result)
        self.assertEqual(result['translation'], "Önbellek")

    def test_dictionary_operations(self):
        self.db.add_term("TestTerm", "TestTanım")
        terms = self.db.get_all_terms()
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0]['term'], "TestTerm")
        
        self.db.delete_term(terms[0]['id'])
        self.assertEqual(len(self.db.get_all_terms()), 0)

class TestAPIService(unittest.TestCase):
    def setUp(self):
        # Mock API Key to bypass check
        with patch.dict(os.environ, {"GEMINI_API_KEY": "FAKE_KEY"}):
            self.api = APIService()

    def test_translate_text_success(self):
        # Mock the client explicitly since it was created in setUp
        self.api.client = MagicMock()
        
        # Mock the Gemini API response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "translation": "Deneme",
            "terms": ["Terim1"]
        })
        
        # Setup the mock chain
        self.api.client.models.generate_content.return_value = mock_response
        
        result = self.api.translate_text("Test")
        
        self.assertEqual(result['translation'], "Deneme")
        self.assertIn("Terim1", result['terms'])

    def test_translate_empty_text(self):
        result = self.api.translate_text("")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
