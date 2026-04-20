import os
import re
import shutil
import tempfile
import time
import zipfile
from datetime import datetime

import streamlit as st
import yt_dlp
from yt_dlp.postprocessor import MetadataParserPP


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Playlist Studio",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Styling — polished, lightweight (no external assets, no heavy animations)
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
    --accent: #7c3aed;
    --accent-2: #ec4899;
    --bg-card: rgba(255,255,255,0.03);
    --bg-card-hover: rgba(255,255,255,0.06);
    --border: rgba(255,255,255,0.08);
    --muted: rgba(255,255,255,0.55);
}

/* Root tweaks */
.stApp {
    background:
        radial-gradient(1200px 600px at 10% -10%, rgba(124,58,237,0.18), transparent 60%),
        radial-gradient(1000px 600px at 100% 0%, rgba(236,72,153,0.12), transparent 60%),
        #0b0b12;
    color: #eaeaf0;
}

/* Hide Streamlit chrome we don't want */
#MainMenu, footer {visibility: hidden;}
header [data-testid="stDecoration"] {display:none;}

/* Header hero */
.hero {
    padding: 28px 30px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background:
        linear-gradient(135deg, rgba(124,58,237,0.22), rgba(236,72,153,0.14));
    backdrop-filter: blur(8px);
    margin-bottom: 18px;
}
.hero h1 {
    margin: 0;
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fff, #dcd4ff 40%, #ffc9e6);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hero p {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 0.95rem;
}
.hero .dot {
    display:inline-block; width:8px; height:8px; border-radius:50%;
    background:#22c55e; margin-right:8px; box-shadow:0 0 10px #22c55e;
}

/* Cards */
.card {
    padding: 18px 20px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--bg-card);
    margin-bottom: 14px;
}
.card h3 {
    margin-top: 0;
    font-size: 1rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 600;
}

/* Stat chips */
.stats { display:flex; flex-wrap:wrap; gap:10px; }
.chip {
    display:inline-flex; align-items:center; gap:8px;
    padding: 8px 14px; border-radius:999px;
    background: var(--bg-card); border:1px solid var(--border);
    font-size:0.85rem; color:#eaeaf0;
}
.chip b { color:#fff; font-weight:700; }

/* Buttons */
.stButton > button, .stDownloadButton > button {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    transition: transform 0.06s ease, background 0.15s ease, border 0.15s ease;
    font-weight: 600 !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(124,58,237,0.5) !important;
}
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 6px 18px rgba(124,58,237,0.35);
}

/* Inputs */
[data-baseweb="input"] > div, [data-baseweb="select"] > div {
    border-radius: 10px !important;
}

/* Dataframe rounded */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}

/* Progress bar color */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
}

/* Expander */
.streamlit-expanderHeader {
    border-radius: 10px !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 14px;
    border-radius: 10px;
    background: var(--bg-card);
    border: 1px solid var(--border);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(124,58,237,0.35), rgba(236,72,153,0.25)) !important;
    border-color: rgba(124,58,237,0.5) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.45); border-radius: 10px; }
::-webkit-scrollbar-track { background: transparent; }

/* Footer */
.footnote {
    text-align:center; color:var(--muted); font-size:0.82rem;
    padding: 14px 0 4px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "playlist_url": "",
        "playlist": None,
        "selected_ids": [],
        "zip_data": None,
        "zip_name": None,
        "last_error": None,
        "download_log": [],  # list of dicts: title, status, ts
        "search_query": "",
        "sort_option": "Playlist order",
        "audio_format": "mp3",
        "audio_quality": "192",
        "embed_metadata": True,
        "embed_thumbnail": True,
        "parse_artist_title": True,
        "album_from_playlist": True,
        "cookies_content": None,   # text of a Netscape cookies.txt file
        "cookies_name": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def sanitize_name(value: str) -> str:
    cleaned = INVALID_CHARS.sub("_", value or "playlist")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:120] or "playlist"


