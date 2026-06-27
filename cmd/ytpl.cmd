@echo off & python -x "%~f0" %* & exit /b
# --- Python starts here ---
import argparse
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Enable ANSI on Windows ────────────────────────────────────────────────────
os.system("")

try:
    import yt_dlp
    from yt_dlp.postprocessor import MetadataParserPP
except ImportError:
    print("\n  \033[31mERROR\033[0m  yt-dlp is not installed.")
    print("         Run: \033[36mpip install yt-dlp\033[0m\n")
    sys.exit(1)

# ── Colour palette ────────────────────────────────────────────────────────────
R  = "\033[0m"          # reset
B  = "\033[1m"          # bold
DIM= "\033[2m"          # dim
PU = "\033[38;5;135m"   # purple
CY = "\033[38;5;51m"    # cyan
GR = "\033[38;5;83m"    # green
RD = "\033[38;5;203m"   # red
YL = "\033[38;5;220m"   # yellow
WH = "\033[97m"         # bright white
MU = "\033[38;5;177m"   # mauve (light purple)

W = 58   # box inner width

# ── Helpers ───────────────────────────────────────────────────────────────────
INVALID_CHARS   = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
PLAYER_FALLBACKS = [["ios"], ["tv_embedded"], ["mweb"], ["web"]]
_lock = threading.Lock()


def sanitize(name):
    c = INVALID_CHARS.sub("_", name or "playlist")
    c = re.sub(r"\s+", " ", c).strip()
    return c[:120] or "playlist"

def fmt_bytes(n):
    if not n or n <= 0: return "—"
    for u in ("B","KB","MB","GB"):
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def fmt_time(s):
    s = max(0, int(s or 0))
    h, r = divmod(s, 3600); m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def ffmpeg_ok():    return shutil.which("ffmpeg") is not None
def is_playlist(u): return bool(re.search(r"list=", u or "", re.I))

def tprint(*a, **k):
    with _lock: print(*a, **k)

class _Silent:
    def debug(self,m): pass
    def info(self,m):  pass
    def warning(self,m): pass
    def error(self,m): pass

# ── Box drawing ───────────────────────────────────────────────────────────────
def box_top(label=""):
    if label:
        pad = W - len(label) - 2
        return f"{PU}  ╭─ {WH}{B}{label}{R}{PU} {'─'*pad}╮{R}"
    return f"{PU}  ╭{'─'*W}╮{R}"

def box_bot():
    return f"{PU}  ╰{'─'*W}╯{R}"

def box_row(text="", color=""):
    inner = f"{color}{text}{R}" if color else text
    # strip ANSI for length calculation
    visible = re.sub(r'\033\[[^m]*m', '', text)
    pad = W - len(visible)
    return f"{PU}  │{R} {inner}{' '*max(pad-1,0)}{PU}│{R}"

def box_div():
    return f"{PU}  ├{'─'*W}┤{R}"

def banner():
    print()
    print(f"{PU}  ╭{'─'*W}╮{R}")
    print(box_row())
    title = f"{B}{WH}◈  ytpl{R}  {DIM}─  YouTube Playlist Downloader{R}"
    print(box_row(title))
    print(box_row())
    print(box_bot())
    print()

def section(label):
    print()
    print(f"  {PU}┄┄┄{R}  {MU}{B}{label}{R}")
    print()

# ── yt-dlp network options ────────────────────────────────────────────────────
def net_opts(cookies_path=None, clients=None):
    o = {
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {"youtube": {"player_client": clients or ["ios","tv_embedded","web"]}},
        "concurrent_fragment_downloads": 4,
        "socket_timeout": 30,
    }
    if cookies_path: o["cookiefile"] = cookies_path
    return o

