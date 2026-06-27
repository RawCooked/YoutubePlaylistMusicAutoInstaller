# ytpl installer
# Run from PowerShell:
#   iwr -useb https://raw.githubusercontent.com/RawCooked/YoutubePlaylistMusicAutoInstaller/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

# ── ANSI helpers ──────────────────────────────────────────────────────────────
$ESC = [char]27
function pu  { "$ESC[38;5;135m$args$ESC[0m" }   # purple
function cy  { "$ESC[38;5;51m$args$ESC[0m"  }   # cyan
function gr  { "$ESC[38;5;83m$args$ESC[0m"  }   # green
function rd  { "$ESC[38;5;203m$args$ESC[0m" }   # red
function yl  { "$ESC[38;5;220m$args$ESC[0m" }   # yellow
function wh  { "$ESC[97m${args}$ESC[0m"     }   # bright white
function dim { "$ESC[2m${args}$ESC[0m"      }   # dim
function b   { "$ESC[1m${args}$ESC[0m"      }   # bold

$W = 58
function box_top  { "$(pu '  ╭')$('─' * $W)$(pu '╮')" }
function box_bot  { "$(pu '  ╰')$('─' * $W)$(pu '╯')" }
function box_div  { "$(pu '  ├')$('─' * $W)$(pu '┤')" }
function box_row($text = "") {
    $clean = $text -replace '\x1b\[[^m]*m', ''
    $pad   = [Math]::Max($W - $clean.Length - 1, 0)
    "$(pu '  │') $text$(' ' * $pad)$(pu '│')"
}

function banner {
    Write-Host ""
    Write-Host (box_top)
    Write-Host (box_row "")
    Write-Host (box_row "$(b (wh '◈  ytpl'))  $(dim '─  YouTube Playlist Downloader')")
    Write-Host (box_row "$(dim 'Installer')")
    Write-Host (box_row "")
    Write-Host (box_bot)
    Write-Host ""
}

function section($label) {
    Write-Host ""
    Write-Host "  $(pu '┄┄┄')  $ESC[38;5;177m$ESC[1m${label}$ESC[0m"
    Write-Host ""
}

function ok($msg)   { Write-Host "  $(gr '✓')  $msg" }
function fail($msg) { Write-Host "  $(rd '✗')  $msg"; exit 1 }
function info($msg) { Write-Host "  $(dim $msg)" }
function warn($msg) { Write-Host "  $(yl '⚠')  $msg" }

# ── Start ─────────────────────────────────────────────────────────────────────
banner

# ── Python ────────────────────────────────────────────────────────────────────
section "Checking requirements"

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $v = & $cmd --version 2>&1
        if ($v -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 9) { $python = $cmd; break }
        }
    } catch {}
}
if (-not $python) { fail "Python 3.9+ not found. Install from $(cy 'https://python.org')" }
ok "Python  $(dim (& $python --version 2>&1))"

# ── ffmpeg ────────────────────────────────────────────────────────────────────
$ffmpegFound = $null -ne (Get-Command ffmpeg -ErrorAction SilentlyContinue)
if ($ffmpegFound) {
    ok "ffmpeg  $(dim 'detected')"
} else {
    warn "ffmpeg not found — ytpl needs it to convert audio."
    Write-Host "     $(dim 'Install with:')  $(cy 'choco install ffmpeg')  $(dim 'or')  $(cy 'scoop install ffmpeg')"
}

# ── yt-dlp ───────────────────────────────────────────────────────────────────
section "Installing yt-dlp"
try {
    & $python -m pip install --quiet --upgrade yt-dlp
    $v = (& $python -m pip show yt-dlp 2>&1 | Select-String "Version:") -replace "Version:\s*",""
    ok "yt-dlp  $(dim "v$v")"
} catch {
    fail "pip install yt-dlp failed: $_"
}

# ── Download ytpl.cmd ─────────────────────────────────────────────────────────
section "Installing ytpl"

$installDir = "$env:USERPROFILE\.ytpl"
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}

$rawUrl = "https://raw.githubusercontent.com/RawCooked/YoutubePlaylistMusicAutoInstaller/main/cmd/ytpl.cmd"
$dest   = "$installDir\ytpl.cmd"

try {
    Invoke-WebRequest -Uri $rawUrl -OutFile $dest -UseBasicParsing
    ok "Downloaded  $(dim $dest)"
} catch {
    fail "Could not download ytpl.cmd: $_"
}

# ── PATH ──────────────────────────────────────────────────────────────────────
section "Adding to PATH"

$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -split ";" | Where-Object { $_ -ieq $installDir }) {
    ok "Already in PATH"
} else {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
    ok "Added  $(dim $installDir)  to user PATH"
    info "Restart your terminal for the PATH change to take effect."
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host (box_top)
Write-Host (box_row "$(gr (b '✓  ytpl installed successfully'))")
Write-Host (box_div)
Write-Host (box_row "$(dim 'Open a new terminal window and run:')")
Write-Host (box_row "")
Write-Host (box_row "$(wh '  ytpl')")
Write-Host (box_row "")
Write-Host (box_bot)
Write-Host ""
