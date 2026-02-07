"""
Video indirme modülü - YouTube, TikTok, Instagram desteği
Instagram 2FA ve güvenli oturum yönetimi
"""
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import yt_dlp
import instaloader


def check_and_get_ffmpeg() -> Optional[str]:
    """FFmpeg'i kontrol et."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'ffmpeg'
    except FileNotFoundError:
        pass
    
    ffmpeg_path = Path.home() / "AppData" / "Local" / "yt-dlp" / "ffmpeg.exe"
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    
    return None


@dataclass
class DownloadResult:
    """İndirme sonucu."""
    success: bool
    filename: str = ""
    filepath: str = ""
    filesize: int = 0
    error: str = ""
    platform: str = ""
    source_url: str = ""


class ProgressCallback:
    """İlerleme callback'i."""
    def __init__(self, callback: Callable[[float, str, str], None]):
        self.callback = callback
        self.last_percent = 0
    
    def update(self, percent: float, status: str, speed: str = ""):
        if self.callback:
            self.callback(percent, status, speed)
        self.last_percent = percent


class BaseDownloader(ABC):
    """Temel indirici sınıfı."""
    
    def __init__(self, download_path: Path):
        self.download_path = download_path
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def download(self, url: str, as_audio: bool = False, quality: str = "best",
                 progress_callback: Optional[ProgressCallback] = None,
                 filename_template: str = None, download_subtitles: bool = False) -> DownloadResult:
        pass
    
    @abstractmethod
    def get_info(self, url: str) -> Dict[str, Any]:
        pass


class YTDLPDownloader(BaseDownloader):
    """yt-dlp tabanlı indirici (YouTube, TikTok)."""
    
    QUALITY_OPTIONS = {
        'best': 'En İyi Kalite',
        '2160': '4K (2160p)',
        '1080': 'Full HD (1080p)',
        '720': 'HD (720p)',
        '480': 'SD (480p)',
        '360': 'Düşük (360p)',
    }
    
    def __init__(self, download_path: Path, platform: str = "youtube"):
        super().__init__(download_path)
        self.platform = platform
        self.filename_template = "%(title)s"
    
    def _get_ydl_opts(self, as_audio: bool, quality: str = "best",
                       progress_hook: Callable = None, filename_template: str = None,
                       download_subtitles: bool = False) -> dict:
        ffmpeg_path = check_and_get_ffmpeg()
        template = filename_template or self.filename_template
        
        opts = {
            'outtmpl': str(self.download_path / f'{template}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        if ffmpeg_path:
            opts['ffmpeg_location'] = ffmpeg_path
        
        if as_audio:
            if not ffmpeg_path:
                raise Exception("MP3 dönüşümü için FFmpeg gerekli!")
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            })
        else:
            if ffmpeg_path:
                if quality == 'best':
                    opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
                else:
                    opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'
                opts['merge_output_format'] = 'mp4'
            else:
                opts['format'] = '22/18/best[vcodec!=none][acodec!=none]/best'

        if download_subtitles and not as_audio:
            opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['tr', 'en', '.*'],
                'skip_download': False,
            })
            if ffmpeg_path:
                opts['embedsubtitles'] = True
        
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
        
        return opts
    
    def download(self, url: str, as_audio: bool = False, quality: str = "best",
                 progress_callback: Optional[ProgressCallback] = None,
                 filename_template: str = None, download_subtitles: bool = False) -> DownloadResult:
        result = DownloadResult(success=False, platform=self.platform, source_url=url)
        downloaded_file = None
        
        def progress_hook(d):
            nonlocal downloaded_file
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0) or 0
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    speed_str = f"{speed / (1024*1024):.1f} MB/s" if speed else ""
                    if progress_callback:
                        progress_callback.update(percent, "İndiriliyor...", speed_str)
            
            elif d['status'] == 'finished':
                downloaded_file = d.get('filename', '')
                if progress_callback:
                    progress_callback.update(100, "Tamamlandı!", "")
        
        try:
            opts = self._get_ydl_opts(as_audio, quality, progress_hook, filename_template, download_subtitles)
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    if as_audio:
                        title = info.get('title', 'video')
                        for char in '<>:"/\\|?*':
                            title = title.replace(char, '_')
                        expected_file = self.download_path / f"{title}.mp3"
                        if expected_file.exists():
                            downloaded_file = str(expected_file)
                    
                    result.success = True
                    result.filename = os.path.basename(downloaded_file) if downloaded_file else info.get('title', 'video')
                    result.filepath = downloaded_file or ""
                    result.filesize = info.get('filesize', 0) or 0
                    if not result.filesize and downloaded_file and Path(downloaded_file).exists():
                        result.filesize = Path(downloaded_file).stat().st_size
        
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def get_info(self, url: str) -> Dict[str, Any]:
        try:
            opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        'title': info.get('title', 'Bilinmiyor'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', info.get('channel', 'Bilinmiyor')),
                        'view_count': info.get('view_count', 0),
                        'qualities': self._get_available_qualities(info),
                        'filesize': info.get('filesize') or info.get('filesize_approx', 0) or 0,
                    }
        except Exception as e:
            return {'error': str(e)}
        return {}
    
    def _get_available_qualities(self, info: dict) -> list:
        qualities = set()
        for f in info.get('formats', []):
            height = f.get('height')
            if height:
                if height >= 2160:
                    qualities.add('2160')
                elif height >= 1080:
                    qualities.add('1080')
                elif height >= 720:
                    qualities.add('720')
                elif height >= 480:
                    qualities.add('480')
                elif height >= 360:
                    qualities.add('360')
        return sorted(list(qualities), key=int, reverse=True) if qualities else ['best']


