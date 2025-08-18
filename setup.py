#!/usr/bin/env python3
"""
Setup script for YouTube Playlist Downloader
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ FFmpeg not found!")
    print("Please install FFmpeg:")
    print("  Windows: Download from https://ffmpeg.org/ or use 'choco install ffmpeg'")
    print("  macOS: brew install ffmpeg")
    print("  Linux: sudo apt install ffmpeg")
    return False

def install_requirements():
    """Install Python requirements"""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🎵 YouTube Playlist Downloader Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("\n⚠️  Setup can continue, but FFmpeg is required for the app to work!")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    print("\n🎉 Setup complete!")
    print("\nTo run the application:")
    print("  streamlit run app.py")
    print("\nThen open your browser to: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)