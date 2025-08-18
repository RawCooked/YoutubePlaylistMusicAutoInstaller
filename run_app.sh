#!/bin/bash

echo "🎵 Starting YouTube Playlist Downloader..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python version: $python_version"

# Check if requirements are installed
if ! python3 -c "import streamlit, yt_dlp" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        exit 1
    fi
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found! The app may not work properly."
    echo "Install FFmpeg:"
    echo "  macOS: brew install ffmpeg"
    echo "  Linux: sudo apt install ffmpeg"
    echo
fi

# Start the Streamlit app
echo "✅ Starting Streamlit app..."
echo "🌐 Your browser should open automatically to http://localhost:8501"
echo
echo "Press Ctrl+C to stop the application"
echo

streamlit run app.py