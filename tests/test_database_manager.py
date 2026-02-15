import unittest
from unittest.mock import patch, MagicMock, ANY
from database.db_manager import DatabaseManager
import sqlite3
import os

class TestDatabaseManager(unittest.TestCase):
    
    @patch('sqlite3.connect')
    def test_init_creates_tables(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager(db_name="translations.db")
        
        # Verify connection to correct DB file
        args, _ = mock_connect.call_args
        self.assertTrue(args[0].endswith("translations.db"))
        
        # Verify table creation queries
        calls = [args[0] for args, _ in mock_cursor.execute.call_args_list]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS history" in call for call in calls))
        self.assertTrue(any("original_text TEXT NOT NULL" in call for call in calls))

    @patch('sqlite3.connect')
    def test_get_translation_hit(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock cursor.fetchone to return a dict-like object
        mock_row = MagicMock()
        data = {"original_text": "Hello", "translation": "Translated Text"}
        mock_row.keys.return_value = list(data.keys())
        mock_row.__iter__ = lambda x: iter(data.items())
        mock_row.__getitem__.side_effect = data.__getitem__
        
        mock_cursor.fetchone.return_value = mock_row
        
        db = DatabaseManager()
        result = db.get_translation("Hello")
        
        self.assertEqual(result, {"original_text": "Hello", "translation": "Translated Text"})
        mock_cursor.execute.assert_called_with('SELECT * FROM history WHERE original_text = ? ORDER BY timestamp DESC LIMIT 1', ("Hello",))

    @patch('sqlite3.connect')
    def test_get_translation_miss(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        
        db = DatabaseManager()
        result = db.get_translation("Unknown")
        
        self.assertIsNone(result)
        
    def test_get_translation_empty_input(self):
        db = DatabaseManager()
        self.assertIsNone(db.get_translation(""))
        self.assertIsNone(db.get_translation(None))

    @patch('sqlite3.connect')
    def test_add_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        db.add_history("Source", "Target")
        
        mock_cursor.execute.assert_called_with(
            'INSERT INTO history (original_text, translation, style) VALUES (?, ?, ?)',
            ("Source", "Target", "Academic")
        )
        mock_conn.commit.assert_called()
        
    @patch('sqlite3.connect')
    def test_add_history_empty_input(self, mock_connect):
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        
        # Reset mocks to ignore init_db calls
        mock_cursor.execute.reset_mock()
        mock_connect.return_value.commit.reset_mock()
        
        db.add_history("", "Target")
        db.add_history("Source", "")
        
        # Verify no NEW executions happened
        mock_cursor.execute.assert_not_called()

    @patch('sqlite3.connect')
    def test_get_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        row1 = MagicMock()
        data1 = {"id": 1, "original_text": "S1", "translation": "T1", "style": "Academic"}
        row1.keys.return_value = list(data1.keys())
        row1.__iter__ = lambda x: iter(data1.items())
        row1.__getitem__.side_effect = data1.__getitem__
        
        mock_cursor.fetchall.return_value = [row1]
        
        db = DatabaseManager()
        history = db.get_history(limit=5)
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["original_text"], "S1")
        mock_cursor.execute.assert_called_with('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (5,))

    @patch('sqlite3.connect')
    def test_clear_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        db.clear_history()
        
        mock_cursor.execute.assert_called_with("DELETE FROM history")
        mock_conn.commit.assert_called()

    @patch('sqlite3.connect')
    def test_get_last_history(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        db = DatabaseManager()
        db.get_last_history(limit=10)
        mock_cursor.execute.assert_called_with('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (10,))

    @patch('sqlite3.connect')
    def test_get_setting_error(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        # Defer exception until after init
        mock_cursor.execute.side_effect = Exception("DB Error")
        
        val = db.get_setting("any", default="err")
        self.assertEqual(val, "err")

    @patch('sqlite3.connect')
    def test_set_setting_error(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        # Defer exception until after init
        mock_cursor.execute.side_effect = Exception("DB Error")
        
        # Should catch exception internally
        db.set_setting("key", "val")
        self.assertTrue(True) # Just ensure it didn't crash

    @patch('sqlite3.connect')
    def test_get_setting_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = {"value": "10"}.__getitem__
        mock_cursor.fetchone.return_value = mock_row
        
        db = DatabaseManager()
        val = db.get_setting("shake_sensitivity")
        self.assertEqual(val, "10")

    @patch('sqlite3.connect')
    def test_get_setting_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None
        
        db = DatabaseManager()
        val = db.get_setting("unknown_key", default="5")
        self.assertEqual(val, "5")

    @patch('sqlite3.connect')
    def test_set_setting(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        db = DatabaseManager()
        db.set_setting("theme", "dark")
        
        mock_cursor.execute.assert_called()
        args = mock_cursor.execute.call_args[0]
        self.assertIn("INSERT INTO settings", args[0])
        self.assertIn("dark", args[1])
        mock_conn.commit.assert_called()

if __name__ == '__main__':
    unittest.main()
