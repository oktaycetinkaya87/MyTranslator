import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from core.usage_tracker import UsageTracker

class TestUsageTracker(unittest.TestCase):
    
    @patch("core.usage_tracker.Path")
    def test_init_load_existing(self, MockPath):
        # Setup mock file structure
        mock_home = MagicMock()
        mock_config_dir = MagicMock()
        mock_usage_file = MagicMock()
        
        MockPath.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_config_dir
        mock_config_dir.__truediv__.return_value = mock_usage_file
        
        # Scenario: usage.json exists
        mock_usage_file.exists.return_value = True
        
        # Mock file content
        with patch("builtins.open", mock_open(read_data='{"translation_count": 50}')):
            tracker = UsageTracker(limit=200)
        
        self.assertEqual(tracker.limit, 200)
        self.assertEqual(tracker.usage_data["translation_count"], 50)
        mock_config_dir.mkdir.assert_called_with(parents=True, exist_ok=True)

    @patch("core.usage_tracker.Path")
    @patch("core.usage_tracker.json.dump")
    def test_init_create_new(self, mock_json_dump, MockPath):
        mock_home = MagicMock()
        mock_config_dir = MagicMock()
        mock_usage_file = MagicMock()
        
        MockPath.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_config_dir
        mock_config_dir.__truediv__.return_value = mock_usage_file
        
        # Scenario: usage.json does NOT exist
        mock_usage_file.exists.return_value = False
        
        # Mock open for WRITE operation (save_usage)
        with patch("builtins.open", mock_open()):
             tracker = UsageTracker()
             
        self.assertEqual(tracker.limit, 100)
        self.assertEqual(tracker.usage_data["translation_count"], 0)
        # Verify it saved default data (since load returned default 0)
        # Actually _load_usage returns 0, but __init__ doesn't call _save_usage explicitly unless count changes? 
        # Wait, UsageTracker.__init__ calls _load_usage. _load_usage returns default dict. 
        # But __init__ doesn't call _save_usage. So json.dump is NOT called in __init__.
        # My previous test assumption was wrong.
        mock_json_dump.assert_not_called()

    @patch("core.usage_tracker.Path")
    @patch("core.usage_tracker.json.dump")
    def test_increment(self, mock_json_dump, MockPath):
        mock_home = MagicMock()
        mock_config_dir = MagicMock()
        mock_usage_file = MagicMock()
        
        MockPath.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_config_dir
        mock_config_dir.__truediv__.return_value = mock_usage_file
        
        mock_usage_file.exists.return_value = True
        
        with patch("builtins.open", mock_open(read_data='{"translation_count": 10}')):
            tracker = UsageTracker()
        
        # Now mock open for writing in increment -> _save_usage
        with patch("builtins.open", mock_open()) as mock_write_file:
            tracker.increment()
        
        self.assertEqual(tracker.usage_data["translation_count"], 11)
        # Verify save called
        mock_json_dump.assert_called()

    @patch("core.usage_tracker.LicenseManager")
    @patch("core.usage_tracker.Path")
    def test_check_limit_under(self, MockPath, MockLicenseManager):
        # Mock Path structure (minimal for init)
        MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        
        # Mock LicenseManager to reflect LIMITED user
        mock_lm_instance = MockLicenseManager.return_value
        mock_lm_instance.is_unlimited.return_value = False
        
        tracker = UsageTracker(limit=100)
        tracker.usage_data = {"translation_count": 99} # Manually set data
        
        self.assertFalse(tracker.check_limit_reached()) # 99 < 100

    @patch("core.usage_tracker.LicenseManager")
    @patch("core.usage_tracker.Path")
    def test_check_limit_reached(self, MockPath, MockLicenseManager):
        MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        mock_lm_instance = MockLicenseManager.return_value
        mock_lm_instance.is_unlimited.return_value = False
        
        tracker = UsageTracker(limit=100)
        tracker.usage_data = {"translation_count": 100}
        
        self.assertTrue(tracker.check_limit_reached()) # 100 >= 100

    @patch("core.usage_tracker.LicenseManager")
    @patch("core.usage_tracker.Path")
    def test_check_limit_unlimited_user(self, MockPath, MockLicenseManager):
        MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        mock_lm_instance = MockLicenseManager.return_value
        mock_lm_instance.is_unlimited.return_value = True
        
        tracker = UsageTracker(limit=100)
        tracker.usage_data = {"translation_count": 150}
        
        # Even if count (150) > limit (100), it should return False because user is unlimited
        self.assertFalse(tracker.check_limit_reached())

    @patch("core.usage_tracker.Path")
    def test_get_used_and_remaining(self, MockPath):
        MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        tracker = UsageTracker(limit=100)
        tracker.usage_data = {"translation_count": 42}
        
        self.assertEqual(tracker.get_used(), 42)
        # Need to patch LicenseManager for get_remaining because it checks it
        with patch("core.usage_tracker.LicenseManager") as MockLM:
            MockLM.return_value.is_unlimited.return_value = False
            self.assertEqual(tracker.get_remaining(), 58)

    @patch("core.usage_tracker.Path")
    def test_can_translate(self, MockPath):
        MockPath.home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = False
        tracker = UsageTracker(limit=100)
        tracker.usage_data = {"translation_count": 42}
        
        with patch("core.usage_tracker.LicenseManager") as MockLM:
             MockLM.return_value.is_unlimited.return_value = False
             # 42 < 100 so can translate
             self.assertTrue(tracker.can_translate())

if __name__ == '__main__':
    unittest.main()
