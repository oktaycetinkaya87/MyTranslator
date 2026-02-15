import os
import sys
import time
from locust import User, task, between, events
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from core.api_service import APIService

class TranslatorUser(User):
    wait_time = between(1, 3) # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize resources for each simulated user"""
        self.db = DatabaseManager()
        # Mock APIService to avoid real network calls/costs
        self.api = APIService()
        self.api.client = MagicMock()
        
        # Mock the stream response
        mock_chunk = MagicMock()
        mock_chunk.text = "Mock Translated Text"
        self.api.client.models.generate_content_stream.return_value = iter([mock_chunk])

    @task(3)
    def read_history(self):
        """Simulate frequent reading from history"""
        start_time = time.time()
        try:
            history = self.db.get_last_history(limit=20)
            # Iterate to ensure data is fetched
            _ = list(history)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="DB_READ",
                name="get_last_history",
                response_time=total_time,
                response_length=len(history),
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="DB_READ",
                name="get_last_history",
                response_time=total_time,
                exception=e,
            )

    @task(1)
    def write_history(self):
        """Simulate adding new translations"""
        start_time = time.time()
        try:
            self.db.add_history("Perf Test Source", "Perf Test Translation")
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="DB_WRITE",
                name="add_history",
                response_time=total_time,
                response_length=0,
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="DB_WRITE",
                name="add_history",
                response_time=total_time,
                exception=e,
            )

    @task(2)
    def process_api_request(self):
        """Simulate API processing logic (Mocked Network)"""
        start_time = time.time()
        try:
            # This tests the generator logic and internal handling of APIService
            chunks = list(self.api.translate_text_stream("Hello World"))
            
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="API_PROC",
                name="translate_text_stream",
                response_time=total_time,
                response_length=len(chunks),
            )
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="API_PROC",
                name="translate_text_stream",
                response_time=total_time,
                exception=e,
            )
