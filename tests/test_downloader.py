from pathlib import Path

from downloader import InstagramDownloader, YTDLPDownloader, create_downloader


def test_extract_shortcode_variants(tmp_path: Path) -> None:
    downloader = InstagramDownloader(tmp_path)
    assert downloader._extract_shortcode("https://www.instagram.com/p/ABCdef123/") == "ABCdef123"
    assert downloader._extract_shortcode("https://www.instagram.com/reel/ABCD-ef_1/?igsh=abc") == "ABCD-ef_1"
    assert downloader._extract_shortcode("https://www.instagram.com/reels/ABCD-ef_1/") == "ABCD-ef_1"


def test_extract_story_identifiers(tmp_path: Path) -> None:
    downloader = InstagramDownloader(tmp_path)
    username, story_id = downloader._extract_story_identifiers(
        "https://www.instagram.com/stories/testuser/3456789012345678901/"
    )
    assert username == "testuser"
    assert story_id == "3456789012345678901"


def test_create_downloader_for_expanded_platforms(tmp_path: Path) -> None:
    assert isinstance(create_downloader("youtube", tmp_path), YTDLPDownloader)
    assert isinstance(create_downloader("instagram", tmp_path), InstagramDownloader)
    assert isinstance(create_downloader("facebook", tmp_path), YTDLPDownloader)
    assert isinstance(create_downloader("twitter", tmp_path), YTDLPDownloader)


def test_subtitle_options(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("downloader.check_and_get_ffmpeg", lambda: "ffmpeg")
    downloader = YTDLPDownloader(tmp_path, "youtube")
    opts = downloader._get_ydl_opts(as_audio=False, quality="best", download_subtitles=True)
    assert opts.get("writesubtitles") is True
    assert opts.get("writeautomaticsub") is True
    assert opts.get("embedsubtitles") is True


def test_subtitle_not_enabled_for_audio(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("downloader.check_and_get_ffmpeg", lambda: "ffmpeg")
    downloader = YTDLPDownloader(tmp_path, "youtube")
    opts = downloader._get_ydl_opts(as_audio=True, quality="best", download_subtitles=True)
    assert "writesubtitles" not in opts


def test_extract_instagram_content_type(tmp_path: Path) -> None:
    downloader = InstagramDownloader(tmp_path)
    assert downloader._extract_content_type("https://www.instagram.com/p/abc/") == "post"
    assert downloader._extract_content_type("https://www.instagram.com/reel/abc/") == "reel"
    assert downloader._extract_content_type("https://www.instagram.com/stories/user/123/") == "story"


def test_find_latest_downloaded_file_with_media_mode(tmp_path: Path) -> None:
    downloader = InstagramDownloader(tmp_path)
    image_file = tmp_path / "ABC_1.jpg"
    video_file = tmp_path / "ABC_2.mp4"
    image_file.write_bytes(b"img")
    video_file.write_bytes(b"vid")

    latest_auto = downloader._find_latest_downloaded_file("ABC", "auto")
    latest_video = downloader._find_latest_downloaded_file("ABC", "video")
    latest_image = downloader._find_latest_downloaded_file("ABC", "image")

    assert latest_auto is not None
    assert latest_video == video_file
    assert latest_image == image_file
