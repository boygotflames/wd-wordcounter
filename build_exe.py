"""
Build standalone .exe for WD Word Counter v2.0 (Windows)

Fixes:
- build_exe.py was duplicated/corrupted; this is a clean single-copy version
- prerequisites check now imports correct module names (Pillow -> PIL)
- includes optional deps (textstat, wordcloud) in spec to prevent runtime ModuleNotFoundError
- adds --debug mode to build a console exe + PyInstaller debug logs
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path


# ----------------------------
# Config
# ----------------------------
REQUIRED = [
    # (pip_name, import_name)
    ("PyQt6", "PyQt6"),
    ("matplotlib", "matplotlib"),
    ("jinja2", "jinja2"),
    ("Pillow", "PIL"),
    ("textstat", "textstat"),
    ("wordcloud", "wordcloud"),
]

PYINSTALLER_LOG = Path("build_pyinstaller.log")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and stream output."""
    return subprocess.run(cmd, check=check)


def check_prerequisites() -> None:
    print("Checking prerequisites...")

    missing: list[str] = []
    for pip_name, import_name in REQUIRED:
        try:
            __import__(import_name)
            print(f"✓ {pip_name}")
        except Exception:
            missing.append(pip_name)

    if missing:
        print(f"\nMissing packages: {missing}")
        print("Installing missing packages...")
        for pkg in missing:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False)

    # Ensure PyInstaller exists
    try:
        import PyInstaller  # noqa: F401
        print("✓ PyInstaller")
    except Exception:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)


def clean_build_artifacts() -> None:
    for p in ["build", "dist", "build_debug", "dist_debug", "WD.spec", "Word-Counter.spec", "Word-Counter.pkg", "wdlib.pyd"]:
        try:
            path = Path(p)
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()
        except Exception:
            pass


def build_rust_backend() -> bool:
    """
    Build Rust backend if Cargo.toml exists.
    Copies target/release/wdlib.dll -> wdlib.pyd (Windows extension modules are DLLs with .pyd)
    """
    print("\nChecking Rust backend...")

    cargo_toml = Path("Cargo.toml")
    if not cargo_toml.exists():
        print("No Rust project found. Using Python backend only.")
        return False

    try:
        print("Building Rust backend...")
        result = subprocess.run(
            ["cargo", "build", "--release"],
            capture_output=True,
            text=True,
            shell=True,
        )

        if result.returncode != 0:
            print("✗ Failed to build Rust backend")
            print(result.stderr)
            return False

        print("✓ Rust backend built successfully")

        if sys.platform == "win32":
            src_lib = Path("target") / "release" / "wdlib.dll"
            dest_lib = Path("wdlib.pyd")
        elif sys.platform == "darwin":
            src_lib = Path("target") / "release" / "libwdlib.dylib"
            dest_lib = Path("wdlib.so")
        else:
            src_lib = Path("target") / "release" / "libwdlib.so"
            dest_lib = Path("wdlib.so")

        if src_lib.exists():
            shutil.copy2(src_lib, dest_lib)
            print(f"✓ Copied {src_lib} -> {dest_lib}")
            return True

        print(f"✗ Library not found at {src_lib}")
        return False

    except FileNotFoundError:
        print("✗ Cargo not found. Install Rust from: https://rustup.rs/")
        return False
    except Exception as e:
        print(f"✗ Error building Rust backend: {e}")
        return False


