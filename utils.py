"""
Yardımcı fonksiyonlar - URL tespiti, dosya işlemleri, bildirimler
"""
import re
import os
import sys
import ctypes
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import Optional, Callable

from constants import PLATFORM_ICONS, PLATFORM_COLORS


def detect_platform(url: str) -> Optional[str]:
    """URL'den platformu tespit eder."""
    normalized_url = url.strip().lower()
    if not normalized_url:
        return None

    platform_patterns = {
        'youtube': [r'(youtube\.com|youtu\.be)'],
        'tiktok': [r'tiktok\.com', r'vm\.tiktok\.com'],
        'instagram': [r'instagram\.com', r'instagr\.am'],
        'facebook': [r'facebook\.com', r'fb\.watch'],
        'twitter': [r'twitter\.com', r'x\.com'],
        'vimeo': [r'vimeo\.com'],
        'dailymotion': [r'dailymotion\.com', r'dai\.ly'],
        'twitch': [r'twitch\.tv'],
    }

    for platform, patterns in platform_patterns.items():
        for pattern in patterns:
            if re.search(pattern, normalized_url):
                return platform

    return None


def normalize_media_url(url: str) -> str:
    """URL üzerindeki takip parametrelerini temizler."""
    cleaned = url.strip()
    if not cleaned:
        return ""

    try:
        parsed = urlparse(cleaned)
    except ValueError:
        return cleaned

    if not parsed.scheme or not parsed.netloc:
        return cleaned

    allowed_params = {
        'youtube': {'v', 'list', 'index', 't'},
        'instagram': {'img_index'},
        'facebook': {'v'},
    }
    platform = detect_platform(cleaned)
    keep = allowed_params.get(platform, set())

    query_items = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=False)
                   if key in keep]
    normalized_query = urlencode(query_items)
    normalized = parsed._replace(query=normalized_query, fragment='')
    return urlunparse(normalized)


def format_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevirir."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_download_folder() -> Path:
    """Varsayılan indirme klasörünü döndürür."""
    downloads = Path.home() / "Downloads" / "VideoDownloader"
    downloads.mkdir(parents=True, exist_ok=True)
    return downloads


def check_ffmpeg() -> bool:
    """FFmpeg'in kurulu olup olmadığını kontrol eder."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_platform_icon(platform: str) -> str:
    """Platform için emoji ikonu döndürür."""
    return PLATFORM_ICONS.get(platform, '🎬')


def get_platform_color(platform: str) -> str:
    """Platform için renk kodu döndürür."""
    return PLATFORM_COLORS.get(platform, '#6366F1')


# ---------- New Helpers ----------

class Debouncer:
    """Debounce function calls — waits for a pause before executing."""
    
    def __init__(self, delay_ms: int = 300):
        self.delay_ms = delay_ms
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
    
    def __call__(self, func: Callable, *args, **kwargs) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(
                self.delay_ms / 1000.0,
                func,
                args=args,
                kwargs=kwargs,
            )
            self._timer.daemon = True
            self._timer.start()
    
    def cancel(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


def get_clipboard_text() -> str:
    """Get text from system clipboard (Windows)."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text.strip()
    except Exception:
        return ""


def flash_taskbar_icon(window) -> None:
    """Flash the taskbar icon to notify the user (Windows only)."""
    if sys.platform != "win32":
        return
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        app_hwnd = window.winfo_id()
        if hwnd != app_hwnd:
            # FLASHW_ALL = 3, FLASHW_TIMERNOFG = 12
            class FLASHWINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint),
                    ("hwnd", ctypes.c_void_p),
                    ("dwFlags", ctypes.c_uint),
                    ("uCount", ctypes.c_uint),
                    ("dwTimeout", ctypes.c_uint),
                ]
            finfo = FLASHWINFO()
            finfo.cbSize = ctypes.sizeof(FLASHWINFO)
            finfo.hwnd = app_hwnd
            finfo.dwFlags = 3 | 12  # FLASHW_ALL | FLASHW_TIMERNOFG
            finfo.uCount = 5
            finfo.dwTimeout = 0
            ctypes.windll.user32.FlashWindowEx(ctypes.byref(finfo))
    except Exception:
        pass


def get_platform_download_path(base_path: Path, platform: str, auto_folder: bool = False) -> Path:
    """Get download path, optionally creating platform subfolder."""
    if auto_folder and platform:
        folder = base_path / platform.capitalize()
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    return base_path


def check_ytdlp_update() -> Optional[str]:
    """Check if yt-dlp has an available update. Returns new version or None."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "yt-dlp"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            import yt_dlp
            current = yt_dlp.version.__version__
            # Parse output for latest version
            for line in result.stdout.splitlines():
                if "LATEST:" in line.upper() or "Available versions:" in line:
                    versions = re.findall(r'[\d.]+', line)
                    if versions and versions[0] != current:
                        return versions[0]
    except Exception:
        pass
    return None


def update_ytdlp() -> bool:
    """Update yt-dlp to latest version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0
    except Exception:
        return False


def extract_urls_from_text(text: str) -> list[str]:
    """Extract valid media URLs from multi-line text."""
    urls = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Basic URL validation
        if re.match(r'https?://', line):
            normalized = normalize_media_url(line)
            if normalized and detect_platform(normalized):
                urls.append(normalized)
    return urls