def is_valid_playlist_url(url: str) -> bool:
    patterns = [
        r"youtube\.com/playlist\?list=",
        r"youtube\.com/watch\?.*list=",
        r"youtu\.be/.*list=",
        r"music\.youtube\.com/playlist\?list=",
        r"music\.youtube\.com/watch\?.*list=",
    ]
    return any(re.search(p, url or "", flags=re.IGNORECASE) for p in patterns)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def seconds_to_hhmmss(seconds) -> str:
    value = int(seconds or 0)
    if value <= 0:
        return "--:--"
    h = value // 3600
    m = (value % 3600) // 60
    s = value % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def humanize_bytes(num: float) -> str:
    if not num or num <= 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def estimate_size_mb(duration_s: int, kbps: int) -> float:
    # Rough: bitrate * seconds / 8 -> bytes
    return max(0.0, (kbps * 1000 * max(0, duration_s)) / 8 / (1024 * 1024))


def _common_network_opts(cookies_path: str | None = None) -> dict:
    """Options that make yt-dlp more likely to succeed from a cloud IP."""
    opts = {
        # A real-browser UA helps with YouTube bot detection.
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        # Prefer the Android + web clients — Android often bypasses PO-token checks.
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }
    if cookies_path:
        opts["cookiefile"] = cookies_path
    return opts