# ── Fetch playlist ────────────────────────────────────────────────────────────
def fetch_playlist(url, cookies_path=None):
    last_exc = None
    for clients in PLAYER_FALLBACKS:
        try:
            with yt_dlp.YoutubeDL({"quiet":True,"no_warnings":True,"extract_flat":True,
                                    "skip_download":True,"logger":_Silent(),
                                    **net_opts(cookies_path, clients)}) as ydl:
                info = ydl.extract_info(url, download=False)
            break
        except Exception as e: last_exc = e; continue
    else:
        raise last_exc or RuntimeError("Could not fetch playlist.")

    entries = []
    for i, e in enumerate(info.get("entries") or [], 1):
        if not e or not e.get("id"): continue
        entries.append({"id":e["id"],"index":i,
                        "title":e.get("title") or f"Video {i}",
                        "duration":e.get("duration") or 0,
                        "uploader":e.get("uploader") or e.get("channel") or "",
                        "url":f"https://www.youtube.com/watch?v={e['id']}"})
    if not entries:
        raise RuntimeError("No videos found — playlist may be private or empty.")
    return {"title":info.get("title") or "Unknown Playlist",
            "uploader":info.get("uploader") or info.get("channel") or "Unknown",
            "entries":entries}

# ── Postprocessors ────────────────────────────────────────────────────────────
def build_pp(fmt, quality, meta, thumb, parse_title):
    supports_thumb = fmt in ("mp3","m4a","opus","flac")
    supports_meta  = fmt != "wav"
    pp = []
    if parse_title:
        pp.append({"key":"MetadataParser","when":"pre_process","actions":[
            (MetadataParserPP.interpretter,"title",
             r"^\s*(?P<artist>[^-–—]+?)\s*[-–—]\s*(?P<title>.+?)\s*$"),
            (MetadataParserPP.interpretter,"title",
             r"^(?P<title>.+?)\s*[\(\[][^\)\]]*?(?:official|lyrics?|audio|video|hd|hq|4k|mv|visualizer|music\s*video|clip)[^\)\]]*[\)\]]\s*$"),
            (MetadataParserPP.interpretter,"uploader",
             r"^\s*(?P<uploader>.+?)(?:\s*-\s*Topic)?\s*$"),
        ]})
        pp.append({"key":"MetadataParser","when":"pre_process","actions":[
            (MetadataParserPP.interpretter,"%(artist,uploader|)s",r"(?P<artist>.+)")]})
    pp.append({"key":"MetadataParser","when":"pre_process","actions":[
        (MetadataParserPP.interpretter,"%(playlist,playlist_title|)s",r"(?P<album>.+)")]})
    if fmt in ("mp3","m4a","opus"):
        pp.append({"key":"FFmpegExtractAudio","preferredcodec":fmt,"preferredquality":quality})
    else:
        pp.append({"key":"FFmpegExtractAudio","preferredcodec":fmt,"preferredquality":"0"})
    if meta and supports_meta:
        pp.append({"key":"FFmpegMetadata","add_metadata":True,"add_chapters":False})
    if thumb and supports_thumb:
        pp.append({"key":"FFmpegThumbnailsConvertor","format":"jpg","when":"before_dl"})
        pp.append({"key":"EmbedThumbnail","already_have_thumbnail":False})
    return pp, supports_thumb

# ── Download one track ────────────────────────────────────────────────────────
def download_one(entry, out_dir, pp, supports_thumb, fmt, quality,
                 thumb, parse_title, cookies_path, counter, total, start_t):
    out_tpl = ("%(artist,uploader|Unknown Artist)s - %(title)s.%(ext)s"
               if parse_title else "%(title)s.%(ext)s")

    def make_opts(clients):
        return {"format":"bestaudio*/best","quiet":True,"no_warnings":True,
                "logger":_Silent(),
                "outtmpl":os.path.join(out_dir, out_tpl),
                "windowsfilenames":True,"postprocessors":pp,"noplaylist":True,
                "ignoreerrors":False,"retries":3,"fragment_retries":3,
                "writethumbnail":bool(thumb and supports_thumb),
                **net_opts(cookies_path, clients)}

    for clients in PLAYER_FALLBACKS:
        try:
            with yt_dlp.YoutubeDL(make_opts(clients)) as ydl:
                ydl.download([entry["url"]])
            with _lock:
                counter["done"] += 1
                n = counter["done"]
                elapsed = max(time.time() - start_t, 0.01)
                eta = (total - n) / (n / elapsed) if n else 0
                w = len(str(total))
                short = entry["title"][:52]
                print(f"  {DIM}[{n:>{w}}/{total}]{R}  {GR}✓{R}  {WH}{short:<52}{R}  "
                      f"{DIM}{fmt_time(int(elapsed))} · ETA {fmt_time(int(eta))}{R}")
            return True
        except Exception as e:
            last_exc = e
            continue

    with _lock:
        counter["done"] += 1
        w = len(str(total))
        short = entry["title"][:52]
        print(f"  {DIM}[{counter['done']:>{w}}/{total}]{R}  {RD}✗{R}  {DIM}{short}{R}")
        print(f"  {' '*(w*2+5)}  {RD}{str(last_exc)[:70]}{R}")
    return False

