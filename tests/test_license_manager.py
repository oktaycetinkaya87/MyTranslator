import unittest
from unittest.mock import patch
from pathlib import Path
from core.license_manager import LicenseManager

class TestLicenseManager(unittest.TestCase):

    @patch("core.license_manager.Path.home")
    def test_init(self, mock_home):
        mock_home.return_value = Path("/mock/home")
        manager = LicenseManager()
        self.assertEqual(manager.unlock_file, Path("/mock/home/.mytranslator/unlock.key"))

    @patch("core.license_manager.Path.exists")
    @patch("core.license_manager.Path.home")
    def test_is_unlimited_true(self, mock_home, mock_exists):
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        
        manager = LicenseManager()
        self.assertTrue(manager.is_unlimited())

    @patch("core.license_manager.Path.exists")
    @patch("core.license_manager.Path.home")
    def test_is_unlimited_false(self, mock_home, mock_exists):
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = False
        
        manager = LicenseManager()
        self.assertFalse(manager.is_unlimited())

    @patch("core.license_manager.Path.exists")
    @patch("core.license_manager.Path.home")
    def test_get_mode_unlimited(self, mock_home, mock_exists):
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = True
        
        manager = LicenseManager()
        self.assertEqual(manager.get_mode(), "UNLIMITED")

    @patch("core.license_manager.Path.exists")
    @patch("core.license_manager.Path.home")
    def test_get_mode_limited(self, mock_home, mock_exists):
        mock_home.return_value = Path("/mock/home")
        mock_exists.return_value = False
        
        manager = LicenseManager()
        self.assertEqual(manager.get_mode(), "LIMITED")

if __name__ == '__main__':
    unittest.main()
