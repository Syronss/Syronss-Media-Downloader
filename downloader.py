"""Downloader backends for yt-dlp and Instagram."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import instaloader
import yt_dlp


def check_and_get_ffmpeg() -> Optional[str]:
    """Return ffmpeg executable path if available."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            return "ffmpeg"
    except FileNotFoundError:
        pass

    ffmpeg_path = Path.home() / "AppData" / "Local" / "yt-dlp" / "ffmpeg.exe"
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    return None


@dataclass
class DownloadResult:
    """Result model for single media download."""

    success: bool
    filename: str = ""
    filepath: str = ""
    filesize: int = 0
    error: str = ""
    platform: str = ""
    source_url: str = ""


class ProgressCallback:
    """Simple callback wrapper for progress updates."""

    def __init__(self, callback: Callable[[float, str, str], None]) -> None:
        self.callback = callback
        self.last_percent = 0.0

    def update(self, percent: float, status: str, speed: str = "") -> None:
        if self.callback:
            self.callback(percent, status, speed)
        self.last_percent = percent


class BaseDownloader(ABC):
    """Base downloader interface."""

    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path
        self.download_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def download(
        self,
        url: str,
        as_audio: bool = False,
        quality: str = "best",
        progress_callback: Optional[ProgressCallback] = None,
        filename_template: str = None,
        download_subtitles: bool = False,
        instagram_content_type: str = "auto",
        instagram_media_mode: str = "auto",
    ) -> DownloadResult:
        raise NotImplementedError

    @abstractmethod
    def get_info(self, url: str) -> Dict[str, Any]:
        raise NotImplementedError