# ── Parallel downloader ───────────────────────────────────────────────────────
def download_playlist(playlist, out_dir, fmt="mp3", quality="192",
                      meta=True, thumb=True, parse_title=True,
                      cookies_path=None, workers=4):
    os.makedirs(out_dir, exist_ok=True)
    pp, supports_thumb = build_pp(fmt, quality, meta, thumb, parse_title)
    entries = playlist["entries"]
    total   = len(entries)
    start_t = time.time()
    counter = {"done": 0}
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(download_one, e, out_dir, pp, supports_thumb,
                        fmt, quality, thumb, parse_title, cookies_path,
                        counter, total, start_t): e
            for e in entries
        }
        for f in as_completed(futures):
            if f.result(): ok += 1
            else:          fail += 1
    return ok, fail

# ── Prompt ───────────────────────────────────────────────────────────────────
def ask(prompt, default=None, color=CY):
    marker = f"{PU}  ›{R} "
    if default:
        sys.stdout.write(f"{marker}{color}{prompt}{R}  {DIM}[{default}]{R}  ")
    else:
        sys.stdout.write(f"{marker}{color}{prompt}{R}  ")
    sys.stdout.flush()
    val = input().strip()
    return val or default or ""

def prompt_config():
    banner()

    # Check ffmpeg here so banner shows first
    if not ffmpeg_ok():
        print(f"  {RD}✗  ffmpeg not found in PATH.{R}")
        print(f"     {DIM}Windows: choco install ffmpeg{R}")
        print(f"     {DIM}macOS:   brew install ffmpeg{R}")
        print(f"     {DIM}Linux:   sudo apt install -y ffmpeg{R}\n")
        sys.exit(1)

    section("Playlist")
    while True:
        url = ask("Paste playlist URL")
        if not url:
            print(f"\n  {DIM}No URL — exiting.{R}\n"); sys.exit(0)
        if is_playlist(url): break
        print(f"  {RD}  ✗  Needs a list= parameter. Try again.{R}\n")

    section("Settings")
    fmt_map  = {"1":"mp3","2":"m4a","3":"opus","4":"flac","5":"wav"}
    qual_map = {"1":"96","2":"128","3":"160","4":"192","5":"256","6":"320"}

    print(f"  {DIM}  Format   :{R}  {WH}1{R} mp3  {WH}2{R} m4a  {WH}3{R} opus  {WH}4{R} flac  {WH}5{R} wav")
    fmt = fmt_map.get(ask("Choice", "1"), "mp3")

    if fmt not in ("flac","wav"):
        print(f"  {DIM}  Quality  :{R}  {WH}1{R} 96  {WH}2{R} 128  {WH}3{R} 160  {WH}4{R} 192  {WH}5{R} 256  {WH}6{R} 320 kbps")
        quality = qual_map.get(ask("Choice", "4"), "192")
    else:
        quality = "0"

    print(f"  {DIM}  Workers  :{R}  1 – 8   {DIM}(4 = safe · 6–8 = fast fibre){R}")
    w_in = ask("Workers", "4")
    workers = max(1, min(8, int(w_in) if w_in.isdigit() else 4))

    default_out = os.path.expanduser("~/Music")
    out = ask("Output folder", default_out)
    out_dir_base = os.path.expanduser(out)

    ck = ask("cookies.txt path  (blank to skip)", "")
    cookies_path = os.path.expanduser(ck) if ck else None
    if cookies_path and not os.path.isfile(cookies_path):
        print(f"  {YL}  ⚠  cookies file not found — skipping{R}")
        cookies_path = None

    print()
    return url, fmt, quality, workers, out_dir_base, cookies_path