def _write_cookies_tempfile() -> str | None:
    """If the user uploaded a cookies.txt, write it to a temp file and return the path."""
    content = st.session_state.get("cookies_content")
    if not content:
        return None
    fd, path = tempfile.mkstemp(prefix="yt_cookies_", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def fetch_playlist(url: str):
    cookies_path = _write_cookies_tempfile()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        **_common_network_opts(cookies_path),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    finally:
        if cookies_path and os.path.exists(cookies_path):
            try:
                os.remove(cookies_path)
            except OSError:
                pass

    entries = []
    for idx, entry in enumerate(info.get("entries", []) or [], start=1):
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id:
            continue
        entries.append(
            {
                "id": video_id,
                "index": idx,
                "title": entry.get("title") or f"Video {idx}",
                "duration": entry.get("duration") or 0,
                "uploader": entry.get("uploader") or entry.get("channel") or "",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )

    if not entries:
        raise RuntimeError("No videos found. The playlist may be private, empty, or unavailable.")

    return {
        "title": info.get("title") or "Unknown Playlist",
        "uploader": info.get("uploader") or info.get("channel") or "Unknown",
        "entries": entries,
    }


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------
def build_zip_from_selection(
    playlist_title,
    selected_entries,
    audio_format,
    audio_quality,
    embed_metadata=True,
    embed_thumbnail=True,
    parse_artist_title=True,
    album_from_playlist=True,
):
    root_tmp = tempfile.mkdtemp(prefix="yt_playlist_")
    audio_dir = os.path.join(root_tmp, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    st.markdown("#### Progress")
    progress = st.progress(0.0)
    status = st.empty()
    eta_box = st.empty()

    total = len(selected_entries)
    completed = 0
    current_title = {"name": ""}
    start_time = time.time()

    def progress_hook(event):
        nonlocal completed
        if event.get("status") == "downloading":
            info_dict = event.get("info_dict") or {}
            title = info_dict.get("title") or current_title["name"]
            current_title["name"] = title
            downloaded = event.get("downloaded_bytes") or 0
            total_bytes = event.get("total_bytes") or event.get("total_bytes_estimate") or 0
            speed = event.get("speed") or 0
            pct_file = (downloaded / total_bytes) if total_bytes else 0
            overall = (completed + pct_file) / max(total, 1)
            progress.progress(min(overall, 1.0))
            speed_txt = f"{humanize_bytes(speed)}/s" if speed else ""
            status.info(
                f"⬇️  **{completed + 1}/{total}** — {title[:80]}  "
                f"&nbsp;·&nbsp; {humanize_bytes(downloaded)} / {humanize_bytes(total_bytes)}  "
                f"&nbsp;·&nbsp; {speed_txt}"
            )
        elif event.get("status") == "finished":
            completed += 1
            elapsed = max(time.time() - start_time, 0.01)
            rate = completed / elapsed
            remaining = (total - completed) / rate if rate > 0 else 0
            eta_box.caption(
                f"✓ Finished {completed}/{total}  ·  elapsed {seconds_to_hhmmss(int(elapsed))}  "
                f"·  ETA {seconds_to_hhmmss(int(remaining))}"
            )
            progress.progress(min(completed / max(total, 1), 1.0))

    # Thumbnail embedding is supported by mp3, m4a, opus, flac — not wav.
    supports_thumbnail = audio_format in ("mp3", "m4a", "opus", "flac")
    # Metadata embedding is supported by everything except wav in any reliable way.
    supports_metadata = audio_format != "wav"

    postprocessors = []

    # --- PRE-PROCESS: parse real metadata out of the YouTube title ---------
    # The YouTube title is usually "Artist - Song (Official Video)".
    # We split it, then clean common suffixes, then fall back to the channel
    # name if no "Artist - " prefix was present.
    if parse_artist_title:
        postprocessors.append({
            "key": "MetadataParser",
            "when": "pre_process",
            "actions": [
                # "Artist - Title"  /  "Artist – Title"  /  "Artist — Title"
                (MetadataParserPP.interpretter, "title",
                 r"^\s*(?P<artist>[^-–—]+?)\s*[-–—]\s*(?P<title>.+?)\s*$"),
                # Strip trailing "(Official Video)", "[Lyrics]", "(Audio)", "(HD)", etc.
                (MetadataParserPP.interpretter, "title",
                 r"^(?P<title>.+?)\s*[\(\[][^\)\]]*?(?:official|lyrics?|audio|video|hd|hq|4k|mv|visualizer|music\s*video|clip)[^\)\]]*[\)\]]\s*$"),
                # Drop the "- Topic" suffix from YouTube Music channels.
                (MetadataParserPP.interpretter, "uploader",
                 r"^\s*(?P<uploader>.+?)(?:\s*-\s*Topic)?\s*$"),
            ],
        })

        # Fallback: if artist is still empty after parsing, copy it from the
        # uploader (channel name). `%(…|…)s` uses the first non-empty field,
        # with an empty default after the `|`.
        postprocessors.append({
            "key": "MetadataParser",
            "when": "pre_process",
            "actions": [
                (MetadataParserPP.interpretter,
                 "%(artist,uploader|)s", r"(?P<artist>.+)"),
            ],
        })

    # Force the album field to the playlist name.
    if album_from_playlist:
        postprocessors.append({
            "key": "MetadataParser",
            "when": "pre_process",
            "actions": [
                (MetadataParserPP.interpretter,
                 "%(playlist,playlist_title|)s", r"(?P<album>.+)"),
            ],
        })

    # --- Convert the audio stream ------------------------------------------
    if audio_format in ("mp3", "m4a", "opus"):
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": audio_quality,
        })
    elif audio_format == "flac":
        postprocessors.append({"key": "FFmpegExtractAudio", "preferredcodec": "flac", "preferredquality": "0"})
    elif audio_format == "wav":
        postprocessors.append({"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "0"})

    # --- Write ID3 / MP4 / Vorbis tags into the file -----------------------
    if embed_metadata and supports_metadata:
        postprocessors.append({
            "key": "FFmpegMetadata",
            "add_metadata": True,
            "add_chapters": False,
        })

    # --- Embed the cover art ------------------------------------------------
    if embed_thumbnail and supports_thumbnail:
        # Normalize whatever format the thumbnail came in (webp, etc.) to jpg
        # so embedding works reliably across players (including Android).
        postprocessors.append({
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg",
            "when": "before_dl",
        })
        postprocessors.append({
            "key": "EmbedThumbnail",
            "already_have_thumbnail": False,
        })

    # Output template: "Artist - Title.ext", with safe fallbacks. Using
    # restrictfilenames=False keeps spaces; we just rely on yt-dlp to strip
    # characters that are illegal on the current filesystem.
    if parse_artist_title:
        out_template = "%(artist,uploader|Unknown Artist)s - %(title)s.%(ext)s"
    else:
        out_template = "%(title)s.%(ext)s"

    cookies_path = _write_cookies_tempfile()
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "outtmpl": os.path.join(audio_dir, out_template),
        "windowsfilenames": True,   # ensure the filename is valid on Windows
        "postprocessors": postprocessors,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
        # IMPORTANT: don't swallow errors silently — we want to show them.
        "ignoreerrors": False,
        "retries": 5,
        "fragment_retries": 5,
        # Needed for EmbedThumbnail — fetch the thumbnail alongside the audio.
        "writethumbnail": bool(embed_thumbnail and supports_thumbnail),
        **_common_network_opts(cookies_path),
    }

    results_log = []
    errors = []  # (title, error_message)
    try:
        status.info("Starting download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for entry in selected_entries:
                try:
                    ydl.download([entry["url"]])
                    results_log.append({
                        "title": entry["title"], "status": "ok",
                        "ts": datetime.now().strftime("%H:%M:%S"),
                    })
                except Exception as exc:
                    msg = str(exc)
                    errors.append((entry["title"], msg))
                    results_log.append({
                        "title": entry["title"], "status": f"error: {msg}",
                        "ts": datetime.now().strftime("%H:%M:%S"),
                    })
                    # Surface the failure live so the user sees what happened.
                    st.warning(f"❌ **{entry['title']}** — {msg[:220]}")

        # What actually landed on disk?
        audio_exts = (".mp3", ".m4a", ".opus", ".flac", ".wav")
        files = [f for f in sorted(os.listdir(audio_dir)) if f.lower().endswith(audio_exts)]

        if not files:
            # No audio at all — give the user a useful diagnosis.
            hint = _diagnose_failure(errors)
            raise RuntimeError(
                f"No files were downloaded ({len(errors)} error(s)).\n\n{hint}"
            )

        zip_name = f"{sanitize_name(playlist_title)}.zip"
        zip_path = os.path.join(root_tmp, zip_name)

        status.info("Packaging ZIP...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as zipf:
            for file_name in files:
                source_path = os.path.join(audio_dir, file_name)
                zipf.write(source_path, arcname=file_name)

        with open(zip_path, "rb") as f:
            zip_data = f.read()

        progress.progress(1.0)
        if errors:
            status.warning(f"Done — {len(files)} ok, {len(errors)} failed. ZIP is ready below.")
        else:
            status.success(f"Done — {len(files)} track(s) packaged. ZIP is ready below.")
        st.session_state.download_log = results_log + st.session_state.download_log
        return zip_name, zip_data
    finally:
        shutil.rmtree(root_tmp, ignore_errors=True)
        if cookies_path and os.path.exists(cookies_path):
            try:
                os.remove(cookies_path)
            except OSError:
                pass


def _diagnose_failure(errors: list[tuple[str, str]]) -> str:
    """Turn raw yt-dlp error text into actionable guidance."""
    if not errors:
        return "Unknown failure — check the Streamlit logs."
    joined = " | ".join(e[1] for e in errors).lower()
    if "sign in to confirm" in joined or "not a bot" in joined or "cookies" in joined:
        return (
            "YouTube is blocking the Streamlit Cloud server with a **bot check**. "
            "Upload a `cookies.txt` exported from your logged-in browser in the "
            "sidebar (Tags & Cover → Cookies) and try again."
        )

    if "http error 403" in joined or "forbidden" in joined:
        return (
            "YouTube returned **HTTP 403**. The cloud IP is throttled or flagged. "
            "Upload a `cookies.txt` from your browser in the sidebar to authenticate."
        )
    if "video unavailable" in joined or "private video" in joined or "members-only" in joined:
        return "Some videos are private, region-locked, or members-only."
    if "ffmpeg" in joined:
        return (
            "FFmpeg error. On Streamlit Cloud, make sure `packages.txt` contains "
            "`ffmpeg` and reboot the app."
        )
    return f"First error was: {errors[0][1][:300]}"


# ---------------------------------------------------------------------------
# UI blocks
# ---------------------------------------------------------------------------
def render_hero():
    status_line = "Ready" if ffmpeg_available() else "FFmpeg missing"
    st.markdown(
        f"""
        <div class="hero">
            <h1>🎧 Playlist Studio</h1>
            <p><span class="dot"></span><b>{status_line}</b> · Convert YouTube playlists into clean, tagged audio archives</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        st.session_state.audio_format = st.selectbox(
            "Audio format",
            options=["mp3", "m4a", "opus", "flac", "wav"],
            index=["mp3", "m4a", "opus", "flac", "wav"].index(st.session_state.audio_format),
            help="MP3 is universal. FLAC/WAV are lossless but much larger.",
        )

        quality_disabled = st.session_state.audio_format in ("flac", "wav")
        st.session_state.audio_quality = st.select_slider(
            "Bitrate (kbps)",
            options=["96", "128", "160", "192", "256", "320"],
            value=st.session_state.audio_quality,
            disabled=quality_disabled,
            help="Higher = better quality, bigger files. 192 is a good balance.",
        )
        if quality_disabled:
            st.caption("Bitrate unused for lossless formats.")

        st.markdown("---")
        st.markdown("### 🏷️ Tags & Cover")
        st.session_state.embed_metadata = st.toggle(
            "Embed metadata (artist, title, album…)",
            value=st.session_state.embed_metadata,
            help="Writes ID3 / MP4 / Vorbis tags into the audio file.",
        )
        st.session_state.embed_thumbnail = st.toggle(
            "Embed cover art (thumbnail)",
            value=st.session_state.embed_thumbnail,
            help="Embeds the YouTube thumbnail as album art. Not supported on WAV.",
        )
        st.session_state.parse_artist_title = st.toggle(
            "Auto-detect artist from title",
            value=st.session_state.parse_artist_title,
            help='Splits "Artist - Title" patterns and cleans "[Official Video]" suffixes. Falls back to the channel name.',
        )
        st.session_state.album_from_playlist = st.toggle(
            "Use playlist name as album",
            value=st.session_state.album_from_playlist,
        )
        if st.session_state.audio_format == "wav" and (
            st.session_state.embed_metadata or st.session_state.embed_thumbnail
        ):
            st.caption("⚠️ WAV has limited/no support for tags and cover art.")

        st.markdown("---")
        st.markdown("### 🔑 Cookies (for cloud hosting)")
        st.caption(
            "If you're running this on Streamlit Cloud / a VPS and YouTube says "
            "\"sign in to confirm you're not a bot\", upload a `cookies.txt` "
            "exported from your **logged-in** browser."
        )
        uploaded = st.file_uploader(
            "cookies.txt (Netscape format)",
            type=["txt"],
            key="cookies_upload",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                st.session_state.cookies_content = uploaded.read().decode("utf-8", errors="replace")
                st.session_state.cookies_name = uploaded.name
            except Exception as exc:
                st.error(f"Could not read cookies file: {exc}")
        if st.session_state.cookies_content:
            c1, c2 = st.columns([3, 1])
            c1.success(f"✓ Using `{st.session_state.cookies_name or 'cookies.txt'}`")
            if c2.button("Clear", key="clear_cookies"):
                st.session_state.cookies_content = None
                st.session_state.cookies_name = None
                st.rerun()
        with st.expander("How to export cookies.txt"):
            st.markdown(
                "1. Install the **Get cookies.txt LOCALLY** browser extension "
                "([Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) / "
                "[Firefox](https://addons.mozilla.org/firefox/addon/cookies-txt/)).\n"
                "2. Open **youtube.com** while logged in.\n"
                "3. Click the extension → **Export** → save `cookies.txt`.\n"
                "4. Upload it here. Cookies stay in this session only."
            )

        st.markdown("---")
        st.markdown("### 🩺 System")
        ff = ffmpeg_available()
        st.markdown(
            f"- FFmpeg: {'✅ detected' if ff else '❌ not found'}\n"
            f"- yt-dlp: ✅ loaded"
        )
        if not ff:
            with st.expander("How to install FFmpeg"):
                st.code(
                    "# Windows (choco)\nchoco install ffmpeg\n\n"
                    "# macOS\nbrew install ffmpeg\n\n"
                    "# Ubuntu / Debian\nsudo apt install -y ffmpeg",
                    language="bash",
                )

        st.markdown("---")
        with st.expander("📜 Recent activity", expanded=False):
            log = st.session_state.download_log[:20]
            if not log:
                st.caption("No downloads yet.")
            else:
                for item in log:
                    icon = "✓" if item["status"] == "ok" else "✗"
                    st.caption(f"{icon} [{item['ts']}] {item['title'][:60]}")

        st.markdown("---")
        st.caption("Respect YouTube's Terms and local copyright laws.")


def render_stats(playlist, selected_ids, audio_quality):
    entries = playlist["entries"]
    total_dur = sum(e["duration"] or 0 for e in entries)
    sel_entries = [e for e in entries if e["id"] in set(selected_ids)]
    sel_dur = sum(e["duration"] or 0 for e in sel_entries)
    try:
        kbps = int(audio_quality)
    except ValueError:
        kbps = 192
    est_mb = sum(estimate_size_mb(e["duration"] or 0, kbps) for e in sel_entries)

    st.markdown(
        f"""
        <div class="stats">
            <div class="chip">🎶 <b>{len(entries)}</b> videos</div>
            <div class="chip">✅ <b>{len(sel_entries)}</b> selected</div>
            <div class="chip">⏱ Total <b>{seconds_to_hhmmss(total_dur)}</b></div>
            <div class="chip">⏱ Selected <b>{seconds_to_hhmmss(sel_dur)}</b></div>
            <div class="chip">📦 Est. size <b>~{est_mb:.0f} MB</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_playlist_section(playlist):
    entries = playlist["entries"]

    tabs = st.tabs(["🎵 Tracks", "🎯 Selection", "📊 Stats"])

    # --- Tracks tab ---
    with tabs[0]:
        c1, c2 = st.columns([3, 2])
        with c1:
            st.session_state.search_query = st.text_input(
                "Search titles",
                value=st.session_state.search_query,
                placeholder="Filter by keyword…",
                label_visibility="collapsed",
            )
        with c2:
            st.session_state.sort_option = st.selectbox(
                "Sort",
                options=["Playlist order", "Title A→Z", "Title Z→A", "Duration ↑", "Duration ↓"],
                index=["Playlist order", "Title A→Z", "Title Z→A", "Duration ↑", "Duration ↓"].index(
                    st.session_state.sort_option
                ),
                label_visibility="collapsed",
            )

        visible = list(entries)
        q = (st.session_state.search_query or "").strip().lower()
        if q:
            visible = [e for e in visible if q in e["title"].lower() or q in (e.get("uploader") or "").lower()]

        sort_opt = st.session_state.sort_option
        if sort_opt == "Title A→Z":
            visible.sort(key=lambda e: e["title"].lower())
        elif sort_opt == "Title Z→A":
            visible.sort(key=lambda e: e["title"].lower(), reverse=True)
        elif sort_opt == "Duration ↑":
            visible.sort(key=lambda e: e["duration"] or 0)
        elif sort_opt == "Duration ↓":
            visible.sort(key=lambda e: e["duration"] or 0, reverse=True)

        rows = [
            {
                "#": e["index"],
                "Title": e["title"],
                "Uploader": e.get("uploader") or "—",
                "Duration": seconds_to_hhmmss(e["duration"]),
            }
            for e in visible
        ]
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True, height=min(520, 52 + 35 * len(rows)))
        else:
            st.info("No tracks match your filter.")

    # --- Selection tab ---
    with tabs[1]:
        bc1, bc2, bc3, bc4 = st.columns(4)
        if bc1.button("Select all", use_container_width=True):
            st.session_state.selected_ids = [e["id"] for e in entries]
        if bc2.button("Clear", use_container_width=True):
            st.session_state.selected_ids = []
        if bc3.button("Invert", use_container_width=True):
            s = set(st.session_state.selected_ids)
            st.session_state.selected_ids = [e["id"] for e in entries if e["id"] not in s]
        if bc4.button("First 10", use_container_width=True):
            st.session_state.selected_ids = [e["id"] for e in entries[:10]]

        labels = {
            e["id"]: f"{e['index']:02d} · {e['title']}  ({seconds_to_hhmmss(e['duration'])})"
            for e in entries
        }
        default_selected = [sid for sid in st.session_state.selected_ids if sid in labels]

        selected = st.multiselect(
            "Pick videos to include",
            options=[e["id"] for e in entries],
            default=default_selected,
            format_func=lambda item_id: labels.get(item_id, item_id),
        )
        st.session_state.selected_ids = selected

    # --- Stats tab ---
    with tabs[2]:
        render_stats(playlist, st.session_state.selected_ids, st.session_state.audio_quality)
        st.caption("Size estimates are approximate; real values depend on source streams.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    init_state()
    render_hero()
    render_sidebar()

    if not ffmpeg_available():
        st.error(
            "**FFmpeg was not found in PATH.** Install it and restart the app. "
            "See the sidebar for platform-specific commands."
        )
        st.stop()

    # URL entry card
    with st.container():
        st.markdown('<div class="card"><h3>1 · Playlist URL</h3>', unsafe_allow_html=True)
        with st.form("playlist_form", clear_on_submit=False):
            col_in, col_btn = st.columns([5, 1])
            with col_in:
                playlist_url = st.text_input(
                    "Playlist URL",
                    value=st.session_state.playlist_url,
                    placeholder="https://www.youtube.com/playlist?list=…",
                    label_visibility="collapsed",
                )
            with col_btn:
                fetch_clicked = st.form_submit_button(
                    "Fetch", type="primary", use_container_width=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

    if fetch_clicked:
        st.session_state.last_error = None
        st.session_state.zip_data = None
        st.session_state.zip_name = None
        st.session_state.playlist_url = (playlist_url or "").strip()

        if not is_valid_playlist_url(st.session_state.playlist_url):
            st.session_state.playlist = None
            st.session_state.selected_ids = []
            st.session_state.last_error = (
                "Invalid playlist URL. Make sure it contains the `list=` parameter "
                "(e.g. https://www.youtube.com/playlist?list=…)."
            )
        else:
            try:
                with st.spinner("Fetching playlist metadata…"):
                    playlist = fetch_playlist(st.session_state.playlist_url)
                st.session_state.playlist = playlist
                st.session_state.selected_ids = [e["id"] for e in playlist["entries"]]
            except Exception as exc:
                st.session_state.playlist = None
                st.session_state.selected_ids = []
                st.session_state.last_error = str(exc)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)
        with st.expander("Troubleshooting"):
            st.markdown(
                "- Confirm the playlist is **public** or **unlisted**.\n"
                "- Verify the URL contains `list=…`.\n"
                "- Some region-locked / age-restricted playlists cannot be fetched.\n"
                "- Try updating yt-dlp: `pip install -U yt-dlp`."
            )

    playlist = st.session_state.playlist
    if playlist:
        # Playlist header card
        st.markdown(
            f"""
            <div class="card">
                <h3>2 · Playlist</h3>
                <div style="font-size:1.15rem; font-weight:700;">{playlist['title']}</div>
                <div style="color:var(--muted); font-size:0.9rem;">
                    by {playlist['uploader']} · {len(playlist['entries'])} videos
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="card"><h3>3 · Select tracks</h3>', unsafe_allow_html=True)
        render_playlist_section(playlist)
        st.markdown("</div>", unsafe_allow_html=True)

        selected_entries = [e for e in playlist["entries"] if e["id"] in set(st.session_state.selected_ids)]

        # Action card
        st.markdown('<div class="card"><h3>4 · Download</h3>', unsafe_allow_html=True)
        render_stats(playlist, st.session_state.selected_ids, st.session_state.audio_quality)
        st.write("")

        cta = st.button(
            f"⬇️ Download {len(selected_entries)} track{'s' if len(selected_entries) != 1 else ''} as "
            f"{st.session_state.audio_format.upper()} ZIP",
            type="primary",
            use_container_width=True,
            disabled=len(selected_entries) == 0,
        )
        if cta:
            if not selected_entries:
                st.warning("Select at least one video.")
            else:
                try:
                    zip_name, zip_data = build_zip_from_selection(
                        playlist["title"],
                        selected_entries,
                        st.session_state.audio_format,
                        st.session_state.audio_quality,
                        embed_metadata=st.session_state.embed_metadata,
                        embed_thumbnail=st.session_state.embed_thumbnail,
                        parse_artist_title=st.session_state.parse_artist_title,
                        album_from_playlist=st.session_state.album_from_playlist,
                    )
                    st.session_state.zip_name = zip_name
                    st.session_state.zip_data = zip_data
                    st.balloons()
                except Exception as exc:
                    st.error(f"Download failed: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.zip_data and st.session_state.zip_name:
        st.markdown('<div class="card"><h3>5 · Your archive</h3>', unsafe_allow_html=True)
        size_txt = humanize_bytes(len(st.session_state.zip_data))
        st.markdown(
            f"**{st.session_state.zip_name}** · {size_txt} · ready to save"
        )
        st.download_button(
            label=f"Save ZIP ({size_txt})",
            data=st.session_state.zip_data,
            file_name=st.session_state.zip_name,
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="footnote">Built with Streamlit · yt-dlp · FFmpeg — lightweight by design</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