class YTDLPDownloader(BaseDownloader):
    """yt-dlp backend for YouTube/TikTok and similar platforms."""

    def __init__(self, download_path: Path, platform: str = "youtube") -> None:
        super().__init__(download_path)
        self.platform = platform
        self.filename_template = "%(title)s"

    def _get_ydl_opts(
        self,
        as_audio: bool,
        quality: str = "best",
        progress_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
        filename_template: Optional[str] = None,
        download_subtitles: bool = False,
    ) -> Dict[str, Any]:
        ffmpeg_path = check_and_get_ffmpeg()
        template = filename_template or self.filename_template

        opts: Dict[str, Any] = {
            "outtmpl": str(self.download_path / f"{template}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        if ffmpeg_path:
            opts["ffmpeg_location"] = ffmpeg_path

        if as_audio:
            if not ffmpeg_path:
                raise RuntimeError("MP3 dönüşümü için FFmpeg gerekli!")
            opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "320",
                        }
                    ],
                }
            )
        else:
            if ffmpeg_path:
                if quality == "best":
                    opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
                else:
                    opts["format"] = (
                        f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
                        f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
                    )
                opts["merge_output_format"] = "mp4"
            else:
                opts["format"] = "22/18/best[vcodec!=none][acodec!=none]/best"

        if download_subtitles and not as_audio:
            opts.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": ["tr", "en", ".*"],
                }
            )
            if ffmpeg_path:
                opts["embedsubtitles"] = True

        if progress_hook:
            opts["progress_hooks"] = [progress_hook]

        return opts

    def download(
        self,
        url: str,
        as_audio: bool = False,
        quality: str = "best",
        progress_callback: Optional[ProgressCallback] = None,
        filename_template: str = None,
        download_subtitles: bool = False,
        instagram_content_type: str = "auto",
        instagram_media_mode: str = "auto",
    ) -> DownloadResult:
        _ = instagram_content_type
        _ = instagram_media_mode
        result = DownloadResult(success=False, platform=self.platform, source_url=url)
        downloaded_file = ""

        def progress_hook(data: Dict[str, Any]) -> None:
            nonlocal downloaded_file
            status = data.get("status", "")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                done = data.get("downloaded_bytes") or 0
                speed = data.get("speed") or 0
                if total > 0 and progress_callback:
                    percent = (float(done) / float(total)) * 100.0
                    speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else ""
                    progress_callback.update(percent, "İndiriliyor...", speed_str)
            elif status == "finished":
                downloaded_file = data.get("filename", "")
                if progress_callback:
                    progress_callback.update(100, "Tamamlandı!", "")

        try:
            options = self._get_ydl_opts(as_audio, quality, progress_hook, filename_template, download_subtitles)
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)

            if info:
                if as_audio:
                    title = info.get("title", "video")
                    for char in '<>:"/\\|?*':
                        title = title.replace(char, "_")
                    expected_file = self.download_path / f"{title}.mp3"
                    if expected_file.exists():
                        downloaded_file = str(expected_file)

                result.success = True
                result.filename = os.path.basename(downloaded_file) if downloaded_file else info.get("title", "video")
                result.filepath = downloaded_file
                result.filesize = int(info.get("filesize") or info.get("filesize_approx") or 0)
                if result.filepath and Path(result.filepath).exists() and result.filesize == 0:
                    result.filesize = Path(result.filepath).stat().st_size
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)

        return result

    def get_info(self, url: str) -> Dict[str, Any]:
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": False}) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                return {}
            return {
                "title": info.get("title", "Bilinmiyor"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "uploader": info.get("uploader", info.get("channel", "Bilinmiyor")),
                "view_count": info.get("view_count", 0),
                "qualities": self._get_available_qualities(info),
                "filesize": info.get("filesize") or info.get("filesize_approx", 0) or 0,
            }
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def _get_available_qualities(self, info: Dict[str, Any]) -> list[str]:
        qualities: set[str] = set()
        for fmt in info.get("formats", []):
            height = fmt.get("height")
            if not height:
                continue
            if height >= 2160:
                qualities.add("2160")
            elif height >= 1080:
                qualities.add("1080")
            elif height >= 720:
                qualities.add("720")
            elif height >= 480:
                qualities.add("480")
            elif height >= 360:
                qualities.add("360")
        return sorted(qualities, key=int, reverse=True) if qualities else ["best"]


class InstagramDownloader(BaseDownloader):
    """Instaloader backend for Instagram content."""

    def __init__(self, download_path: Path) -> None:
        super().__init__(download_path)
        self.loader = self._create_loader(download_path)
        self.logged_in = False
        self.username: Optional[str] = None
        self._session_file: Optional[Path] = None

    def _create_loader(self, download_path: Path) -> instaloader.Instaloader:
        return instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            dirname_pattern=str(download_path),
            filename_pattern="{shortcode}",
        )

    def login(self, username: str, password: str) -> tuple[bool, str]:
        try:
            self.loader.login(username, password)
            self.logged_in = True
            self.username = username
            return True, "Giriş başarılı!"
        except instaloader.exceptions.BadCredentialsException:
            return False, "Kullanıcı adı veya şifre hatalı!"
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            self.username = username
            return False, "2FA_REQUIRED"
        except instaloader.exceptions.ConnectionException as exc:
            msg = str(exc)
            if "checkpoint" in msg.lower():
                return False, "Instagram güvenlik doğrulaması gerekli. Lütfen tarayıcıdan giriş yapın."
            return False, f"Bağlantı hatası: {msg}"
        except Exception as exc:  # noqa: BLE001
            return False, f"Giriş hatası: {exc}"

    def login_with_2fa(self, username: str, password: str, code: str) -> tuple[bool, str]:
        _ = password
        try:
            self.loader.two_factor_login(code)
            self.logged_in = True
            self.username = username
            return True, "Giriş başarılı!"
        except instaloader.exceptions.BadCredentialsException:
            return False, "Geçersiz doğrulama kodu!"
        except Exception as exc:  # noqa: BLE001
            return False, f"Doğrulama hatası: {exc}"

    def load_session(self, username: str) -> bool:
        try:
            self.loader.load_session_from_file(username)
            self.logged_in = True
            self.username = username
            self._session_file = self._get_session_file(username)
            return True
        except Exception:
            return False

    def save_session(self, username: str) -> None:
        try:
            self.loader.save_session_to_file(username)
            self._session_file = self._get_session_file(username)
        except Exception:
            pass

    def logout(self) -> bool:
        try:
            if self.username:
                self._cleanup_session_artifacts(self.username)
            self.loader = self._create_loader(self.download_path)
            self.logged_in = False
            self.username = None
            self._session_file = None
            return True
        except Exception:
            return False

    def _cleanup_session_artifacts(self, username: str) -> None:
        home = Path.home()
        patterns = [
            home / f".instaloader-session-{username}",
            home / f"{username}_session",
            home / f".{username}_session",
            home / username,
        ]
        for path in patterns:
            self._safe_delete(path)

        candidate_dirs = [
            self.download_path,
            Path(__file__).parent,
            Path.cwd(),
            home / "AppData" / "Local" / "Instaloader",
            home / "AppData" / "Roaming" / "Instaloader",
            home / ".config" / "instaloader",
        ]
        for directory in candidate_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            for item in directory.iterdir():
                if username.lower() in item.name.lower():
                    self._safe_delete(item)

    def _safe_delete(self, path: Path) -> None:
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    def _get_session_file(self, username: str) -> Optional[Path]:
        path = Path.home() / f".instaloader-session-{username}"
        return path if path.exists() else None

    def download(
        self,
        url: str,
        as_audio: bool = False,
        quality: str = "best",
        progress_callback: Optional[ProgressCallback] = None,
        filename_template: str = None,
        download_subtitles: bool = False,
        instagram_content_type: str = "auto",
        instagram_media_mode: str = "auto",
    ) -> DownloadResult:
        _ = as_audio
        _ = quality
        _ = filename_template
        _ = download_subtitles

        result = DownloadResult(success=False, platform="instagram", source_url=url)

        try:
            if progress_callback:
                progress_callback.update(10, "Bağlanılıyor...", "")

            detected_content_type = self._extract_content_type(url)
            normalized_request_type = instagram_content_type if instagram_content_type in {"auto", "post", "reel", "story"} else "auto"
            if normalized_request_type != "auto" and normalized_request_type != detected_content_type:
                result.error = f"Seçilen Instagram türü ({normalized_request_type}) URL ile eşleşmiyor ({detected_content_type})"
                return result

            story_username, story_id = self._extract_story_identifiers(url)
            if story_username and story_id:
                if progress_callback:
                    progress_callback.update(30, "Hikaye bilgileri alınıyor...", "")
                return self._download_story(story_username, story_id, progress_callback, url, instagram_media_mode)

            shortcode = self._extract_shortcode(url)
            if not shortcode:
                result.error = "Geçersiz Instagram URL'si"
                return result

            if progress_callback:
                progress_callback.update(30, "Instagram gönderi bilgileri alınıyor...", "")

            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            if progress_callback:
                progress_callback.update(50, "İndiriliyor...", "")

            self.loader.download_post(post, target=str(self.download_path))

            media_mode = instagram_media_mode if instagram_media_mode in {"auto", "video", "image"} else "auto"
            downloaded_file = self._find_latest_downloaded_file(shortcode, media_mode)
            if not downloaded_file:
                result.error = "İndirilen dosya bulunamadı"
                return result

            if progress_callback:
                progress_callback.update(100, "Tamamlandı!", "")

            result.success = True
            result.filename = downloaded_file.name
            result.filepath = str(downloaded_file)
            result.filesize = downloaded_file.stat().st_size
            return result
        except instaloader.exceptions.LoginRequiredException:
            result.error = "Bu içerik için Instagram girişi gerekli"
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            result.error = "Bu içerik gizli bir hesaba ait"
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)

        return result

    def get_info(self, url: str) -> Dict[str, Any]:
        try:
            story_username, story_id = self._extract_story_identifiers(url)
            if story_username and story_id:
                return {
                    "title": f"Story • @{story_username}",
                    "uploader": story_username,
                    "thumbnail": "",
                    "duration": 0,
                    "qualities": ["best"],
                    "content_type": "story",
                    "media_modes": ["auto", "video", "image"],
                }

            shortcode = self._extract_shortcode(url)
            if shortcode:
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                return {
                    "title": post.caption[:50] if post.caption else shortcode,
                    "uploader": post.owner_username,
                    "thumbnail": "",
                    "duration": 0,
                    "qualities": ["best"],
                    "content_type": self._extract_content_type(url),
                    "media_modes": ["auto", "video", "image"],
                    "is_video": bool(post.is_video),
                }
        except Exception:
            pass
        return {}

    def _extract_shortcode(self, url: str) -> Optional[str]:
        patterns = [
            r"instagram\.com/p/([A-Za-z0-9_-]+)",
            r"instagram\.com/reel/([A-Za-z0-9_-]+)",
            r"instagram\.com/tv/([A-Za-z0-9_-]+)",
            r"instagram\.com/reels/([A-Za-z0-9_-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_content_type(self, url: str) -> str:
        lowered = url.lower()
        if "/stories/" in lowered:
            return "story"
        if "/reel/" in lowered or "/reels/" in lowered or "/tv/" in lowered:
            return "reel"
        return "post"

    def _find_latest_downloaded_file(self, shortcode: str, media_mode: str = "auto") -> Optional[Path]:
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        video_extensions = {".mp4", ".mov", ".mkv"}

        candidates = [
            file
            for file in self.download_path.glob(f"*{shortcode}*.*")
            if file.is_file() and file.suffix.lower() in image_extensions.union(video_extensions)
        ]
        if not candidates:
            return None

        if media_mode == "video":
            candidates = [file for file in candidates if file.suffix.lower() in video_extensions]
        elif media_mode == "image":
            candidates = [file for file in candidates if file.suffix.lower() in image_extensions]

        if not candidates:
            return None
        return max(candidates, key=lambda file: file.stat().st_mtime)

    def _extract_story_identifiers(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r"instagram\.com/stories/([^/]+)/([^/?#]+)", url)
        if not match:
            return None, None
        username = match.group(1)
        story_id = match.group(2).split("?")[0]
        if not username or not story_id:
            return None, None
        return username, story_id

    def _download_story(
        self,
        username: str,
        story_id: str,
        progress_callback: Optional[ProgressCallback],
        source_url: str,
        media_mode: str = "auto",
    ) -> DownloadResult:
        result = DownloadResult(success=False, platform="instagram", source_url=source_url)
        profile = instaloader.Profile.from_username(self.loader.context, username)

        found_story = None
        for story in self.loader.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                if str(item.mediaid) == story_id:
                    found_story = item
                    break
            if found_story:
                break

        if not found_story:
            result.error = "Hikaye bulunamadı veya süresi dolmuş"
            return result

        if progress_callback:
            progress_callback.update(60, "Instagram hikayesi indiriliyor...", "")

        self.loader.download_storyitem(found_story, target=str(self.download_path))
        downloaded_file = self._find_latest_downloaded_file(story_id, media_mode if media_mode in {"auto", "video", "image"} else "auto")
        if not downloaded_file:
            result.error = "Hikaye dosyası bulunamadı"
            return result

        if progress_callback:
            progress_callback.update(100, "Tamamlandı!", "")

        result.success = True
        result.filename = downloaded_file.name
        result.filepath = str(downloaded_file)
        result.filesize = downloaded_file.stat().st_size
        return result


def create_downloader(platform: str, download_path: Path) -> BaseDownloader:
    """Create the right downloader implementation for the platform."""
    if platform == "youtube":
        return YTDLPDownloader(download_path, "youtube")
    if platform == "tiktok":
        return YTDLPDownloader(download_path, "tiktok")
    if platform == "instagram":
        return InstagramDownloader(download_path)
    if platform in {"facebook", "twitter", "vimeo", "dailymotion", "twitch"}:
        return YTDLPDownloader(download_path, platform)
    raise ValueError(f"Desteklenmeyen platform: {platform}")