# ── Arg parse ─────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(prog="ytpl")
    p.add_argument("url", nargs="?", default=None)
    p.add_argument("-f","--format",  default="mp3", choices=["mp3","m4a","opus","flac","wav"])
    p.add_argument("-q","--quality", default="192", choices=["96","128","160","192","256","320"])
    p.add_argument("-w","--workers", default=4, type=int)
    p.add_argument("-o","--output",  default=None)
    p.add_argument("--no-metadata",  action="store_true")
    p.add_argument("--no-thumbnail", action="store_true")
    p.add_argument("--no-parse",     action="store_true")
    p.add_argument("--cookies",      default=None)
    return p.parse_args()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    if args.url is None:
        url, fmt, quality, workers, out_dir_base, cookies_path = prompt_config()
        meta = thumb = parse_title = True
    else:
        banner()
        if not ffmpeg_ok():
            print(f"  {RD}✗  ffmpeg not found.{R}\n"); sys.exit(1)
        url          = args.url.strip()
        fmt          = args.format
        quality      = args.quality
        workers      = max(1, min(8, args.workers))
        out_dir_base = os.path.expanduser(args.output or "~/Music")
        cookies_path = os.path.expanduser(args.cookies) if args.cookies else None
        meta         = not args.no_metadata
        thumb        = not args.no_thumbnail
        parse_title  = not args.no_parse
        if not is_playlist(url):
            print(f"  {RD}✗  URL needs a list= parameter.{R}\n"); sys.exit(1)

    # ── Fetch ──────────────────────────────────────────────────────────────────
    section("Fetching metadata")
    sys.stdout.write(f"  {DIM}Connecting…{R}")
    sys.stdout.flush()
    try:
        pl = fetch_playlist(url, cookies_path)
    except Exception as e:
        print(f"\r  {RD}✗  {e}{R}\n"); sys.exit(1)

    title    = pl["title"]
    uploader = pl["uploader"]
    count    = len(pl["entries"])
    out_dir  = os.path.join(out_dir_base, sanitize(title))
    qual_lbl = f"{quality} kbps" if fmt not in ("flac","wav") else "lossless"

    print(f"\r  {GR}✓  Fetched{R}  {DIM}({count} tracks){R}          ")
    print()
    print(f"{PU}  ╭{'─'*W}╮{R}")
    print(box_row(f"{B}{WH}{title}{R}"))
    print(box_row(f"{DIM}by {uploader}{R}"))
    print(box_div())
    print(box_row(f"{CY}{count} tracks{R}  ·  {CY}{fmt.upper()}{R}  {DIM}{qual_lbl}{R}  ·  {CY}{workers} workers{R}"))
    print(box_row(f"{DIM}{out_dir}{R}"))
    print(f"{PU}  ╰{'─'*W}╯{R}")

    # ── Download ───────────────────────────────────────────────────────────────
    section("Downloading")
    start = time.time()
    try:
        ok, failed = download_playlist(
            pl, out_dir, fmt=fmt, quality=quality,
            meta=meta, thumb=thumb, parse_title=parse_title,
            cookies_path=cookies_path, workers=workers)
    except KeyboardInterrupt:
        print(f"\n\n  {YL}Aborted.{R}\n"); sys.exit(130)
    except Exception as e:
        print(f"\n  {RD}✗  {e}{R}\n"); sys.exit(1)

    elapsed = fmt_time(int(time.time() - start))
    print()
    print(f"{PU}  ╭{'─'*W}╮{R}")
    if failed == 0:
        print(box_row(f"{GR}{B}✓  All {ok} tracks downloaded{R}"))
    else:
        print(box_row(f"{GR}✓  {ok} downloaded{R}  {RD}✗  {failed} failed{R}"))
    print(box_row(f"{DIM}Time: {elapsed}  ·  Saved to: {out_dir}{R}"))
    print(f"{PU}  ╰{'─'*W}╯{R}")
    print()

main()
