"""
Yardımcı fonksiyonlar - URL tespiti, dosya işlemleri
"""
import re
import os
from pathlib import Path
from typing import Optional


def detect_platform(url: str) -> Optional[str]:
    """URL'den platformu tespit eder."""
    url = url.strip().lower()
    
    youtube_patterns = [r'(youtube\.com|youtu\.be)']
    tiktok_patterns = [r'tiktok\.com', r'vm\.tiktok\.com']
    instagram_patterns = [r'instagram\.com', r'instagr\.am']
    
    for pattern in youtube_patterns:
        if re.search(pattern, url):
            return 'youtube'
    
    for pattern in tiktok_patterns:
        if re.search(pattern, url):
            return 'tiktok'
    
    for pattern in instagram_patterns:
        if re.search(pattern, url):
            return 'instagram'
    
    return None


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
    icons = {'youtube': '📺', 'tiktok': '🎵', 'instagram': '📸'}
    return icons.get(platform, '🎬')


def get_platform_color(platform: str) -> str:
    """Platform için renk kodu döndürür."""
    colors = {'youtube': '#FF0000', 'tiktok': '#00F2EA', 'instagram': '#E4405F'}
    return colors.get(platform, '#6366F1')
