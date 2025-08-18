# 🎵 YouTube Playlist Downloader

A Streamlit web application that allows you to download YouTube playlists as MP3 files bundled in a convenient ZIP package.

## 🎯 Features

- **Simple Interface**: Clean, user-friendly Streamlit web interface
- **Playlist Support**: Download entire YouTube playlists with one click
- **MP3 Conversion**: Automatically extracts audio and converts to MP3 format (192 kbps)
- **Progress Tracking**: Real-time progress bar showing download status
- **ZIP Packaging**: All MP3 files bundled into a single ZIP file for easy download
- **Error Handling**: Robust error handling for invalid URLs and failed downloads
- **Auto Cleanup**: Temporary files are automatically cleaned up after download
- **URL Validation**: Validates YouTube playlist URLs before processing

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- FFmpeg (required for audio conversion)

### Install FFmpeg

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract and add to your system PATH
3. Or use chocolatey: `choco install ffmpeg`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Install Python Dependencies

1. Clone or download this repository
2. Navigate to the project directory
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Running the Application

1. Open a terminal/command prompt
2. Navigate to the project directory
3. Run the Streamlit app:

```bash
streamlit run app.py
```

4. Your web browser should automatically open to `http://localhost:8501`
5. If it doesn't open automatically, navigate to that URL manually

### Using the App

1. **Enter Playlist URL**: Paste a YouTube playlist URL into the text field
2. **Validate URL**: The app will automatically validate and show playlist information
3. **Download**: Click "Download Playlist" to start the download process
4. **Monitor Progress**: Watch the progress bar as videos are downloaded and converted
5. **Download ZIP**: Once complete, click "Download ZIP" to save the files to your computer
6. **Extract**: Extract the ZIP file to access your MP3 files

### Supported URL Formats

- `https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx`
- `https://www.youtube.com/watch?v=xxxxxxxxx&list=PLxxxxxxxxxxxxxxx`
- `https://youtu.be/xxxxxxxxx?list=PLxxxxxxxxxxxxxxx`

## 📁 File Structure

```
pythonApp/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Technical Details

### Dependencies

- **Streamlit**: Web framework for the user interface
- **yt-dlp**: YouTube downloader and audio extractor
- **FFmpeg**: Audio/video processing (external dependency)

### Audio Quality

- Format: MP3
- Quality: 192 kbps
- Source: Best available audio stream from YouTube

### File Naming

Downloaded files are named with the format:
`{playlist_index} - {video_title}.mp3`

Example: `01 - My Favorite Song.mp3`

## ⚠️ Important Notes

1. **FFmpeg Required**: Make sure FFmpeg is installed and accessible from your system PATH
2. **Internet Connection**: Stable internet connection required for downloading
3. **Disk Space**: Ensure sufficient disk space for temporary files and final ZIP
4. **YouTube Terms**: Respect YouTube's Terms of Service when using this tool
5. **Copyright**: Only download content you have the right to download

## 🐛 Troubleshooting

### Common Issues

**"FFmpeg not found" error:**
- Install FFmpeg and ensure it's in your system PATH
- Restart your terminal/command prompt after installation

**"Invalid playlist URL" error:**
- Ensure the URL contains a playlist ID (list parameter)
- Check that the playlist is public and accessible

**Download fails:**
- Check your internet connection
- Verify the playlist still exists and is accessible
- Some videos might be region-restricted or private

**Streamlit won't start:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using Python 3.7 or higher
- Try running with: `python -m streamlit run app.py`

### Getting Help

If you encounter issues:
1. Check the error messages in the Streamlit interface
2. Look at the terminal/command prompt for detailed error logs
3. Ensure all prerequisites are properly installed

## 📝 License

This project is for educational purposes. Please respect YouTube's Terms of Service and copyright laws when using this application.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this application.