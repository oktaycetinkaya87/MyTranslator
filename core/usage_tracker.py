import json
from pathlib import Path
from core.license_manager import LicenseManager

class UsageTracker:
    """Kullanıcının kaç çeviri yaptığını takip eder"""
    
    def __init__(self, limit=100):
        self.limit = limit
        self.config_dir = Path.home() / ".mytranslator"
        self.usage_file = self.config_dir / "usage.json"
        
        # Klasör yoksa oluştur
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Kullanım verilerini yükle
        self.usage_data = self._load_usage()
    
    def _load_usage(self):
        """usage.json dosyasından veriyi yükle"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                return {"translation_count": 0}
        return {"translation_count": 0}
    
    def _save_usage(self):
        """usage.json dosyasına kaydet"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)

    def increment(self):
        """Çeviri sayısını 1 artır"""
        self.usage_data["translation_count"] += 1
        self._save_usage()
        
    def check_limit_reached(self):
        """
        Eğer Limitsiz moddaysa -> Her zaman False (Kullanabilir)
        Eğer Limited moddaysa ve Çeviri >= 100 ise -> True (Engelli)
        """
        manager = LicenseManager()
        if manager.is_unlimited():
            return False # Limit YOK
        
        return self.usage_data["translation_count"] >= self.limit

    def can_translate(self):
        """Ters mantık: Limit aşılmadıysa True döner"""
        return not self.check_limit_reached()

    def get_count(self):
        return self.usage_data["translation_count"]

    def get_used(self):
        """Kullanılan çeviri sayısını döner"""
        return self.get_count()

    def get_remaining(self):
        """
        Kalan hakkı döner.
        Limitsiz ise -> -1 döner
        Limited ise -> limit - kullanılan
        """
        if LicenseManager().is_unlimited():
            return -1
        
        remaining = self.limit - self.get_count()
        return max(0, remaining)
