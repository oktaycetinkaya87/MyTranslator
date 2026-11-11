import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import threading
from core.api_service import APIService
from core.prompts import REFINE_SYSTEM_PROMPT

class TestAPIServiceAdvanced(unittest.TestCase):

    @patch('core.api_service.load_dotenv')
    @patch('os.getenv')
    def test_init_no_api_key(self, mock_getenv, mock_load):
        # Simulate missing API key
        mock_getenv.return_value = None
        with patch('logging.error') as mock_log:
            service = APIService()
            self.assertIsNone(service.api_key)
            mock_log.assert_called_with("❌ API Key missing!")

    @patch('core.api_service.APIService.warmup')
    @patch('google.genai.Client')
    def test_init_success(self, MockClient, mock_warmup):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            service = APIService()
            self.assertEqual(service.api_key, "fake_key")
            MockClient.assert_called_once()
            mock_warmup.assert_called_once()

    @patch('google.genai.Client')
    def test_warmup_exception(self, MockClient):
        # We need to test the inner task logic
        mock_client_instance = MockClient.return_value
        mock_client_instance.models.generate_content.side_effect = Exception("Warmup Fail")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('logging.warning') as mock_log:
                service = APIService()
                # Warmup runs in a thread, so we might need a small sleep or join
                # In our case, we just want to ensure it doesn't crash the main init
                # and hits the log.
                import time
                time.sleep(0.5) 
                mock_log.assert_called_with(ANY) 

    @patch('google.genai.Client')
    def test_translate_text_stream_error(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_client_instance.models.generate_content_stream.side_effect = Exception("Stream Error")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.translate_text_stream("Hello"))
                self.assertIn("[Hata: Stream Error]", chunks[0])

    @patch('google.genai.Client')
    def test_refine_text_stream_error(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_client_instance.models.generate_content_stream.side_effect = Exception("Refine Error")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.refine_text_stream("source", "current"))
                self.assertIn("[Error: Refine Error]", chunks[0])

    def test_refine_text_stream_empty(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.refine_text_stream("", ""))
                self.assertEqual(len(chunks), 0)

    @patch('google.genai.Client')
    def test_refine_text_stream_success(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_chunk = MagicMock()
        mock_chunk.text = "Refined"
        mock_client_instance.models.generate_content_stream.return_value = iter([mock_chunk])
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.refine_text_stream("source", "current"))
                self.assertEqual("".join(chunks), "Refined")

                kwargs = mock_client_instance.models.generate_content_stream.call_args.kwargs
                self.assertEqual(
                    kwargs["contents"],
                    "<source_text>\nsource\n</source_text>\n\n<current_text>\ncurrent\n</current_text>"
                )
                self.assertEqual(kwargs["config"].system_instruction, REFINE_SYSTEM_PROMPT)

    @patch('google.genai.Client')
    def test_refine_text_stream_without_source(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_chunk = MagicMock()
        mock_chunk.text = "Refined"
        mock_client_instance.models.generate_content_stream.return_value = iter([mock_chunk])

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.refine_text_stream("", "current"))
                self.assertEqual("".join(chunks), "Refined")

                kwargs = mock_client_instance.models.generate_content_stream.call_args.kwargs
                self.assertEqual(kwargs["contents"], "<current_text>\ncurrent\n</current_text>")

    @patch('google.genai.Client')
    def test_translate_image_stream_success(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_chunk = MagicMock()
        mock_chunk.text = "Extracted"
        mock_client_instance.models.generate_content_stream.return_value = iter([mock_chunk])
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.translate_image_stream(b"fake_image_bytes"))
                self.assertEqual("".join(chunks), "Extracted")

    @patch('google.genai.Client')
    def test_translate_image_stream_error(self, MockClient):
        mock_client_instance = MockClient.return_value
        mock_client_instance.models.generate_content_stream.side_effect = Exception("Image Error")
        
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.translate_image_stream(b"fake_image_bytes"))
                self.assertIn("[Hata: Image Error]", chunks[0])

    def test_translate_image_stream_empty(self):
         with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            with patch('core.api_service.APIService.warmup'):
                service = APIService()
                chunks = list(service.translate_image_stream(None))
                self.assertEqual(len(chunks), 0)

if __name__ == '__main__':
    unittest.main()
