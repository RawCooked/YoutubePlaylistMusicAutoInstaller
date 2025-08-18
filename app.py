import streamlit as st
import yt_dlp
import os
import tempfile
import zipfile
import shutil
import re
from pathlib import Path
import threading
import time

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Playlist Downloader",
    page_icon="🎵",
    layout="wide"
)

def is_valid_playlist_url(url):
    """Check if the URL is a valid YouTube playlist URL"""
    playlist_patterns = [
        r'youtube\.com/playlist\?list=',
        r'youtube\.com/watch\?.*list=',
        r'youtu\.be/.*list='
    ]
    return any(re.search(pattern, url) for pattern in playlist_patterns)

def get_playlist_info(url):
    """Get playlist information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return {
                    'title': info.get('title', 'Unknown Playlist'),
                    'count': len(list(info['entries']))
                }
    except Exception as e:
        st.error(f"Error getting playlist info: {str(e)}")
        return None
    
    return None

def download_playlist_audio(url, temp_dir, progress_callback=None):
    """Download playlist as MP3 files"""
    
    # yt-dlp options for audio extraction
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    
    # Add progress hook if callback provided
    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
        return False

def create_zip_file(temp_dir, zip_path):
    """Create ZIP file from downloaded MP3 files"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.mp3'):
                        file_path = os.path.join(root, file)
                        # Add file to zip with just the filename (no path)
                        zipf.write(file_path, file)
        return True
    except Exception as e:
        st.error(f"Failed to create ZIP file: {str(e)}")
        return False

def cleanup_temp_files(temp_dir):
    """Clean up temporary directory"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        st.warning(f"Could not clean up temporary files: {str(e)}")

def main():
    st.title("🎵 YouTube Playlist Downloader")
    st.markdown("Download YouTube playlists as MP3 files in a convenient ZIP package!")
    
    # Initialize session state
    if 'download_complete' not in st.session_state:
        st.session_state.download_complete = False
    if 'zip_path' not in st.session_state:
        st.session_state.zip_path = None
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'playlist_title' not in st.session_state:
        st.session_state.playlist_title = None
    
    # URL input
    st.subheader("📋 Enter Playlist URL")
    playlist_url = st.text_input(
        "YouTube Playlist URL:",
        placeholder="https://www.youtube.com/playlist?list=...",
        help="Enter a valid YouTube playlist URL"
    )
    
    # Validate URL and show playlist info
    if playlist_url:
        if is_valid_playlist_url(playlist_url):
            st.success("✅ Valid playlist URL detected!")
            
            # Get playlist info
            with st.spinner("Getting playlist information..."):
                playlist_info = get_playlist_info(playlist_url)
            
            if playlist_info:
                st.info(f"📊 **{playlist_info['title']}** - {playlist_info['count']} videos")
                
                # Download button
                col1, col2 = st.columns([1, 3])
                with col1:
                    download_btn = st.button("🎵 Download Playlist", type="primary")
                
                if download_btn:
                    # Reset session state
                    st.session_state.download_complete = False
                    st.session_state.zip_path = None
                    
                    # Create temporary directory
                    temp_dir = tempfile.mkdtemp(prefix="youtube_playlist_")
                    st.session_state.temp_dir = temp_dir
                    st.session_state.playlist_title = playlist_info['title']
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    downloaded_count = 0
                    total_count = playlist_info['count']
                    
                    def progress_hook(d):
                        nonlocal downloaded_count
                        if d['status'] == 'finished':
                            downloaded_count += 1
                            progress = downloaded_count / total_count
                            progress_bar.progress(progress)
                            status_text.text(f"Downloaded {downloaded_count}/{total_count} videos...")
                    
                    status_text.text("Starting download...")
                    
                    # Download playlist
                    success = download_playlist_audio(playlist_url, temp_dir, progress_hook)
                    
                    if success:
                        status_text.text("Creating ZIP file...")
                        
                        # Create ZIP file
                        zip_filename = f"{playlist_info['title']}_playlist.zip"
                        # Clean filename for filesystem
                        zip_filename = re.sub(r'[<>:"/\\|?*]', '_', zip_filename)
                        zip_path = os.path.join(temp_dir, zip_filename)
                        
                        if create_zip_file(temp_dir, zip_path):
                            st.session_state.download_complete = True
                            st.session_state.zip_path = zip_path
                            progress_bar.progress(1.0)
                            status_text.text("✅ Download complete!")
                            st.success("🎉 Playlist downloaded successfully!")
                        else:
                            cleanup_temp_files(temp_dir)
                    else:
                        cleanup_temp_files(temp_dir)
            else:
                st.error("❌ Could not retrieve playlist information. Please check the URL.")
        else:
            st.error("❌ Invalid playlist URL. Please enter a valid YouTube playlist URL.")
    
    # Download section
    if st.session_state.download_complete and st.session_state.zip_path:
        st.subheader("📥 Download Your Files")
        
        # Read ZIP file for download
        try:
            with open(st.session_state.zip_path, 'rb') as f:
                zip_data = f.read()
            
            zip_filename = os.path.basename(st.session_state.zip_path)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                download_button = st.download_button(
                    label="📦 Download ZIP",
                    data=zip_data,
                    file_name=zip_filename,
                    mime="application/zip",
                    type="primary"
                )
            
            if download_button:
                st.success("📁 ZIP file downloaded! You can now close this page.")
                # Clean up after download
                cleanup_temp_files(st.session_state.temp_dir)
                st.session_state.download_complete = False
                st.session_state.zip_path = None
                st.session_state.temp_dir = None
                
        except Exception as e:
            st.error(f"Error preparing download: {str(e)}")
            cleanup_temp_files(st.session_state.temp_dir)
    
    # Instructions
    st.markdown("---")
    st.subheader("📖 Instructions")
    st.markdown("""
    1. **Enter a YouTube playlist URL** in the text field above
    2. **Click "Download Playlist"** to start the download process
    3. **Wait for the download to complete** - you'll see a progress bar
    4. **Click "Download ZIP"** to save the MP3 files to your computer
    5. **Extract the ZIP file** to access your MP3 files
    
    **Supported URL formats:**
    - `https://www.youtube.com/playlist?list=...`
    - `https://www.youtube.com/watch?v=...&list=...`
    - `https://youtu.be/...?list=...`
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit and yt-dlp*")

if __name__ == "__main__":
    main()