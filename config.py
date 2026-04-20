"""
Configuration file for YouTube Playlist Downloader
Modify these settings to customize the application behavior
"""

# Audio quality settings
AUDIO_QUALITY = '320'  # kbps (128, 192, 256, 320)
AUDIO_FORMAT = 'mp3'   # mp3, m4a, wav, flac

# Download settings
MAX_CONCURRENT_DOWNLOADS = 1  # Number of simultaneous downloads
RETRY_ATTEMPTS = 3            # Number of retry attempts for failed downloads

# File naming template
# Available variables: %(title)s, %(uploader)s, %(playlist_index)s, %(duration)s, etc.
FILENAME_TEMPLATE = '%(playlist_index)02d - %(title)s.%(ext)s'

# Streamlit UI settings
PAGE_TITLE = "YouTube Playlist Downloader"
PAGE_ICON = "🎵"
LAYOUT = "wide"  # "centered" or "wide"

# Temporary directory settings
TEMP_DIR_PREFIX = "youtube_playlist_"
AUTO_CLEANUP = True  # Automatically clean up temporary files

# Progress update interval (seconds)
PROGRESS_UPDATE_INTERVAL = 0.5

# Maximum playlist size (0 = no limit)
MAX_PLAYLIST_SIZE = 0  # Set to a number to limit playlist size

# Custom yt-dlp options (advanced users only)
# These will be merged with the default options
CUSTOM_YDL_OPTS = {
    # Example: Add subtitle download
    # 'writesubtitles': True,
    # 'writeautomaticsub': True,
    
    # Example: Add thumbnail download
    # 'writethumbnail': True,
    
    # Example: Custom user agent
    # 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Error handling settings
SHOW_DETAILED_ERRORS = False  # Show detailed error messages to users
LOG_ERRORS = True            # Log errors to console

# UI customization
SHOW_PLAYLIST_INFO = True    # Show playlist title and video count
SHOW_INSTRUCTIONS = True     # Show usage instructions
SHOW_FOOTER = True          # Show footer with credits