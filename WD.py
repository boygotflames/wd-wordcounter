#!/usr/bin/env python3
"""
WD - Minimalist Word Counter Desktop App
Main launcher

Fixes for PyInstaller:
- Always write a runtime log (even in windowed builds)
- Show a Windows MessageBox on fatal startup errors
- Force Qt plugin paths in frozen mode (common "silent exit" cause)
- Add `--test` mode so build scripts can validate the exe quickly
"""

from __future__ import annotations

import os
import sys
import logging
import ctypes
from pathlib import Path

# ---------------------------------------------------------------------
# Runtime paths
# ---------------------------------------------------------------------
IS_FROZEN = bool(getattr(sys, "frozen", False))
MEIPASS = Path(getattr(sys, "_MEIPASS", "")) if IS_FROZEN and hasattr(sys, "_MEIPASS") else None
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent

LOG_PATH = APP_DIR / "wd_runtime.log"
_FAULT_FH = None


def _configure_logging() -> None:
    """Always log to a file next to the exe (or next to WD.py in dev)."""
    global _FAULT_FH

    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    handlers: list[logging.Handler] = []
    try:
        handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8", mode="a"))
    except Exception:
        handlers.append(logging.StreamHandler(sys.stderr))

    # Optional console stream (only exists in console builds)
    if sys.stdout:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )

    # Low-level crash dumps (segfaults, etc.)
    try:
        import faulthandler
        _FAULT_FH = open(LOG_PATH, "a", encoding="utf-8")
        faulthandler.enable(_FAULT_FH)
    except Exception:
        pass


def _windows_message_box(title: str, message: str) -> None:
    """Show a native Windows error popup (works even if Qt fails to init)."""
    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        pass


def _fatal_excepthook(exctype, value, tb) -> None:
    """Global exception hook: log + popup."""
    try:
        logging.critical("UNHANDLED EXCEPTION", exc_info=(exctype, value, tb))
    except Exception:
        pass

    msg = (
        "WD crashed on startup.\n\n"
        f"Log file:\n{LOG_PATH}\n\n"
        "Open the log and send the last ~30 lines."
    )

    if sys.platform == "win32":
        _windows_message_box("WD - Startup Error", msg)
    else:
        try:
            print(msg, file=sys.stderr)
        except Exception:
            pass


def _log_environment() -> None:
    logging.info("=== WD STARTUP ===")
    logging.info("IS_FROZEN=%s", IS_FROZEN)
    logging.info("APP_DIR=%s", APP_DIR)
    logging.info("CWD=%s", Path.cwd())
    logging.info("sys.executable=%s", sys.executable)
    if MEIPASS:
        logging.info("sys._MEIPASS=%s", MEIPASS)
    logging.info("sys.path=%s", sys.path)


def _maybe_fix_qt_paths() -> None:
    """
    In frozen mode, Qt sometimes fails to find its platform plugins (silent exit).
    PyInstaller usually handles this, but forcing the paths makes it robust.
    """
    # Make matplotlib pick a Qt backend when the GUI runs
    os.environ.setdefault("MPLBACKEND", "QtAgg")

    if not IS_FROZEN or not MEIPASS:
        return

    qt_bin = MEIPASS / "PyQt6" / "Qt6" / "bin"
    qt_plugins = MEIPASS / "PyQt6" / "Qt6" / "plugins"
    qt_platforms = qt_plugins / "platforms"

    if qt_bin.exists():
        os.environ["PATH"] = str(qt_bin) + os.pathsep + os.environ.get("PATH", "")
        logging.info("Added Qt bin to PATH: %s", qt_bin)

    if qt_plugins.exists():
        os.environ.setdefault("QT_PLUGIN_PATH", str(qt_plugins))
        logging.info("QT_PLUGIN_PATH=%s", os.environ.get("QT_PLUGIN_PATH"))

    if qt_platforms.exists():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(qt_platforms))
        logging.info("QT_QPA_PLATFORM_PLUGIN_PATH=%s", os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"))


# ---------------------------------------------------------------------
# Import path setup (must happen BEFORE importing your src modules)
# ---------------------------------------------------------------------
if IS_FROZEN and MEIPASS:
    src_path = MEIPASS / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
else:
    sys.path.insert(0, str(APP_DIR))


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource for dev and PyInstaller."""
    base = str(MEIPASS) if (IS_FROZEN and MEIPASS) else str(APP_DIR)
    return os.path.join(base, relative_path)


# ---------------------------------------------------------------------
# Centralized module imports (with logging)
# ---------------------------------------------------------------------
HAS_RUST = False


def _import_modules():
    global HAS_RUST

    _maybe_fix_qt_paths()

    # Rust backend (optional)
    try:
        import wdlib  # noqa: F401
        HAS_RUST = True
        logging.info("Rust backend: OK")
    except Exception as e:
        HAS_RUST = False
        logging.warning("Rust backend import failed (Python fallback): %s", e)

    # Managers
    try:
        from src.export_manager import ExportManager
        from src.theme_manager import ThemeManager
        logging.info("Imported managers from src.*")
    except Exception as e1:
        try:
            from export_manager import ExportManager
            from theme_manager import ThemeManager
            logging.info("Imported managers from direct modules (PyInstaller data mode)")
        except Exception as e2:
            raise ImportError(f"Failed to import ExportManager/ThemeManager: {e1} / {e2}") from e2

    # UI
    try:
        from src.ui_mainwindow import WDMainWindow
        import src.ui_mainwindow as ui_mod
        ui_mod.HAS_RUST = HAS_RUST
        logging.info("Imported UI from src.ui_mainwindow")
    except Exception as e1:
        try:
            from ui_mainwindow import WDMainWindow
            logging.info("Imported UI from direct ui_mainwindow")
        except Exception as e2:
            raise ImportError(f"Failed to import UI module: {e1} / {e2}") from e2

    return ExportManager, ThemeManager, WDMainWindow


def self_test() -> int:
    """Quick validation mode: used by build scripts as `Word-Counter.exe --test`."""
    try:
        _configure_logging()
        sys.excepthook = _fatal_excepthook
        _log_environment()

        _import_modules()

        icon = resource_path(os.path.join("assets", "wd_pixel.ico"))
        logging.info("Icon exists=%s path=%s", os.path.exists(icon), icon)

        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        app.quit()

        logging.info("Self-test OK")
        return 0
    except Exception:
        _fatal_excepthook(*sys.exc_info())
        return 1


def main() -> int:
    _configure_logging()
    sys.excepthook = _fatal_excepthook
    _log_environment()

    if "--test" in sys.argv:
        return self_test()

    try:
        ExportManager, ThemeManager, WDMainWindow = _import_modules()

        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon

        app = QApplication(sys.argv)
        app.setApplicationName("WD Word Counter")
        app.setApplicationDisplayName("WD")

        icon_path = resource_path(os.path.join("assets", "wd_pixel.ico"))
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # Theme (if it fails, we log but still run)
        try:
            theme_stylesheet = ThemeManager.apply_theme(app, "terminal_black")
            app.setStyleSheet(theme_stylesheet)
        except Exception as e:
            logging.exception("Theme apply failed: %s", e)

        window = WDMainWindow()
        window.show()

        # Helps if the window is created off-screen / behind other windows
        try:
            window.raise_()
            window.activateWindow()
        except Exception:
            pass

        return int(app.exec())
    except Exception:
        _fatal_excepthook(*sys.exc_info())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
