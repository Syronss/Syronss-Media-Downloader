"""Tests for utils.py — platform detection, URL normalization, helpers."""

from utils import (
    detect_platform, get_platform_icon, get_platform_color,
    normalize_media_url, format_size, Debouncer,
    extract_urls_from_text, get_platform_download_path,
)
from constants import PLATFORM_ICONS, PLATFORM_COLORS
from pathlib import Path
import time


# ─── detect_platform ───

def test_detect_platform_supported_urls() -> None:
    assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
    assert detect_platform("https://www.instagram.com/reel/abc") == "instagram"
    assert detect_platform("https://www.instagram.com/stories/user/123456789/") == "instagram"
    assert detect_platform("https://www.facebook.com/watch/?v=100") == "facebook"


def test_detect_platform_returns_none_for_unsupported() -> None:
    assert detect_platform("https://www.example.com/video") is None
    assert detect_platform("") is None
    assert detect_platform("not-a-url") is None


def test_detect_platform_case_insensitive() -> None:
    assert detect_platform("https://WWW.YOUTUBE.COM/watch?v=abc") == "youtube"
    assert detect_platform("https://TikTok.com/@user/video/123") == "tiktok"


def test_detect_platform_all_supported() -> None:
    """Ensure all platforms in constants are detectable."""
    test_urls = {
        "youtube": "https://youtube.com/watch?v=xyz",
        "tiktok": "https://tiktok.com/@a/video/1",
        "instagram": "https://instagram.com/p/abc",
        "facebook": "https://facebook.com/watch/?v=1",
        "twitter": "https://x.com/user/status/1",
        "vimeo": "https://vimeo.com/123",
        "dailymotion": "https://dailymotion.com/video/x1",
        "twitch": "https://twitch.tv/user",
    }
    for platform, url in test_urls.items():
        assert detect_platform(url) == platform, f"Failed for {platform}"


# ─── get_platform_icon & get_platform_color ───

def test_get_platform_icon_known() -> None:
    assert get_platform_icon("youtube") == PLATFORM_ICONS["youtube"]
    assert get_platform_icon("instagram") == PLATFORM_ICONS["instagram"]


def test_get_platform_icon_fallback() -> None:
    assert get_platform_icon("unknown") == "🎬"


def test_get_platform_color_known() -> None:
    assert get_platform_color("youtube") == PLATFORM_COLORS["youtube"]


def test_get_platform_color_fallback() -> None:
    assert get_platform_color("unknown") == "#6366F1"


# ─── normalize_media_url ───

def test_normalize_strips_tracking_params_youtube() -> None:
    url = "https://www.youtube.com/watch?v=abc&si=tracking&utm_source=x"
    result = normalize_media_url(url)
    assert "v=abc" in result
    assert "si=" not in result
    assert "utm_source" not in result


def test_normalize_keeps_essential_params() -> None:
    url = "https://www.youtube.com/watch?v=abc&list=PLxyz"
    result = normalize_media_url(url)
    assert "v=abc" in result
    assert "list=PLxyz" in result


def test_normalize_empty_string() -> None:
    assert normalize_media_url("") == ""
    assert normalize_media_url("   ") == ""


def test_normalize_instagram_strips_igsh() -> None:
    url = "https://www.instagram.com/p/abc123/?igsh=xyz"
    result = normalize_media_url(url)
    assert "igsh" not in result


# ─── format_size ───

def test_format_size() -> None:
    assert format_size(500) == "500 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
    assert format_size(1073741824) == "1.00 GB"


# ─── extract_urls_from_text ───

def test_extract_urls_basic() -> None:
    text = """
    https://www.youtube.com/watch?v=abc
    https://www.instagram.com/p/def/
    # this is a comment
    not a url
    https://example.com/not-supported
    """
    urls = extract_urls_from_text(text)
    assert len(urls) == 2
    assert any("youtube" in u for u in urls)
    assert any("instagram" in u for u in urls)


def test_extract_urls_empty() -> None:
    assert extract_urls_from_text("") == []
    assert extract_urls_from_text("# just comments") == []


# ─── get_platform_download_path ───

def test_platform_download_path_no_auto(tmp_path: Path) -> None:
    result = get_platform_download_path(tmp_path, "youtube", auto_folder=False)
    assert result == tmp_path


def test_platform_download_path_with_auto(tmp_path: Path) -> None:
    result = get_platform_download_path(tmp_path, "youtube", auto_folder=True)
    assert result == tmp_path / "Youtube"
    assert result.exists()


# ─── Debouncer ───

def test_debouncer_calls_once() -> None:
    results = []
    debouncer = Debouncer(delay_ms=50)

    debouncer(lambda: results.append(1))
    debouncer(lambda: results.append(2))
    debouncer(lambda: results.append(3))

    time.sleep(0.15)
    assert results == [3], "Only the last call should execute"


def test_debouncer_cancel() -> None:
    results = []
    debouncer = Debouncer(delay_ms=50)

    debouncer(lambda: results.append(1))
    debouncer.cancel()

    time.sleep(0.15)
    assert results == []