class InstagramDownloader(BaseDownloader):
    """Instagram indirici - 2FA ve güvenli oturum desteği."""
    
    def __init__(self, download_path: Path):
        super().__init__(download_path)
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            dirname_pattern=str(download_path),
            filename_pattern='{shortcode}',
        )
        self.logged_in = False
        self.username = None
        self._session_file = None
    
    def login(self, username: str, password: str) -> tuple:
        """Instagram'a giriş yap."""
        try:
            self.loader.login(username, password)
            self.logged_in = True
            self.username = username
            return True, "Giriş başarılı!"
        except instaloader.exceptions.BadCredentialsException:
            return False, "Kullanıcı adı veya şifre hatalı!"
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            # 2FA gerekli - özel hata kodu döndür
            self.username = username
            return False, "2FA_REQUIRED"
        except instaloader.exceptions.ConnectionException as e:
            if "checkpoint" in str(e).lower():
                return False, "Instagram güvenlik doğrulaması gerekli. Lütfen tarayıcıdan giriş yapın."
            return False, f"Bağlantı hatası: {str(e)}"
        except Exception as e:
            return False, f"Giriş hatası: {str(e)}"
    
    def login_with_2fa(self, username: str, password: str, code: str) -> tuple:
        """2FA kodu ile giriş yap."""
        try:
            self.loader.two_factor_login(code)
            self.logged_in = True
            self.username = username
            return True, "Giriş başarılı!"
        except instaloader.exceptions.BadCredentialsException:
            return False, "Geçersiz doğrulama kodu!"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    def load_session(self, username: str) -> bool:
        """Kayıtlı oturumu yükle."""
        try:
            self.loader.load_session_from_file(username)
            self.logged_in = True
            self.username = username
            self._session_file = self._get_session_file(username)
            return True
        except Exception:
            return False
    
    def save_session(self, username: str):
        """Oturumu kaydet."""
        try:
            self.loader.save_session_to_file(username)
            self._session_file = self._get_session_file(username)
        except Exception:
            pass
    
    def logout(self) -> bool:
        """Oturumu kapat ve TÜM dosyaları temizle."""
        try:
            username = self.username
            if username:
                import shutil
                
                # 1. Home dizinindeki session dosyaları
                home_dir = Path.home()
                home_patterns = [
                    f'.instaloader-session-{username}',
                    f'{username}_session',
                    f'.{username}_session',
                    f'{username}',  # Bazen sadece kullanıcı adı olarak kaydedilir
                ]
                for pattern in home_patterns:
                    path = home_dir / pattern
                    if path.exists():
                        if path.is_file():
                            path.unlink()
                        elif path.is_dir():
                            shutil.rmtree(path, ignore_errors=True)
                
                # 2. İndirme klasöründeki session dosyaları
                if self.download_path.exists():
                    for item in self.download_path.iterdir():
                        if username.lower() in item.name.lower():
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except:
                                pass
                
                # 3. Uygulama klasöründeki (current dir) session dosyaları
                app_dir = Path(__file__).parent
                if app_dir.exists():
                    for item in app_dir.iterdir():
                        if username.lower() in item.name.lower():
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except:
                                pass
                
                # 4. AppData klasörleri
                appdata_dirs = [
                    home_dir / "AppData" / "Local" / "Instaloader",
                    home_dir / "AppData" / "Roaming" / "Instaloader",
                    home_dir / ".config" / "instaloader",
                ]
                for appdata_dir in appdata_dirs:
                    if appdata_dir.exists():
                        for item in appdata_dir.glob(f"*{username}*"):
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except:
                                pass
                
                # 5. Current working directory
                cwd = Path.cwd()
                if cwd != app_dir and cwd != self.download_path:
                    for item in cwd.iterdir():
                        if username.lower() in item.name.lower():
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item, ignore_errors=True)
                            except:
                                pass
            
            # Loader'ı sıfırla
            self.loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                dirname_pattern=str(self.download_path),
                filename_pattern='{shortcode}',
            )
            
            self.logged_in = False
            self.username = None
            self._session_file = None
            
            return True
        except Exception as e:
            print(f"Logout error: {e}")
            return False
    
    def _get_session_file(self, username: str) -> Optional[Path]:
        """Session dosya yolunu al."""
        session_file = Path.home() / f".instaloader-session-{username}"
        if session_file.exists():
            return session_file
        return None
    
    def download(self, url: str, as_audio: bool = False, quality: str = "best",
                 progress_callback: Optional[ProgressCallback] = None,
                 filename_template: str = None, download_subtitles: bool = False) -> DownloadResult:
        result = DownloadResult(success=False, platform="instagram", source_url=url)
        
        try:
            if progress_callback:
                progress_callback.update(10, "Bağlanılıyor...", "")
            
            story_username, story_id = self._extract_story_identifiers(url)
            if story_username and story_id:
                if progress_callback:
                    progress_callback.update(30, "Hikaye bilgileri alınıyor...", "")
                return self._download_story(story_username, story_id, progress_callback, url)

            shortcode = self._extract_shortcode(url)
            if not shortcode:
                result.error = "Geçersiz Instagram URL'si"
                return result

            if progress_callback:
                progress_callback.update(30, "Video bilgileri alınıyor...", "")

            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            if progress_callback:
                progress_callback.update(50, "İndiriliyor...", "")

            self.loader.download_post(post, target=str(self.download_path))

            video_file = self._find_latest_downloaded_file(shortcode)

            if video_file:
                if progress_callback:
                    progress_callback.update(100, "Tamamlandı!", "")

                result.success = True
                result.filename = video_file.name
                result.filepath = str(video_file)
                result.filesize = video_file.stat().st_size
            else:
                result.error = "Video dosyası bulunamadı"
        
        except instaloader.exceptions.LoginRequiredException:
            result.error = "Bu içerik için Instagram girişi gerekli"
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            result.error = "Bu içerik gizli bir hesaba ait"
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def get_info(self, url: str) -> Dict[str, Any]:
        try:
            story_username, story_id = self._extract_story_identifiers(url)
            if story_username and story_id:
                return {
                    'title': f"Story • @{story_username}",
                    'uploader': story_username,
                    'thumbnail': '',
                    'duration': 0,
                    'qualities': ['best'],
                }

            shortcode = self._extract_shortcode(url)
            if shortcode:
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                return {
                    'title': post.caption[:50] if post.caption else shortcode,
                    'uploader': post.owner_username,
                    'thumbnail': '',
                    'duration': 0,
                    'qualities': ['best'],
                }
        except Exception:
            pass
        return {}
    
    def _extract_shortcode(self, url: str) -> Optional[str]:
        import re
        patterns = [
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
            r'instagram\.com/reels/([A-Za-z0-9_-]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None


    def _find_latest_downloaded_file(self, shortcode: str) -> Optional[Path]:
        candidates = [
            file for file in self.download_path.glob(f"*{shortcode}*.mp4")
            if file.is_file()
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda file: file.stat().st_mtime)

    def _extract_story_identifiers(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        import re

        match = re.search(r'instagram\.com/stories/([^/]+)/([^/?#]+)', url)
        if not match:
            return None, None

        username = match.group(1)
        story_id = match.group(2).split('?')[0]
        if not username or not story_id:
            return None, None

        return username, story_id

    def _download_story(self, username: str, story_id: str, progress_callback: Optional[ProgressCallback], source_url: str) -> DownloadResult:
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

        downloaded_file = self._find_latest_downloaded_file(story_id)
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
    """Platform için uygun indiriciyi oluştur."""
    if platform == 'youtube':
        return YTDLPDownloader(download_path, 'youtube')
    elif platform == 'tiktok':
        return YTDLPDownloader(download_path, 'tiktok')
    elif platform == 'instagram':
        return InstagramDownloader(download_path)
    elif platform in {'facebook', 'twitter', 'vimeo', 'dailymotion', 'twitch'}:
        return YTDLPDownloader(download_path, platform)
    else:
        raise ValueError(f"Desteklenmeyen platform: {platform}")
