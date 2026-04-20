# YouTube Playlist to MP3 (Single Python App)

This project is now structured as a clear, single Streamlit application centered on one file: `app.py`.

## What You Get

- Single-app flow: fetch playlist -> choose all or selected videos -> download ZIP
- MP3 extraction with `yt-dlp` + FFmpeg
- Progress bar and clear status updates
- Error handling for invalid/private/unavailable playlists
- Deploy-ready setup for local run, PaaS, and Docker

## Core Files

- `app.py`: entire application logic and UI
- `requirements.txt`: dependencies
- `Procfile`: PaaS start command
- `Dockerfile`: container deployment

## Prerequisites

- Python 3.9+
- FFmpeg available in PATH

Install FFmpeg:

- Windows: `choco install ffmpeg`
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt update && sudo apt install -y ffmpeg`

## Local Run

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run app

```bash
streamlit run app.py
```

3. Open `http://localhost:8501`

## Deploy (PaaS)

Use the `Procfile` command:

```bash
web: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

Set environment/service to install system FFmpeg before launching app.

## Deploy (Docker)

1. Build image

```bash
docker build -t yt-playlist-mp3 .
```

2. Run container

```bash
docker run -p 8501:8501 yt-playlist-mp3
```

3. Open `http://localhost:8501`

## Notes

- Download only content you have rights to access.
- Respect YouTube terms and your local copyright laws.