"""
Yardımcı fonksiyonlar - URL tespiti, dosya işlemleri
"""
import re
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from typing import Optional


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
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_platform_icon(platform: str) -> str:
    """Platform için emoji ikonu döndürür."""
    icons = {
        'youtube': '📺',
        'tiktok': '🎵',
        'instagram': '📸',
        'facebook': '📘',
        'twitter': '🐦',
        'vimeo': '🎞️',
        'dailymotion': '🎬',
        'twitch': '🟣',
    }
    return icons.get(platform, '🎬')


def get_platform_color(platform: str) -> str:
    """Platform için renk kodu döndürür."""
    colors = {
        'youtube': '#FF0000',
        'tiktok': '#00F2EA',
        'instagram': '#E4405F',
        'facebook': '#1877F2',
        'twitter': '#1DA1F2',
        'vimeo': '#1AB7EA',
        'dailymotion': '#005BE2',
        'twitch': '#9146FF',
    }
    return colors.get(platform, '#6366F1')
