# 📦 Installation Guide

This guide will help you install and run the YouTube Playlist Downloader on your system.

## 🔧 Prerequisites

### 1. Python 3.7+
Download and install Python from [python.org](https://www.python.org/downloads/)

**Verify installation:**
```bash
python --version
# or
python3 --version
```

### 2. FFmpeg (Required for audio conversion)

#### Windows
**Option 1: Download manually**
1. Go to https://ffmpeg.org/download.html
2. Download the Windows build
3. Extract to a folder (e.g., `C:\ffmpeg`)
4. Add `C:\ffmpeg\bin` to your system PATH

**Option 2: Using Chocolatey**
```cmd
choco install ffmpeg
```

**Option 3: Using Scoop**
```cmd
scoop install ffmpeg
```

#### macOS
```bash
# Using Homebrew (recommended)
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# Fedora
sudo dnf install ffmpeg

# CentOS/RHEL (enable EPEL first)
sudo yum install epel-release
sudo yum install ffmpeg
```

**Verify FFmpeg installation:**
```bash
ffmpeg -version
```

## 🚀 Quick Installation

### Method 1: Automated Setup (Recommended)

1. **Download/Clone the project**
2. **Run the setup script:**

```bash
# On Windows
python setup.py

# On Linux/macOS
python3 setup.py
```

3. **Start the application:**

```bash
# On Windows
run_app.bat

# On Linux/macOS
chmod +x run_app.sh
./run_app.sh
```

### Method 2: Manual Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
```

2. **Run the application:**
```bash
streamlit run app.py
```

3. **Open your browser to:**
```
http://localhost:8501
```

## 🧪 Testing Installation

Run the test script to verify everything is working:

```bash
python test_installation.py
# or
python3 test_installation.py
```

This will check:
- ✅ Python version (3.7+)
- ✅ Streamlit installation
- ✅ yt-dlp installation
- ✅ FFmpeg availability
- ✅ Streamlit CLI functionality

## 🐛 Troubleshooting

### Common Issues

#### "Python not found" or "Command not found"
- **Windows**: Make sure Python is added to your PATH during installation
- **Linux/macOS**: Try using `python3` instead of `python`

#### "FFmpeg not found"
- Verify FFmpeg is installed: `ffmpeg -version`
- **Windows**: Ensure FFmpeg is in your system PATH
- **Linux/macOS**: Try installing via package manager

#### "Permission denied" (Linux/macOS)
```bash
chmod +x run_app.sh
chmod +x setup.py
chmod +x test_installation.py
```

#### "Module not found" errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or install individually
pip install streamlit yt-dlp
```

#### Streamlit won't start
```bash
# Try running directly
python -m streamlit run app.py

# Check Streamlit installation
streamlit --version
```

#### Downloads fail with "No audio streams found"
- This usually means FFmpeg is not properly installed or not in PATH
- Verify FFmpeg installation and restart your terminal

### Advanced Troubleshooting

#### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv youtube_downloader
# or
python3 -m venv youtube_downloader

# Activate virtual environment
# Windows:
youtube_downloader\Scripts\activate
# Linux/macOS:
source youtube_downloader/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

#### Proxy/Firewall Issues
If you're behind a corporate firewall:

```bash
# Set proxy for pip
pip install --proxy http://proxy.company.com:port -r requirements.txt

# Set proxy for yt-dlp (add to config.py)
CUSTOM_YDL_OPTS = {
    'proxy': 'http://proxy.company.com:port'
}
```

#### Memory Issues (Large Playlists)
For very large playlists, you might need to:

1. Increase system memory/swap
2. Limit playlist size in `config.py`:
```python
MAX_PLAYLIST_SIZE = 50  # Limit to 50 videos
```

## 📱 Platform-Specific Notes

### Windows
- Use Command Prompt or PowerShell
- Antivirus software might flag yt-dlp (add exception if needed)
- Windows Defender might slow down downloads

### macOS
- Use Terminal
- You might need to install Xcode Command Line Tools: `xcode-select --install`
- Some versions might require additional certificates

### Linux
- Most distributions work out of the box
- Ensure you have `python3-pip` installed
- Some minimal distributions might need additional packages

## 🔄 Updating

To update the application:

```bash
# Update Python packages
pip install --upgrade streamlit yt-dlp

# Update FFmpeg (platform-specific)
# Windows (Chocolatey): choco upgrade ffmpeg
# macOS (Homebrew): brew upgrade ffmpeg
# Linux: sudo apt upgrade ffmpeg
```

## 📞 Getting Help

If you're still having issues:

1. **Run the test script** to identify specific problems
2. **Check the error messages** in the terminal/command prompt
3. **Verify all prerequisites** are properly installed
4. **Try the virtual environment approach** for a clean installation
5. **Check firewall/antivirus settings** if downloads fail

## 🎯 Next Steps

Once installed successfully:

1. Open your browser to `http://localhost:8501`
2. Enter a YouTube playlist URL
3. Click "Download Playlist"
4. Wait for the download to complete
5. Download the ZIP file with your MP3s

Enjoy your music! 🎵