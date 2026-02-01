@echo off
chcp 65001 >nul
title WD Word Counter

echo ========================================
echo   WD - Minimalist Word Counter
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
pip list | findstr "PyQt6" >nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Build Rust backend if needed
if not exist "wdlib.pyd" (
    if exist "Cargo.toml" (
        echo Building Rust backend...
        cargo build --release
        if exist "target\release\wdlib.dll" (
            copy "target\release\wdlib.dll" "wdlib.pyd"
        )
    )
)

REM Run the application
echo.
echo Starting WD Word Counter...
python WD.py

pause