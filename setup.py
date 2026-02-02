"""
Setup script for WD Word Counter
Handles dependency installation on Windows
"""

import sys
import subprocess
import os

def check_and_install():
    """Check and install required packages"""
    
    required_packages = [
        "PyQt6",
        "watchdog",
        "matplotlib",
        "seaborn",
        "pandas",
        "jinja2",
        "textstat",
        "colorama",
        "pygments",
        "Pillow"
    ]
    
    print("Checking Python dependencies...")
    print("=" * 50)
    
    for package in required_packages:
        try:
            __import__(package.lower() if package == "PyQt6" else package)
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}")
                print("Trying alternative installation method...")
                try:
                    # Try without version constraints
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package.split(">=")[0]])
                except:
                    print(f"Please install {package} manually: pip install {package}")
    
    print("\n" + "=" * 50)
    print("Dependency check complete!")
    
    # Check Rust installation
    print("\nChecking Rust installation...")
    try:
        subprocess.run(["cargo", "--version"], check=True, capture_output=True)
        print("✓ Rust is installed")
        
        # Build Rust backend
        print("Building Rust backend...")
        subprocess.run(["cargo", "build", "--release"], check=True)
        print("✓ Rust backend built successfully")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Rust not found. Using Python fallback backend.")
        print("Install Rust from: https://rustup.rs/")

if __name__ == "__main__":
    check_and_install()
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now run:")
    print("  python WD.py")
    
    # Ask if user wants to run the app
    response = input("\nRun WD Word Counter now? (y/n): ")
    if response.lower() == 'y':
        print("Starting WD Word Counter...")
        os.system("python WD.py")