@echo off
REM Setup script for Codex Mentis Podcast Video Converter (Windows)

echo 🎙️  Setting up Codex Mentis Podcast Video Converter
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip.
    pause
    exit /b 1
)

echo ✓ pip found
pip --version

REM Install Python dependencies
echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies. Please check the error messages above.
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully!

REM Check directory structure
echo.
echo 📁 Checking directory structure...

if exist "input" (
    echo ✓ input/ directory exists
) else (
    echo ❌ input/ directory missing
)

if exist "output" (
    echo ✓ output/ directory exists
) else (
    echo ❌ output/ directory missing
)

if exist "assets" (
    echo ✓ assets/ directory exists
) else (
    echo ❌ assets/ directory missing
)

if exist "src" (
    echo ✓ src/ directory exists
) else (
    echo ❌ src/ directory missing
)

REM Check for logo
echo.
echo 🖼️  Checking for podcast logo...
if exist "assets\podcast_logo.jpg" (
    echo ✅ Podcast logo found!
) else (
    echo ⚠️  Podcast logo not found.
    echo Please place your podcast logo at: assets\podcast_logo.jpg
    echo.
    echo Logo requirements:
    echo • File name: podcast_logo.jpg
    echo • Recommended size: 500x500 pixels or larger
    echo • Format: JPG or PNG
)

echo.
echo 🎯 Setup complete! Usage instructions:
echo 1. Place your WAV files in the input\ directory
echo 2. Ensure your podcast logo is at assets\podcast_logo.jpg
echo 3. Run: python src\main.py
echo.
echo 📚 For more information, see README.md

pause
