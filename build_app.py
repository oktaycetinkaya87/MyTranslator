import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
APP_NAME = "MyTranslator"
MAIN_SCRIPT = "main.py"
LICENSE_MANAGER_PATH = os.path.join("core", "license_manager.py")

# Detect OS
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'

# OS Specific Config
if IS_WINDOWS:
    ICON_FILE = os.path.join("assets", "app_icon.ico")
    ADD_DATA_SEP = ";"
else:
    ICON_FILE = os.path.join("assets", "app_icon.icns")
    ADD_DATA_SEP = ":"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def build(mode="limited"):
    print(f"🔨 Building {APP_NAME} in [{mode.upper()}] mode on {sys.platform}...")
    
    original_code = read_file(LICENSE_MANAGER_PATH)
    
    try:
        # Modify License Manager if Unlimited
        if mode == "unlimited":
            print(f"🔓 Patching {LICENSE_MANAGER_PATH} for unlimited access...")
            new_code = original_code.replace(
                "return self.unlock_file.exists()", 
                "return True # Patched for Unlimited Build"
            )
            write_file(LICENSE_MANAGER_PATH, new_code)
        
        # Clean previous builds
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        
        # PyInstaller Command Construction
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name", f"{APP_NAME}_{mode.capitalize()}",
            f"--add-data", f"assets{ADD_DATA_SEP}assets",
            "--hidden-import", "PIL",
            MAIN_SCRIPT
        ]

        # Conditional Hidden Imports
        if IS_MACOS:
            cmd.extend([
                "--hidden-import", "pynput.keyboard._darwin",
                "--hidden-import", "pynput.mouse._darwin"
            ])
        elif IS_WINDOWS:
            cmd.extend([
                "--hidden-import", "pynput.keyboard._win32",
                "--hidden-import", "pynput.mouse._win32"
            ])
        
        # Icon
        if os.path.exists(ICON_FILE):
             cmd.extend(["--icon", ICON_FILE])
        else:
            print(f"⚠️ Icon not found: {ICON_FILE}")

        # Execute
        print(f"🚀 Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        print(f"✅ Build Successful: dist/{APP_NAME}_{mode.capitalize()}")
        
    except Exception as e:
        print(f"❌ Build Failed: {e}")
        sys.exit(1)
        
    finally:
        # Restore License Manager
        if mode == "unlimited":
            print(f"🔄 Restoring {LICENSE_MANAGER_PATH}...")
            write_file(LICENSE_MANAGER_PATH, original_code)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["limited", "unlimited", "all"], default="all")
    args = parser.parse_args()
    
    if args.mode == "all":
        build("limited")
        print("-" * 30)
        build("unlimited")
    else:
        build(args.mode)
