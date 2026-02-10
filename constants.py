"""
Shared constants for Syronss's Media Downloader.
Central location for all configuration values, presets, and mappings.
"""

APP_NAME = "Syronss's Media Downloader"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Syronss"
APP_GITHUB = "https://github.com/Syronss"

# Supported platforms
SUPPORTED_PLATFORMS = [
    "youtube", "tiktok", "instagram", "facebook",
    "twitter", "vimeo", "dailymotion", "twitch",
]

# Quality presets
QUALITY_OPTIONS = ["best", "2160", "1080", "720", "480", "360"]

# Filename templates
FILENAME_TEMPLATES = {
    "%(title)s": "filename_title_only",
    "%(title)s - %(uploader)s": "filename_title_channel",
    "%(uploader)s - %(title)s": "filename_channel_title",
    "%(upload_date)s - %(title)s": "filename_date_title",
}

# Platform emoji icons
PLATFORM_ICONS = {
    "youtube": "📺",
    "tiktok": "🎵",
    "instagram": "📸",
    "facebook": "📘",
    "twitter": "🐦",
    "vimeo": "🎞️",
    "dailymotion": "🎬",
    "twitch": "🟣",
}

# Platform colors
PLATFORM_COLORS = {
    "youtube": "#FF0000",
    "tiktok": "#00F2EA",
    "instagram": "#E4405F",
    "facebook": "#1877F2",
    "twitter": "#1DA1F2",
    "vimeo": "#1AB7EA",
    "dailymotion": "#005BE2",
    "twitch": "#9146FF",
}

# UI Colors
COLORS = {
    "primary": ("#6366F1", "#5B5BD6"),
    "primary_hover": ("#4F46E5", "#4C4CC4"),
    "success": ("#22C55E", "#16A34A"),
    "success_hover": ("#16A34A", "#15803D"),
    "danger": ("#EF4444", "#DC2626"),
    "danger_hover": ("#DC2626", "#B91C1C"),
    "warning": ("#F59E0B", "#D97706"),
    "instagram": ("#E4405F", "#C13584"),
    "instagram_hover": ("#C13584", "#A02570"),
    "muted_text": ("gray50", "gray60"),
    "card_bg": ("gray90", "gray17"),
    "card_bg_alt": ("gray88", "gray20"),
    "button_bg": ("gray85", "gray20"),
    "button_hover": ("gray75", "gray30"),
    "button_text": ("gray30", "gray80"),
    "error_text": "#FF6B6B",
}

# Instagram content type mappings
INSTAGRAM_CONTENT_TYPES = {
    "auto": "ig_auto",
    "post": "ig_post",
    "reel": "ig_reel",
    "story": "ig_story",
}

INSTAGRAM_MEDIA_MODES = {
    "auto": "ig_media_auto",
    "video": "ig_media_video",
    "image": "ig_media_image",
}

# History limits
MAX_HISTORY_ITEMS = 50
MAX_HISTORY_DISPLAY = 10

# Settings defaults
DEFAULT_SETTINGS = {
    "filename_template": "%(title)s",
    "theme": "dark",
    "language": "tr",
    "auto_folder": False,
    "notifications": True,
    "auto_update_check": True,
}

# Available languages
LANGUAGES = {
    "tr": "Türkçe",
    "en": "English",
}