def create_pyinstaller_spec(debug: bool) -> None:
    """
    Generate WD.spec. In debug mode:
    - console=True
    - debug=True
    - upx=False (less moving parts)
    """
    if not Path("hooks").exists():
        Path("hooks").mkdir(parents=True, exist_ok=True)

    # NOTE: We use collect_all for packages that often break silently when missing.
    # Add more here if your UI imports more libs dynamically.
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Ensure project root and src are visible during analysis
project_root = os.path.abspath('.')
src_root = os.path.abspath('src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_root)

pyqt6_datas, pyqt6_binaries, pyqt6_hidden = collect_all('PyQt6')
mpl_datas, mpl_binaries, mpl_hidden = collect_all('matplotlib')
jinja2_datas, jinja2_binaries, jinja2_hidden = collect_all('jinja2')
pillow_datas, pillow_binaries, pillow_hidden = collect_all('PIL')

# Optional deps used by your project (you installed them)
textstat_datas, textstat_binaries, textstat_hidden = collect_all('textstat')
wordcloud_datas, wordcloud_binaries, wordcloud_hidden = collect_all('wordcloud')

datas = [
    ('src', 'src'),
    ('assets', 'assets'),
] + pyqt6_datas + mpl_datas + jinja2_datas + pillow_datas + textstat_datas + wordcloud_datas

binaries = pyqt6_binaries + mpl_binaries + jinja2_binaries + pillow_binaries + textstat_binaries + wordcloud_binaries

hiddenimports = [
    # Qt
    'PyQt6.sip',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',

    # matplotlib Qt backend
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_qt',
    'matplotlib.pyplot',

    # jinja2 / pillow
    'jinja2',
    'PIL',
    'PIL._imaging',

    # optional deps
    'textstat',
    'wordcloud',

    # your internal modules
    'src.ui_mainwindow',
    'src.export_manager',
    'src.theme_manager',
] + pyqt6_hidden + mpl_hidden + jinja2_hidden + pillow_hidden + textstat_hidden + wordcloud_hidden

a = Analysis(
    ['WD.py'],
    pathex=[project_root, src_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
    cipher=block_cipher,
    noarchive=False,
)

# Include Rust backend if present
if os.path.exists('wdlib.pyd'):
    a.binaries.append(('wdlib.pyd', 'wdlib.pyd', 'BINARY'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=('Word-Counter-Debug' if {str(debug)} else 'Word-Counter'),
    debug={str(debug)},
    bootloader_ignore_signals=False,
    strip=False,
    upx={str(not debug)},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={str(debug)},
    disable_windowed_traceback=False,
    icon='assets/wd_pixel.ico' if os.path.exists('assets/wd_pixel.ico') else None,
)
'''
    Path("WD.spec").write_text(spec_content, encoding="utf-8")
    print("✓ WD.spec created")


def run_pyinstaller(debug: bool) -> bool:
    print("\nRunning PyInstaller...")

    distpath = "dist_debug" if debug else "dist"
    workpath = "build_debug" if debug else "build"

    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--distpath", distpath,
        "--workpath", workpath,
        "WD.spec",
    ]
    if debug:
        cmd += ["--log-level=DEBUG"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Persist the build logs no matter what
    try:
        PYINSTALLER_LOG.write_text(
            "=== STDOUT ===\n" + (result.stdout or "") + "\n\n=== STDERR ===\n" + (result.stderr or ""),
            encoding="utf-8",
        )
        print(f"✓ PyInstaller log saved to: {PYINSTALLER_LOG}")
    except Exception:
        pass

    if result.returncode != 0:
        print("\n✗ BUILD FAILED (see build_pyinstaller.log)")
        print(result.stderr)
        return False

    exe_name = "Word-Counter-Debug.exe" if debug else "Word-Counter.exe"
    exe_path = Path("dist_debug" if debug else "dist") / exe_name
    if not exe_path.exists():
        print(f"✗ Build finished but exe was not found in {exe_path.parent}/")
        return False

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 55)
    print("✅ BUILD SUCCESSFUL!")
    print("=" * 55)
    print(f"Executable: {exe_path} ({size_mb:.1f} MB)")

    # Quick test (now supported by WD.py)
    print("\nTesting executable with --test ...")
    try:
        test = subprocess.run([str(exe_path), "--test"], timeout=10)
        if test.returncode == 0:
            print("✓ --test passed")
        else:
            print("⚠ --test failed (check wd_runtime.log next to the exe)")
    except Exception:
        print("⚠ Could not run --test (check wd_runtime.log next to the exe)")

    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Build a console exe + verbose logs")
    parser.add_argument("--clean", action="store_true", help="Delete build/dist/spec before building")
    parser.add_argument("--skip-rust", action="store_true", help="Skip building Rust backend")
    args = parser.parse_args()

    print("=" * 60)
    print("WD Word Counter v2.0 - Build System")
    print("=" * 60)

    if args.clean:
        clean_build_artifacts()

    check_prerequisites()

    if not args.skip_rust:
        build_rust_backend()

    create_pyinstaller_spec(debug=args.debug)
    ok = run_pyinstaller(debug=args.debug)

    print("\n" + "=" * 60)
    print("Build process complete!")
    print("=" * 60)

    if ok:
        print("\nNext steps:")
        if args.debug:
            print(r"Run debug exe: .\dist_debug\Word-Counter-Debug.exe")
        else:
            print(r"Run release exe: .\dist\Word-Counter.exe")
        return 0

    print("\nBuild failed. Check build_pyinstaller.log")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
