#!/usr/bin/env python3
"""
WD - Minimalist Word Counter Desktop App
Main launcher
"""

import sys
import os
import ctypes
import subprocess
from pathlib import Path

# Try to import UI module at top level (helps PyInstaller detect it)
try:
    from src.ui_mainwindow import WDMainWindow
    _UI_AVAILABLE = True
except ImportError:
    _UI_AVAILABLE = False
    WDMainWindow = None

# Add Rust library path
rust_lib_path = Path(__file__).parent / "target" / "release"
if rust_lib_path.exists():
    sys.path.insert(0, str(rust_lib_path))

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        from PyQt6.QtWidgets import QApplication
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nInstall dependencies with:")
        print("pip install PyQt6 pyqt6-tools")
        return False

def build_rust_backend():
    """Build the Rust backend if not already built"""
    try:
        import wdlib
        print("✓ Rust backend already built")
        return True
    except ImportError:
        print("Building Rust backend...")
        
        project_dir = Path(__file__).parent
        cargo_toml = project_dir / "Cargo.toml"
        
        if cargo_toml.exists():
            try:
                # Build in release mode
                result = subprocess.run(
                    ["cargo", "build", "--release"],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    shell=True
                )
                
                if result.returncode == 0:
                    print("✓ Rust backend built successfully")
                    
                    # Copy library to appropriate location
                    if sys.platform == "win32":
                        src_lib = project_dir / "target" / "release" / "wdlib.dll"
                    elif sys.platform == "darwin":
                        src_lib = project_dir / "target" / "release" / "libwdlib.dylib"
                    else:
                        src_lib = project_dir / "target" / "release" / "libwdlib.so"
                    
                    if src_lib.exists():
                        dest_dir = Path(__file__).parent
                        dest_lib = dest_dir / "wdlib.pyd" if sys.platform == "win32" else dest_dir / "wdlib.so"
                        import shutil
                        shutil.copy2(src_lib, dest_lib)
                        print(f"✓ Library copied to {dest_lib}")
                    
                    return True
                else:
                    print("✗ Failed to build Rust backend")
                    print("Error:", result.stderr)
                    return False
                    
            except FileNotFoundError:
                print("✗ Cargo not found. Install Rust from: https://rustup.rs/")
                return False
        else:
            print("✗ Cargo.toml not found")
            return False

def set_windows_title():
    """Set Windows console title"""
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW("WD Word Counter")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def main():
    """Main entry point"""
    set_windows_title()
    
    if sys.stdout:
        print("=" * 50)
        print("WD - Minimalist Word Counter v1.0")
        print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Try to build Rust backend
    if sys.stdout:
        print("\nChecking backend...")
    rust_available = build_rust_backend()
    
    if rust_available:
        if sys.stdout: print("✓ Using Rust backend (fast)")
    else:
        if sys.stdout: print("⚠ Using Python backend (slower)")
    
    # Import and run app
    from PyQt6.QtWidgets import QApplication
    
    if sys.stdout: print("\nLaunching WD Word Counter...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("WD Word Counter")
    app.setApplicationDisplayName("WD")
    
    # Set window icon
    from PyQt6.QtGui import QIcon
    icon_path = resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Set dark palette
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 255, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
    app.setPalette(palette)
    
    # Ensure UI class is loaded
    ui_class = WDMainWindow
    if not _UI_AVAILABLE:
        try:
            from src.ui_mainwindow import WDMainWindow as ui_class
        except ImportError:
            sys.exit(1)
            
    window = ui_class()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()