@echo off
echo 🎵 Starting YouTube Playlist Downloader...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import streamlit, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Start the Streamlit app
echo ✅ Starting Streamlit app...
echo 🌐 Your browser should open automatically to http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.
streamlit run app.py

pause