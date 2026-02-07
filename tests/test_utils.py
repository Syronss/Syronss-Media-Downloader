from utils import detect_platform, get_platform_icon, get_platform_color, normalize_media_url


def test_detect_platform_supported_urls() -> None:
    assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
    assert detect_platform("https://www.instagram.com/reel/abc") == "instagram"
    assert detect_platform("https://www.instagram.com/stories/user/123456789/") == "instagram"
    assert detect_platform("https://www.facebook.com/watch/?v=100") == "facebook"
    assert detect_platform("https://x.com/user/status/100") == "twitter"
    assert detect_platform("https://vimeo.com/123") == "vimeo"
    assert detect_platform("https://www.dailymotion.com/video/x7") == "dailymotion"
    assert detect_platform("https://www.twitch.tv/videos/100") == "twitch"


def test_detect_platform_empty_or_invalid() -> None:
    assert detect_platform("") is None
    assert detect_platform("https://example.com/video") is None


def test_platform_icon_color_defaults() -> None:
    assert get_platform_icon("twitter") == "🐦"
    assert get_platform_color("facebook") == "#1877F2"
    assert get_platform_icon("unknown") == "🎬"
    assert get_platform_color("unknown") == "#6366F1"


def test_normalize_media_url() -> None:
    assert normalize_media_url("https://www.youtube.com/watch?v=abc&utm_source=test&feature=share") == "https://www.youtube.com/watch?v=abc"
    assert normalize_media_url("https://www.instagram.com/reel/xyz/?utm_source=ig_web_copy_link") == "https://www.instagram.com/reel/xyz/"
    assert normalize_media_url("") == ""
