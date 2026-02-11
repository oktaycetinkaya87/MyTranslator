import os
from pathlib import Path

class LicenseManager:
    """Kullanıcının limitsiz erişimi olup olmadığını kontrol eder"""
    
    def __init__(self):
        # ~/.mytranslator/unlock.key dosyasının yolu
        self.config_dir = Path.home() / ".mytranslator"
        self.unlock_file = self.config_dir / "unlock.key"
    
    def is_unlimited(self):
        """
        unlock.key dosyası varsa True döner (Limitsiz)
        Yoksa False döner (Limited - 100 çeviri)
        """
        return self.unlock_file.exists()
    
    def get_mode(self):
        """Kullanıcı modunu string olarak döner"""
        return "UNLIMITED" if self.is_unlimited() else "LIMITED"
