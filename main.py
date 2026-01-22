"""
Video Downloader Pro - Modern UI
YouTube, TikTok, Instagram video ve MP3 indirme
2FA desteği, güvenli oturum yönetimi
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

from utils import detect_platform, format_size, get_download_folder, get_platform_icon, get_platform_color, check_ffmpeg
from downloader import create_downloader, ProgressCallback, InstagramDownloader, DownloadResult, YTDLPDownloader


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


FILENAME_TEMPLATES = {
    "%(title)s": "Video Başlığı",
    "%(title)s - %(uploader)s": "Başlık - Kanal",
    "%(uploader)s - %(title)s": "Kanal - Başlık",
    "%(upload_date)s - %(title)s": "Tarih - Başlık",
}


class QueueItem:
    def __init__(self, url: str, platform: str, quality: str = "best", 
                 as_audio: bool = False, title: str = ""):
        self.url = url
        self.platform = platform
        self.quality = quality
        self.as_audio = as_audio
        self.title = title or url[:50]
        self.status = "pending"
        self.progress = 0
        self.error = ""


class QueueItemWidget(ctk.CTkFrame):
    def __init__(self, master, item: QueueItem, on_remove: callable, **kwargs):
        super().__init__(master, **kwargs)
        self.item = item
        self.on_remove = on_remove
        self.configure(fg_color=("gray90", "gray17"), corner_radius=8)
        
        icon = get_platform_icon(item.platform)
        ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=18), width=30).pack(side="left", padx=(8, 5))
        
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        title = item.title[:35] + "..." if len(item.title) > 38 else item.title
        ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        
        quality_text = "MP3" if item.as_audio else f"{item.quality}p" if item.quality != "best" else "En İyi"
        ctk.CTkLabel(info_frame, text=quality_text, font=ctk.CTkFont(size=10), 
                     text_color=("gray50", "gray60"), anchor="w").pack(fill="x")
        
        if item.status == "pending":
            ctk.CTkButton(self, text="✕", width=30, height=30, corner_radius=6,
                         fg_color=("gray80", "gray25"), hover_color=("#FF6B6B", "#CC5555"),
                         command=lambda: on_remove(item)).pack(side="right", padx=8, pady=6)
        elif item.status == "downloading":
            ctk.CTkLabel(self, text="⏳", font=ctk.CTkFont(size=16)).pack(side="right", padx=12)
        elif item.status == "completed":
            ctk.CTkLabel(self, text="✅", font=ctk.CTkFont(size=16)).pack(side="right", padx=12)
        elif item.status == "error":
            ctk.CTkLabel(self, text="❌", font=ctk.CTkFont(size=16)).pack(side="right", padx=12)


class VideoPreviewFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=("gray90", "gray17"), corner_radius=12)
        self.video_info = None
        
        self.title_label = ctk.CTkLabel(self, text="📺 Video Önizleme", 
                                         font=ctk.CTkFont(size=14, weight="bold"))
        self.title_label.pack(fill="x", padx=15, pady=(12, 5))
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        self.empty_label = ctk.CTkLabel(self.content_frame, 
                                         text="URL yapıştırın, video bilgileri burada görünecek",
                                         font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
        self.empty_label.pack(pady=10)
        
        self.preview_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        self.info_container = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        self.info_container.pack(fill="both", expand=True)
        
        self.video_title_label = ctk.CTkLabel(self.info_container, text="", 
                                               font=ctk.CTkFont(size=13, weight="bold"),
                                               anchor="w", wraplength=400)
        self.video_title_label.pack(fill="x")
        
        self.uploader_label = ctk.CTkLabel(self.info_container, text="",
                                            font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"), anchor="w")
        self.uploader_label.pack(fill="x")
        
        self.duration_label = ctk.CTkLabel(self.info_container, text="",
                                            font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"), anchor="w")
        self.duration_label.pack(fill="x")
        
        self.loading_label = ctk.CTkLabel(self.content_frame, text="⏳ Video bilgileri yükleniyor...",
                                           font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
    
    def show_loading(self):
        self.empty_label.pack_forget()
        self.preview_container.pack_forget()
        self.loading_label.pack(pady=10)
    
    def show_empty(self):
        self.loading_label.pack_forget()
        self.preview_container.pack_forget()
        self.empty_label.pack(pady=10)
    
    def show_preview(self, info: dict):
        self.video_info = info
        self.empty_label.pack_forget()
        self.loading_label.pack_forget()
        
        title = info.get('title', 'Bilinmiyor')
        if len(title) > 60:
            title = title[:57] + "..."
        self.video_title_label.configure(text=title)
        
        uploader = info.get('uploader', '')
        self.uploader_label.configure(text=f"📺 {uploader}" if uploader else "")
        
        duration = info.get('duration', 0)
        if duration:
            mins, secs = divmod(duration, 60)
            hours, mins = divmod(mins, 60)
            duration_str = f"⏱️ {hours}:{mins:02d}:{secs:02d}" if hours else f"⏱️ {mins}:{secs:02d}"
            self.duration_label.configure(text=duration_str)
        else:
            self.duration_label.configure(text="")
        
        self.preview_container.pack(fill="x", pady=5)
    
    def get_qualities(self) -> list:
        if self.video_info:
            return self.video_info.get('qualities', ['best'])
        return ['best']


class InstagramLoginDialog(ctk.CTkToplevel):
    """Instagram giriş penceresi - 2FA desteği ile."""
    
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.title("📸 Instagram Giriş")
        self.geometry("420x400")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        self.downloader = None
        self.awaiting_2fa = False
        self.temp_username = None
        self.temp_password = None
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (210)
        y = (self.winfo_screenheight() // 2) - (200)
        self.geometry(f"420x400+{x}+{y}")
    
    def setup_ui(self):
        # Scrollable container for all content
        main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        ctk.CTkLabel(main_container, text="📸 Instagram Giriş", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(main_container, text="Private videolara erişmek için giriş yapın", 
                     font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack(pady=(0, 15))
        
        # Form
        form_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)
        
        # Kullanıcı adı
        ctk.CTkLabel(form_frame, text="Kullanıcı Adı", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x")
        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="instagram_kullanici_adi", 
                                            height=40, corner_radius=10)
        self.username_entry.pack(fill="x", pady=(5, 12))
        
        # Şifre
        ctk.CTkLabel(form_frame, text="Şifre", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x")
        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="••••••••", show="•", 
                                            height=40, corner_radius=10)
        self.password_entry.pack(fill="x", pady=(5, 12))
        
        # 2FA Kodu (başlangıçta gizli)
        self.twofa_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        
        ctk.CTkLabel(self.twofa_frame, text="🔐 Doğrulama Kodu", 
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
                     text_color=("#E4405F", "#E4405F")).pack(fill="x")
        ctk.CTkLabel(self.twofa_frame, text="Instagram'dan gelen 6 haneli kodu girin", 
                     font=ctk.CTkFont(size=10), text_color=("gray50", "gray60"), anchor="w").pack(fill="x")
        self.twofa_entry = ctk.CTkEntry(self.twofa_frame, placeholder_text="123456", 
                                         height=45, corner_radius=10, font=ctk.CTkFont(size=16),
                                         justify="center")
        self.twofa_entry.pack(fill="x", pady=(8, 12))
        
        # Giriş butonu
        self.login_btn = ctk.CTkButton(form_frame, text="Giriş Yap", height=45, corner_radius=10,
                                        font=ctk.CTkFont(size=14, weight="bold"), 
                                        fg_color=("#E4405F", "#C13584"),
                                        hover_color=("#C13584", "#A02570"),
                                        command=self.do_login)
        self.login_btn.pack(fill="x", pady=(8, 0))
        
        # Durum mesajı
        self.status_label = ctk.CTkLabel(main_container, text="", font=ctk.CTkFont(size=11), 
                                          text_color="#FF6B6B", wraplength=350)
        self.status_label.pack(pady=15)
        
        # Uyarı
        ctk.CTkLabel(main_container, 
                     text="⚠️ Giriş bilgileriniz sadece bu oturum için kullanılır", 
                     font=ctk.CTkFont(size=10), text_color=("gray50", "gray60")).pack(pady=(0, 10))
    
    def show_2fa_input(self):
        """2FA giriş alanını göster."""
        self.awaiting_2fa = True
        self.twofa_frame.pack(fill="x", pady=(0, 12), before=self.login_btn)
        self.twofa_entry.focus()
        self.login_btn.configure(text="Doğrula")
        self.status_label.configure(
            text="📱 Instagram hesabınıza gönderilen doğrulama kodunu girin",
            text_color=("#E4405F", "#E4405F")
        )
    
    def do_login(self):
        if self.awaiting_2fa:
            self.verify_2fa()
            return
        
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.status_label.configure(text="Lütfen tüm alanları doldurun", text_color="#FF6B6B")
            return
        
        self.temp_username = username
        self.temp_password = password
        self.login_btn.configure(state="disabled", text="Giriş yapılıyor...")
        self.status_label.configure(text="", text_color="gray60")
        
        def login_thread():
            self.downloader = InstagramDownloader(get_download_folder())
            success, message = self.downloader.login(username, password)
            self.after(0, lambda: self.handle_login_result(success, message))
        
        threading.Thread(target=login_thread, daemon=True).start()
    
    def handle_login_result(self, success: bool, message: str):
        if success:
            self.downloader.save_session(self.temp_username)
            self.on_login_success(self.temp_username, self.downloader)
            self.destroy()
        elif message == "2FA_REQUIRED":
            self.login_btn.configure(state="normal")
            self.show_2fa_input()
        else:
            self.status_label.configure(text=message, text_color="#FF6B6B")
            self.login_btn.configure(state="normal", text="Giriş Yap")
    
    def verify_2fa(self):
        code = self.twofa_entry.get().strip()
        
        if not code or len(code) != 6 or not code.isdigit():
            self.status_label.configure(text="Lütfen 6 haneli doğrulama kodunu girin", text_color="#FF6B6B")
            return
        
        self.login_btn.configure(state="disabled", text="Doğrulanıyor...")
        
        def verify_thread():
            success, message = self.downloader.login_with_2fa(self.temp_username, self.temp_password, code)
            self.after(0, lambda: self.handle_2fa_result(success, message))
        
        threading.Thread(target=verify_thread, daemon=True).start()
    
    def handle_2fa_result(self, success: bool, message: str):
        if success:
            self.downloader.save_session(self.temp_username)
            self.on_login_success(self.temp_username, self.downloader)
            self.destroy()
        else:
            self.status_label.configure(text=message, text_color="#FF6B6B")
            self.login_btn.configure(state="normal", text="Doğrula")
            self.twofa_entry.delete(0, "end")


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, current_template: str, on_save: callable):
        super().__init__(master)
        self.on_save = on_save
        self.current_template = current_template
        
        self.title("⚙️ Ayarlar")
        self.geometry("450x320")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (225)
        y = (self.winfo_screenheight() // 2) - (160)
        self.geometry(f"450x320+{x}+{y}")
    
    def setup_ui(self):
        ctk.CTkLabel(self, text="⚙️ Dosya Adı Şablonu", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(25, 15))
        ctk.CTkLabel(self, text="İndirilen dosyaların nasıl adlandırılacağını seçin",
                     font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack(pady=(0, 15))
        
        self.template_var = ctk.StringVar(value=self.current_template)
        
        for template, description in FILENAME_TEMPLATES.items():
            radio = ctk.CTkRadioButton(self, text=description, variable=self.template_var, value=template,
                                        font=ctk.CTkFont(size=13))
            radio.pack(anchor="w", padx=40, pady=5)
        
        ctk.CTkButton(self, text="💾 Kaydet", width=120, height=40,
                     command=self.save_and_close).pack(pady=25)
    
    def save_and_close(self):
        self.on_save(self.template_var.get())
        self.destroy()


class DownloadHistoryItem(ctk.CTkFrame):
    def __init__(self, master, filename: str, platform: str, size: str, filepath: str, **kwargs):
        super().__init__(master, **kwargs)
        self.filepath = filepath
        self.configure(fg_color=("gray90", "gray17"), corner_radius=8)
        
        ctk.CTkLabel(self, text=get_platform_icon(platform), font=ctk.CTkFont(size=20), width=30).pack(side="left", padx=(10, 5))
        
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)
        
        display_name = filename[:40] + "..." if len(filename) > 43 else filename
        ctk.CTkLabel(info_frame, text=display_name, font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{platform.capitalize()} • {size}", font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray60"), anchor="w").pack(fill="x")
        
        ctk.CTkButton(self, text="📂", width=35, height=35, corner_radius=8,
                     fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"),
                     command=self.open_folder).pack(side="right", padx=10, pady=8)
    
    def open_folder(self):
        if self.filepath and os.path.exists(self.filepath):
            os.startfile(os.path.dirname(self.filepath))


class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🎬 Syronss's Media Downloader")
        self.geometry("650x850")
        self.minsize(600, 700)
        
        self.settings_file = Path.home() / ".video_downloader_settings.json"
        self.load_settings()
        
        self.format_var = ctk.StringVar(value="video")
        self.quality_var = ctk.StringVar(value="En İyi")
        self.is_downloading = False
        self.instagram_downloader: Optional[InstagramDownloader] = None
        self.instagram_username: Optional[str] = None
        self.download_history = []
        self.download_queue: List[QueueItem] = []
        self.current_video_info = None
        self.filename_template = self.settings.get("filename_template", "%(title)s")
        
        self.ffmpeg_available = check_ffmpeg()
        self.load_history()
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (325)
        y = (self.winfo_screenheight() // 2) - (425)
        self.geometry(f"650x850+{x}+{y}")
    
    def setup_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.main_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)
        
        self.footer_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(10, 0))
        
        self.main_frame = self.main_scroll
        
        self.create_header()
        self.create_url_input()
        self.create_video_preview()
        self.create_options_panel()
        self.create_download_button()
        self.create_progress_section()
        self.create_queue_section()
        self.create_history_section()
        self.create_footer()
    
    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header_frame, text="🎬 Syronss's Media Downloader",
                     font=ctk.CTkFont(size=26, weight="bold")).pack()
        ctk.CTkLabel(header_frame, text="YouTube • TikTok • Instagram",
                     font=ctk.CTkFont(size=13), text_color=("gray50", "gray60")).pack(pady=(3, 0))
    
    def create_url_input(self):
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(input_frame, text="🔗 Video URL'si",
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x", pady=(0, 6))
        
        entry_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        entry_frame.pack(fill="x")
        
        self.url_entry = ctk.CTkEntry(entry_frame, placeholder_text="YouTube, TikTok veya Instagram URL'sini yapıştırın...",
                                       height=48, corner_radius=10, font=ctk.CTkFont(size=13))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.fetch_btn = ctk.CTkButton(entry_frame, text="🔍", width=50, height=48, corner_radius=10,
                                        command=self.fetch_video_info)
        self.fetch_btn.pack(side="right")
        
        self.platform_label = ctk.CTkLabel(input_frame, text="", font=ctk.CTkFont(size=11),
                                            text_color=("gray50", "gray60"))
        self.platform_label.pack(anchor="w", pady=(5, 0))
        
        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        self.url_entry.bind("<Return>", lambda e: self.fetch_video_info())
    
    def create_video_preview(self):
        self.preview_frame = VideoPreviewFrame(self.main_frame)
        self.preview_frame.pack(fill="x", pady=10)
    
    def create_options_panel(self):
        options_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray90", "gray17"), corner_radius=12)
        options_frame.pack(fill="x", pady=10, ipady=8)
        
        row1 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(10, 5))
        
        format_frame = ctk.CTkFrame(row1, fg_color="transparent")
        format_frame.pack(side="left", expand=True)
        
        ctk.CTkLabel(format_frame, text="📦 Format", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        format_buttons = ctk.CTkFrame(format_frame, fg_color="transparent")
        format_buttons.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkRadioButton(format_buttons, text="🎬 Video", variable=self.format_var, value="video",
                           font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 15))
        ctk.CTkRadioButton(format_buttons, text="🎵 MP3", variable=self.format_var, value="audio",
                           font=ctk.CTkFont(size=12)).pack(side="left")
        
        quality_frame = ctk.CTkFrame(row1, fg_color="transparent")
        quality_frame.pack(side="right", expand=True)
        
        ctk.CTkLabel(quality_frame, text="📊 Kalite", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        
        self.quality_menu = ctk.CTkOptionMenu(quality_frame, values=["En İyi", "1080p", "720p", "480p", "360p"],
                                               variable=self.quality_var, width=120, height=32)
        self.quality_menu.pack(anchor="w", pady=(5, 0))
    
    def create_download_button(self):
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        self.download_btn = ctk.CTkButton(btn_frame, text="📥 İNDİR", height=52, corner_radius=12,
                                           font=ctk.CTkFont(size=17, weight="bold"),
                                           fg_color=("#6366F1", "#5B5BD6"), hover_color=("#4F46E5", "#4C4CC4"),
                                           command=self.start_download)
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.add_queue_btn = ctk.CTkButton(btn_frame, text="➕ Kuyruğa Ekle", height=52, corner_radius=12,
                                            font=ctk.CTkFont(size=13), width=130,
                                            fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"),
                                            text_color=("gray30", "gray80"), command=self.add_to_queue)
        self.add_queue_btn.pack(side="right")
    
    def create_progress_section(self):
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=8)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10, corner_radius=5,
                                                 progress_color=("#6366F1", "#5B5BD6"))
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Hazır", font=ctk.CTkFont(size=11),
                                          text_color=("gray50", "gray60"))
        self.status_label.pack(pady=(6, 0))
    
    def create_queue_section(self):
        queue_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        queue_frame.pack(fill="x", pady=(10, 5))
        
        header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="📋 İndirme Kuyruğu", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        
        self.queue_count_label = ctk.CTkLabel(header, text="(0)", font=ctk.CTkFont(size=12),
                                               text_color=("gray50", "gray60"))
        self.queue_count_label.pack(side="left", padx=5)
        
        self.start_queue_btn = ctk.CTkButton(header, text="▶️ Başlat", width=80, height=28, corner_radius=6,
                                              fg_color=("#22C55E", "#16A34A"), hover_color=("#16A34A", "#15803D"),
                                              command=self.start_queue)
        self.start_queue_btn.pack(side="right")
        
        self.queue_scroll = ctk.CTkScrollableFrame(queue_frame, fg_color="transparent", height=100)
        self.queue_scroll.pack(fill="x", pady=(8, 0))
        
        self.queue_empty_label = ctk.CTkLabel(self.queue_scroll, text="Kuyruk boş",
                                               font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
        self.queue_empty_label.pack(pady=15)
    
    def create_history_section(self):
        history_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        history_frame.pack(fill="both", expand=True, pady=(10, 5))
        
        header = ctk.CTkFrame(history_frame, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="📂 Son İndirilenler", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="🗑️", width=35, height=28, corner_radius=6,
                     fg_color=("gray80", "gray25"), hover_color=("gray70", "gray35"),
                     command=self.clear_history).pack(side="right")
        
        self.history_scroll = ctk.CTkScrollableFrame(history_frame, fg_color="transparent", height=150)
        self.history_scroll.pack(fill="both", expand=True, pady=(8, 0))
        
        self.display_history()
    
    def create_footer(self):
        self.instagram_btn = ctk.CTkButton(self.footer_frame, text="📸 Instagram", width=120, height=35, corner_radius=8,
                                            fg_color=("gray85", "gray20"), hover_color=("gray75", "gray30"),
                                            text_color=("gray30", "gray80"), font=ctk.CTkFont(size=12),
                                            command=self.show_instagram_login)
        self.instagram_btn.pack(side="left")
        
        ctk.CTkButton(self.footer_frame, text="⚙️", width=35, height=35, corner_radius=8,
                     fg_color=("gray85", "gray20"), hover_color=("gray75", "gray30"),
                     command=self.show_settings).pack(side="left", padx=8)
        
        self.folder_btn = ctk.CTkButton(self.footer_frame, text=f"📁 {self.download_path.name}", width=150, height=35, corner_radius=8,
                                         fg_color=("gray85", "gray20"), hover_color=("gray75", "gray30"),
                                         text_color=("gray30", "gray80"), font=ctk.CTkFont(size=12),
                                         command=self.change_download_folder)
        self.folder_btn.pack(side="right")
        
        self.theme_switch = ctk.CTkSwitch(self.footer_frame, text="🌙", width=40,
                                           command=self.toggle_theme, onvalue="dark", offvalue="light")
        self.theme_switch.pack(side="right", padx=10)
        self.theme_switch.select()
    
    def on_url_change(self, event=None):
        url = self.url_entry.get().strip()
        if url:
            platform = detect_platform(url)
            if platform:
                icon = get_platform_icon(platform)
                self.platform_label.configure(text=f"{icon} {platform.capitalize()} tespit edildi",
                                               text_color=get_platform_color(platform))
            else:
                self.platform_label.configure(text="⚠️ Desteklenmeyen platform", text_color="#FF6B6B")
        else:
            self.platform_label.configure(text="")
            self.preview_frame.show_empty()
    
    def fetch_video_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        platform = detect_platform(url)
        if not platform:
            messagebox.showerror("Hata", "Desteklenmeyen URL!")
            return
        
        self.preview_frame.show_loading()
        self.fetch_btn.configure(state="disabled")
        
        def fetch_thread():
            try:
                downloader = create_downloader(platform, self.download_path)
                info = downloader.get_info(url)
                self.after(0, lambda: self.handle_video_info(info, platform))
            except Exception as e:
                self.after(0, lambda: self.handle_video_info({'error': str(e)}, platform))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def handle_video_info(self, info: dict, platform: str):
        self.fetch_btn.configure(state="normal")
        
        if 'error' in info:
            self.preview_frame.show_empty()
            messagebox.showerror("Hata", f"Video bilgisi alınamadı: {info['error']}")
            return
        
        self.current_video_info = info
        self.current_video_info['platform'] = platform
        self.preview_frame.show_preview(info)
        
        qualities = info.get('qualities', ['best'])
        quality_labels = []
        for q in qualities:
            if q == 'best':
                quality_labels.append("En İyi")
            else:
                quality_labels.append(f"{q}p")
        
        if quality_labels:
            self.quality_menu.configure(values=quality_labels)
            self.quality_var.set(quality_labels[0])
    
    def get_selected_quality(self) -> str:
        quality = self.quality_var.get()
        if quality == "En İyi":
            return "best"
        return quality.replace("p", "")
    
    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin!")
            return
        
        platform = detect_platform(url)
        if not platform:
            messagebox.showerror("Hata", "Desteklenmeyen URL!")
            return
        
        title = ""
        if self.current_video_info:
            title = self.current_video_info.get('title', '')
        
        item = QueueItem(url=url, platform=platform, quality=self.get_selected_quality(),
                        as_audio=self.format_var.get() == "audio", title=title or url[:40])
        
        self.download_queue.append(item)
        self.update_queue_display()
        
        self.url_entry.delete(0, "end")
        self.platform_label.configure(text="")
        self.preview_frame.show_empty()
        self.current_video_info = None
    
    def remove_from_queue(self, item: QueueItem):
        if item in self.download_queue:
            self.download_queue.remove(item)
            self.update_queue_display()
    
    def update_queue_display(self):
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()
        
        self.queue_count_label.configure(text=f"({len(self.download_queue)})")
        
        if not self.download_queue:
            self.queue_empty_label = ctk.CTkLabel(self.queue_scroll, text="Kuyruk boş",
                                                   font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
            self.queue_empty_label.pack(pady=15)
            return
        
        for item in self.download_queue:
            widget = QueueItemWidget(self.queue_scroll, item, self.remove_from_queue)
            widget.pack(fill="x", pady=2)
    
    def start_queue(self):
        if not self.download_queue:
            messagebox.showinfo("Bilgi", "Kuyruk boş!")
            return
        
        if self.is_downloading:
            return
        
        self.process_next_queue_item()
    
    def process_next_queue_item(self):
        pending_items = [item for item in self.download_queue if item.status == "pending"]
        
        if not pending_items:
            self.is_downloading = False
            self.download_btn.configure(state="normal", text="📥 İNDİR")
            messagebox.showinfo("Tamamlandı", "Tüm indirmeler tamamlandı!")
            return
        
        item = pending_items[0]
        item.status = "downloading"
        self.update_queue_display()
        
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ Kuyruk işleniyor...")
        
        thread = threading.Thread(target=self.download_queue_item, args=(item,), daemon=True)
        thread.start()
    
    def download_queue_item(self, item: QueueItem):
        try:
            if item.platform == "instagram" and self.instagram_downloader:
                downloader = self.instagram_downloader
            else:
                downloader = create_downloader(item.platform, self.download_path)
            
            def progress_update(percent, status, speed):
                self.after(0, lambda: self.update_progress(percent, status, speed))
            
            callback = ProgressCallback(progress_update)
            result = downloader.download(item.url, item.as_audio, item.quality, callback, self.filename_template)
            
            if result.success:
                item.status = "completed"
                self.after(0, lambda: self.add_to_history(result))
            else:
                item.status = "error"
                item.error = result.error
            
            self.after(0, self.update_queue_display)
            self.after(100, self.process_next_queue_item)
        
        except Exception as e:
            item.status = "error"
            item.error = str(e)
            self.after(0, self.update_queue_display)
            self.after(100, self.process_next_queue_item)
    
    def start_download(self):
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir video URL'si girin!")
            return
        
        platform = detect_platform(url)
        if not platform:
            messagebox.showerror("Hata", "Desteklenmeyen URL!")
            return
        
        if self.is_downloading:
            return
        
        as_audio = self.format_var.get() == "audio"
        if as_audio and not self.ffmpeg_available:
            messagebox.showwarning("FFmpeg Gerekli", "MP3 dönüşümü için FFmpeg kurulu olmalı.")
            return
        
        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="⏳ İndiriliyor...")
        self.progress_bar.set(0)
        self.status_label.configure(text="Başlatılıyor...")
        
        quality = self.get_selected_quality()
        
        thread = threading.Thread(target=self.download_thread, args=(url, platform, as_audio, quality), daemon=True)
        thread.start()
    
    def download_thread(self, url: str, platform: str, as_audio: bool, quality: str):
        try:
            if platform == "instagram" and self.instagram_downloader:
                downloader = self.instagram_downloader
            else:
                downloader = create_downloader(platform, self.download_path)
            
            def progress_update(percent, status, speed):
                self.after(0, lambda: self.update_progress(percent, status, speed))
            
            callback = ProgressCallback(progress_update)
            result = downloader.download(url, as_audio, quality, callback, self.filename_template)
            
            self.after(0, lambda: self.handle_download_result(result))
        
        except Exception as e:
            self.after(0, lambda: self.handle_download_error(str(e)))
    
    def update_progress(self, percent: float, status: str, speed: str):
        self.progress_bar.set(percent / 100)
        status_text = f"{status} {percent:.0f}%"
        if speed:
            status_text += f" • {speed}"
        self.status_label.configure(text=status_text)
    
    def handle_download_result(self, result: DownloadResult):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="📥 İNDİR")
        
        if result.success:
            self.progress_bar.set(1)
            self.status_label.configure(text="✅ İndirme tamamlandı!")
            self.add_to_history(result)
            self.url_entry.delete(0, "end")
            self.platform_label.configure(text="")
            self.preview_frame.show_empty()
            self.current_video_info = None
        else:
            self.progress_bar.set(0)
            self.status_label.configure(text=f"❌ Hata: {result.error[:50]}")
            messagebox.showerror("İndirme Hatası", result.error)
    
    def handle_download_error(self, error: str):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="📥 İNDİR")
        self.progress_bar.set(0)
        self.status_label.configure(text="❌ Hata")
        messagebox.showerror("İndirme Hatası", error)
    
    def add_to_history(self, result: DownloadResult):
        item = {"filename": result.filename, "platform": result.platform,
                "size": format_size(result.filesize), "filepath": result.filepath,
                "date": datetime.now().isoformat()}
        self.download_history.insert(0, item)
        self.download_history = self.download_history[:20]
        self.save_history()
        self.display_history()
    
    def display_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        
        if not self.download_history:
            ctk.CTkLabel(self.history_scroll, text="Henüz indirme yapılmadı",
                         font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(pady=20)
            return
        
        for item in self.download_history[:8]:
            history_item = DownloadHistoryItem(self.history_scroll, filename=item["filename"],
                                                platform=item["platform"], size=item["size"], filepath=item["filepath"])
            history_item.pack(fill="x", pady=2)
    
    def clear_history(self):
        if messagebox.askyesno("Onay", "İndirme geçmişini temizlemek istediğinizden emin misiniz?"):
            self.download_history = []
            self.save_history()
            self.display_history()
    
    def save_history(self):
        try:
            history_file = self.download_path / "history.json"
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self.download_history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_history(self):
        try:
            history_file = self.download_path / "history.json"
            if history_file.exists():
                with open(history_file, "r", encoding="utf-8") as f:
                    self.download_history = json.load(f)
        except Exception:
            self.download_history = []
    
    def show_instagram_login(self):
        if self.instagram_username:
            if messagebox.askyesno("Instagram Çıkış", 
                                    f"@{self.instagram_username} olarak giriş yapılmış.\n\n"
                                    "Çıkış yapmak ve tüm oturum bilgilerini silmek ister misiniz?"):
                # Güvenli çıkış - tüm dosyaları temizle
                if self.instagram_downloader:
                    self.instagram_downloader.logout()
                
                self.instagram_downloader = None
                self.instagram_username = None
                self.instagram_btn.configure(text="📸 Instagram")
                messagebox.showinfo("Çıkış Yapıldı", "Instagram oturumu güvenli bir şekilde kapatıldı ve tüm oturum dosyaları silindi.")
        else:
            InstagramLoginDialog(self, self.on_instagram_login)
    
    def on_instagram_login(self, username: str, downloader: InstagramDownloader):
        self.instagram_username = username
        self.instagram_downloader = downloader
        self.instagram_btn.configure(text=f"📸 @{username[:10]}")
    
    def show_settings(self):
        SettingsDialog(self, self.filename_template, self.on_settings_save)
    
    def on_settings_save(self, template: str):
        self.filename_template = template
        self.settings["filename_template"] = template
        self.save_settings()
    
    def change_download_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = Path(folder)
            self.folder_btn.configure(text=f"📁 {self.download_path.name}")
            self.save_settings()
            messagebox.showinfo("Başarılı", f"İndirme klasörü değiştirildi:\n{folder}")
    
    def save_settings(self):
        try:
            self.settings["download_path"] = str(self.download_path)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                    saved_path = Path(self.settings.get("download_path", ""))
                    if saved_path.exists():
                        self.download_path = saved_path
                    else:
                        self.download_path = get_download_folder()
            else:
                self.settings = {}
                self.download_path = get_download_folder()
        except Exception:
            self.settings = {}
            self.download_path = get_download_folder()
    
    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)


def main():
    app = VideoDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
