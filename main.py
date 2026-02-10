"""
Syronss's Media Downloader v2.0 - Modern UI
YouTube, TikTok, Instagram, Facebook, X, Vimeo, Dailymotion, Twitch
Multi-language, queue system, stats, batch import, auto-folder, notifications
"""

import multiprocessing
multiprocessing.freeze_support()

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import json

from constants import (
    APP_NAME, APP_VERSION, COLORS, FILENAME_TEMPLATES,
    DEFAULT_SETTINGS, MAX_HISTORY_ITEMS, MAX_HISTORY_DISPLAY,
)
from i18n import t, set_language, get_language
from utils import (
    detect_platform, format_size, get_download_folder, get_platform_icon,
    get_platform_color, check_ffmpeg, normalize_media_url, Debouncer,
    flash_taskbar_icon, get_platform_download_path, check_ytdlp_update,
    update_ytdlp, get_clipboard_text,
)
from downloader import (
    create_downloader, ProgressCallback, InstagramDownloader, DownloadResult,
)
from widgets import (
    QueueItem, QueueItemWidget, VideoPreviewFrame, DownloadHistoryItem, StatsPanel,
)
from dialogs import InstagramLoginDialog, SettingsDialog, BatchImportDialog


class VideoDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"🎬 {APP_NAME}")
        self.geometry("680x900")
        self.minsize(620, 750)

        # Threading lock for shared state
        self._lock = threading.Lock()

        # Load settings first (sets download_path, theme, language, etc.)
        self.settings_file = Path.home() / ".video_downloader_settings.json"
        self.settings = {}
        self.download_path = get_download_folder()
        self.load_settings()

        # Apply saved theme and language
        ctk.set_appearance_mode(self.settings.get("theme", "dark"))
        ctk.set_default_color_theme("blue")
        set_language(self.settings.get("language", "tr"))

        # State variables
        self.format_var = ctk.StringVar(value="video")
        self.quality_var = ctk.StringVar(value=t("quality_best"))
        self.subtitles_var = ctk.BooleanVar(value=False)
        self.instagram_content_var = ctk.StringVar(value=t("ig_auto"))
        self.instagram_media_var = ctk.StringVar(value=t("ig_media_auto"))
        self.is_downloading = False
        self.instagram_downloader: Optional[InstagramDownloader] = None
        self.instagram_username: Optional[str] = None
        self.download_history = []
        self.download_queue: List[QueueItem] = []
        self.current_video_info = None
        self.filename_template = self.settings.get("filename_template", "%(title)s")

        self.ffmpeg_available = check_ffmpeg()
        self.url_debouncer = Debouncer(delay_ms=400)

        self.load_history()
        self.setup_ui()
        self.center_window()

        # Check for yt-dlp updates in background
        if self.settings.get("auto_update_check", True):
            threading.Thread(target=self._check_updates_bg, daemon=True).start()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (340)
        y = (self.winfo_screenheight() // 2) - (450)
        self.geometry(f"680x900+{x}+{y}")

    # ─────────────── UI SETUP ───────────────

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
        self.create_stats_section()
        self.create_queue_section()
        self.create_history_section()
        self.create_footer()

        self.subtitle_checkbox.configure(state="disabled")
        self.instagram_section.pack_forget()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        self.header_title = ctk.CTkLabel(
            header_frame,
            text=t("app_title"),
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        self.header_title.pack()

        version_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        version_row.pack()

        self.header_subtitle = ctk.CTkLabel(
            version_row,
            text=t("app_subtitle"),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["muted_text"],
        )
        self.header_subtitle.pack(side="left")

        ctk.CTkLabel(
            version_row,
            text=f" • v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        ).pack(side="left")

        # yt-dlp update badge (hidden by default)
        self.update_badge = ctk.CTkButton(
            header_frame,
            text=t("update_btn"),
            width=100,
            height=28,
            corner_radius=14,
            fg_color=COLORS["warning"],
            hover_color=("#D97706", "#B45309"),
            font=ctk.CTkFont(size=11),
            command=self._do_ytdlp_update,
        )
        # Will be shown by _check_updates_bg if update available

    def create_url_input(self):
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(
            input_frame,
            text=t("url_label"),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        entry_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        self.url_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text=t("url_placeholder"),
            height=48,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Paste from clipboard button
        ctk.CTkButton(
            entry_frame,
            text=t("btn_paste"),
            width=42,
            height=48,
            corner_radius=10,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            command=self._paste_from_clipboard,
        ).pack(side="left", padx=(0, 4))

        self.fetch_btn = ctk.CTkButton(
            entry_frame,
            text="🔍",
            width=50,
            height=48,
            corner_radius=10,
            command=self.fetch_video_info,
        )
        self.fetch_btn.pack(side="right")

        self.platform_label = ctk.CTkLabel(
            input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )
        self.platform_label.pack(anchor="w", pady=(5, 0))

        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        self.url_entry.bind("<Return>", lambda e: self.fetch_video_info())

    def create_video_preview(self):
        self.preview_frame = VideoPreviewFrame(self.main_frame)
        self.preview_frame.pack(fill="x", pady=10)

    def create_options_panel(self):
        options_frame = ctk.CTkFrame(
            self.main_frame, fg_color=COLORS["card_bg"], corner_radius=12
        )
        options_frame.pack(fill="x", pady=10, ipady=8)

        row1 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(10, 5))

        # Format selection
        format_frame = ctk.CTkFrame(row1, fg_color="transparent")
        format_frame.pack(side="left", expand=True)

        ctk.CTkLabel(
            format_frame,
            text=t("format_label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")
        format_buttons = ctk.CTkFrame(format_frame, fg_color="transparent")
        format_buttons.pack(anchor="w", pady=(5, 0))

        ctk.CTkRadioButton(
            format_buttons,
            text=t("format_video"),
            variable=self.format_var,
            value="video",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 15))
        ctk.CTkRadioButton(
            format_buttons,
            text=t("format_audio"),
            variable=self.format_var,
            value="audio",
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        # Quality selection
        quality_frame = ctk.CTkFrame(row1, fg_color="transparent")
        quality_frame.pack(side="right", expand=True)

        ctk.CTkLabel(
            quality_frame,
            text=t("quality_label"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=[t("quality_best"), "1080p", "720p", "480p", "360p"],
            variable=self.quality_var,
            width=120,
            height=32,
        )
        self.quality_menu.pack(anchor="w", pady=(5, 0))

        # Subtitle checkbox
        row2 = ctk.CTkFrame(options_frame, fg_color="transparent")
        row2.pack(fill="x", padx=15, pady=(4, 10))
        self.subtitle_checkbox = ctk.CTkCheckBox(
            row2,
            text=t("subtitle_label"),
            variable=self.subtitles_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(size=11),
        )
        self.subtitle_checkbox.pack(anchor="w")

        # Instagram options (initially hidden)
        self.instagram_section = ctk.CTkFrame(
            options_frame, fg_color=COLORS["card_bg_alt"], corner_radius=10
        )
        self.instagram_section.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            self.instagram_section,
            text=t("ig_section_title"),
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ig_row = ctk.CTkFrame(self.instagram_section, fg_color="transparent")
        ig_row.pack(fill="x", padx=10, pady=(0, 8))

        ig_type_frame = ctk.CTkFrame(ig_row, fg_color="transparent")
        ig_type_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(ig_type_frame, text=t("ig_type_label"), font=ctk.CTkFont(size=10)).pack(anchor="w")
        self.instagram_content_menu = ctk.CTkOptionMenu(
            ig_type_frame,
            values=[t("ig_auto"), t("ig_post"), t("ig_reel"), t("ig_story")],
            variable=self.instagram_content_var,
            width=120,
            height=30,
        )
        self.instagram_content_menu.pack(anchor="w", pady=(3, 0))

        ig_media_frame = ctk.CTkFrame(ig_row, fg_color="transparent")
        ig_media_frame.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(ig_media_frame, text=t("ig_media_label"), font=ctk.CTkFont(size=10)).pack(anchor="w")
        self.instagram_media_menu = ctk.CTkOptionMenu(
            ig_media_frame,
            values=[t("ig_media_auto"), t("ig_media_video"), t("ig_media_image")],
            variable=self.instagram_media_var,
            width=120,
            height=30,
        )
        self.instagram_media_menu.pack(anchor="w", pady=(3, 0))

    def create_download_button(self):
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        self.download_btn = ctk.CTkButton(
            btn_frame,
            text=t("btn_download"),
            height=52,
            corner_radius=12,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.start_download,
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.add_queue_btn = ctk.CTkButton(
            btn_frame,
            text=t("btn_add_queue"),
            height=52,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            width=130,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["button_text"],
            command=self.add_to_queue,
        )
        self.add_queue_btn.pack(side="right")

    def create_progress_section(self):
        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=8)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=10,
            corner_radius=5,
            progress_color=COLORS["primary"],
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text=t("status_ready"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )
        self.status_label.pack(pady=(6, 0))

    def create_stats_section(self):
        self.stats_panel = StatsPanel(self.main_frame)
        self.stats_panel.pack(fill="x", pady=(5, 10))
        self.stats_panel.update_stats(self.download_history)

    def create_queue_section(self):
        queue_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        queue_frame.pack(fill="x", pady=(10, 5))

        header = ctk.CTkFrame(queue_frame, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=t("queue_title"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        self.queue_count_label = ctk.CTkLabel(
            header,
            text="(0)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted_text"],
        )
        self.queue_count_label.pack(side="left", padx=5)

        # Batch import button
        ctk.CTkButton(
            header,
            text=t("btn_batch_import"),
            width=130,
            height=28,
            corner_radius=6,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["button_text"],
            font=ctk.CTkFont(size=11),
            command=self.show_batch_import,
        ).pack(side="right", padx=(5, 0))

        self.start_queue_btn = ctk.CTkButton(
            header,
            text=t("btn_start_queue"),
            width=80,
            height=28,
            corner_radius=6,
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            command=self.start_queue,
        )
        self.start_queue_btn.pack(side="right")

        self.queue_scroll = ctk.CTkScrollableFrame(
            queue_frame, fg_color="transparent", height=100
        )
        self.queue_scroll.pack(fill="x", pady=(8, 0))

        self.queue_empty_label = ctk.CTkLabel(
            self.queue_scroll,
            text=t("queue_empty"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )
        self.queue_empty_label.pack(pady=15)

    def create_history_section(self):
        history_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        history_frame.pack(fill="both", expand=True, pady=(10, 5))

        header = ctk.CTkFrame(history_frame, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text=t("history_title"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="🗑️",
            width=35,
            height=28,
            corner_radius=6,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            command=self.clear_history,
        ).pack(side="right")

        # Search bar for history
        self.history_search_var = ctk.StringVar()
        self.history_search_var.trace_add("write", lambda *_: self.display_history())
        self.history_search_entry = ctk.CTkEntry(
            history_frame,
            placeholder_text=t("history_search_placeholder"),
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            textvariable=self.history_search_var,
        )
        self.history_search_entry.pack(fill="x", pady=(6, 0))

        self.history_scroll = ctk.CTkScrollableFrame(
            history_frame, fg_color="transparent", height=150
        )
        self.history_scroll.pack(fill="both", expand=True, pady=(8, 0))

        self.display_history()

    def create_footer(self):
        self.instagram_btn = ctk.CTkButton(
            self.footer_frame,
            text="📸 Instagram",
            width=120,
            height=35,
            corner_radius=8,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["button_text"],
            font=ctk.CTkFont(size=12),
            command=self.show_instagram_login,
        )
        self.instagram_btn.pack(side="left")

        ctk.CTkButton(
            self.footer_frame,
            text="⚙️",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            command=self.show_settings,
        ).pack(side="left", padx=8)

        self.folder_btn = ctk.CTkButton(
            self.footer_frame,
            text=f"📁 {self.download_path.name}",
            width=150,
            height=35,
            corner_radius=8,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["button_text"],
            font=ctk.CTkFont(size=12),
            command=self.change_download_folder,
        )
        self.folder_btn.pack(side="right")

        self.theme_switch = ctk.CTkSwitch(
            self.footer_frame,
            text="🌙",
            width=40,
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light",
        )
        self.theme_switch.pack(side="right", padx=10)
        if self.settings.get("theme", "dark") == "dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

    # ─────────────── EVENT HANDLERS ───────────────

    def on_url_change(self, event=None):
        """Debounced URL change handler."""
        self.url_debouncer(self._process_url_change)

    def _process_url_change(self):
        """Actual URL processing (runs on debounce timer)."""
        url = self.url_entry.get().strip()
        self.after(0, lambda: self._update_platform_display(url))

    def _update_platform_display(self, url: str):
        if url:
            platform = detect_platform(url)
            if platform:
                icon = get_platform_icon(platform)
                self.platform_label.configure(
                    text=t("platform_detected", icon=icon, platform=platform.capitalize()),
                    text_color=get_platform_color(platform),
                )
                subtitle_state = "normal" if platform == "youtube" else "disabled"
                self.subtitle_checkbox.configure(state=subtitle_state)
                if platform != "youtube":
                    self.subtitles_var.set(False)

                if platform == "instagram":
                    self.instagram_section.pack(fill="x", padx=15, pady=(0, 10))
                    self.format_var.set("video")
                else:
                    self.instagram_section.pack_forget()
            else:
                self.platform_label.configure(
                    text=t("url_unsupported"), text_color=COLORS["error_text"]
                )
                self.subtitle_checkbox.configure(state="disabled")
                self.subtitles_var.set(False)
                self.instagram_section.pack_forget()
        else:
            self.platform_label.configure(text="")
            self.preview_frame.show_empty()
            self.subtitle_checkbox.configure(state="disabled")
            self.subtitles_var.set(False)
            self.instagram_section.pack_forget()

    def _paste_from_clipboard(self):
        """Paste URL from system clipboard."""
        text = get_clipboard_text()
        if text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text)
            self._process_url_change()

    def fetch_video_info(self):
        url = normalize_media_url(self.url_entry.get())
        if not url:
            return

        platform = detect_platform(url)
        if not platform:
            messagebox.showerror(t("error_title"), t("error_unsupported_url"))
            return

        self.preview_frame.show_loading()
        self.fetch_btn.configure(state="disabled")

        def fetch_thread():
            try:
                downloader = create_downloader(platform, self.download_path)
                info = downloader.get_info(url)
                self.after(0, lambda: self.handle_video_info(info, platform))
            except Exception as e:
                self.after(0, lambda: self.handle_video_info({"error": str(e)}, platform))

        threading.Thread(target=fetch_thread, daemon=True).start()

    def handle_video_info(self, info: dict, platform: str):
        self.fetch_btn.configure(state="normal")

        if "error" in info:
            self.preview_frame.show_empty()
            messagebox.showerror(
                t("error_title"), t("error_video_info_failed", error=info["error"])
            )
            return

        self.current_video_info = info
        self.current_video_info["platform"] = platform
        self.preview_frame.show_preview(info)

        qualities = info.get("qualities", ["best"])
        quality_labels = []
        for q in qualities:
            quality_labels.append(t("quality_best") if q == "best" else f"{q}p")

        if quality_labels:
            self.quality_menu.configure(values=quality_labels)
            self.quality_var.set(quality_labels[0])

        if platform == "instagram":
            content_type = info.get("content_type", "post")
            self.instagram_content_var.set(t(f"ig_{content_type}"))

            raw_media_modes = info.get("media_modes", ["auto", "video", "image"])
            menu_labels = []
            for mode in raw_media_modes:
                label = t(f"ig_media_{mode}")
                if label not in menu_labels:
                    menu_labels.append(label)
            if t("ig_media_auto") not in menu_labels:
                menu_labels.insert(0, t("ig_media_auto"))
            self.instagram_media_menu.configure(values=menu_labels)
            self.instagram_media_var.set(menu_labels[0])

    # ─────────────── DOWNLOAD HELPERS ───────────────

    def get_selected_quality(self) -> str:
        quality = self.quality_var.get()
        if quality == t("quality_best"):
            return "best"
        return quality.replace("p", "")

    def get_instagram_content_type(self) -> str:
        val = self.instagram_content_var.get()
        reverse = {t("ig_auto"): "auto", t("ig_post"): "post", t("ig_reel"): "reel", t("ig_story"): "story"}
        return reverse.get(val, "auto")

    def get_instagram_media_mode(self) -> str:
        val = self.instagram_media_var.get()
        reverse = {t("ig_media_auto"): "auto", t("ig_media_video"): "video", t("ig_media_image"): "image"}
        return reverse.get(val, "auto")

    def _get_effective_download_path(self, platform: str) -> Path:
        """Get the actual download path, respecting auto-folder setting."""
        auto_folder = self.settings.get("auto_folder", False)
        return get_platform_download_path(self.download_path, platform, auto_folder)

    def _do_download(self, url: str, platform: str, as_audio: bool, quality: str,
                     download_subtitles: bool, instagram_content_type: str,
                     instagram_media_mode: str, progress_callback: ProgressCallback) -> DownloadResult:
        """Unified download logic used by both single and queue downloads."""
        effective_path = self._get_effective_download_path(platform)

        if platform == "instagram" and self.instagram_downloader:
            downloader = self.instagram_downloader
        else:
            downloader = create_downloader(platform, effective_path)

        return downloader.download(
            url, as_audio, quality, progress_callback,
            self.filename_template, download_subtitles,
            instagram_content_type, instagram_media_mode,
        )

    # ─────────────── QUEUE ───────────────

    def add_to_queue(self):
        url = normalize_media_url(self.url_entry.get())
        if not url:
            messagebox.showwarning(t("warning"), t("error_no_url"))
            return

        platform = detect_platform(url)
        if not platform:
            messagebox.showerror(t("error_title"), t("error_unsupported_url"))
            return

        title = ""
        if self.current_video_info:
            title = self.current_video_info.get("title", "")

        quality = self.get_selected_quality()
        as_audio = self.format_var.get() == "audio"
        subtitles = bool(self.subtitles_var.get()) and platform == "youtube" and not as_audio
        ig_content = self.get_instagram_content_type() if platform == "instagram" else "auto"
        ig_media = self.get_instagram_media_mode() if platform == "instagram" else "auto"

        new_item = QueueItem(
            url=url, platform=platform, quality=quality, as_audio=as_audio,
            title=title or url[:40], download_subtitles=subtitles,
            instagram_content_type=ig_content, instagram_media_mode=ig_media,
        )

        # Duplicate check using QueueItem.matches()
        with self._lock:
            for queued in self.download_queue:
                if queued.status in {"pending", "downloading"} and queued.matches(new_item):
                    messagebox.showinfo(t("info"), t("queue_already_exists"))
                    return
            self.download_queue.append(new_item)

        self.update_queue_display()
        self.url_entry.delete(0, "end")
        self.platform_label.configure(text="")
        self.preview_frame.show_empty()
        self.current_video_info = None

    def remove_from_queue(self, item: QueueItem):
        with self._lock:
            if item in self.download_queue:
                self.download_queue.remove(item)
        self.update_queue_display()

    def update_queue_display(self):
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()

        with self._lock:
            queue_len = len(self.download_queue)
            queue_copy = list(self.download_queue)

        self.queue_count_label.configure(text=f"({queue_len})")

        if not queue_copy:
            self.queue_empty_label = ctk.CTkLabel(
                self.queue_scroll,
                text=t("queue_empty"),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["muted_text"],
            )
            self.queue_empty_label.pack(pady=15)
            return

        for item in queue_copy:
            widget = QueueItemWidget(self.queue_scroll, item, self.remove_from_queue)
            widget.pack(fill="x", pady=2)

    def start_queue(self):
        if not self.download_queue:
            messagebox.showinfo(t("info"), t("queue_empty"))
            return

        with self._lock:
            if self.is_downloading:
                return

        self.process_next_queue_item()

    def process_next_queue_item(self):
        with self._lock:
            pending_items = [item for item in self.download_queue if item.status == "pending"]

        if not pending_items:
            with self._lock:
                self.is_downloading = False
            self.download_btn.configure(state="normal", text=t("btn_download"))
            self.progress_bar.set(0)
            self.status_label.configure(text=t("status_ready"))

            if self.settings.get("notifications", True):
                flash_taskbar_icon(self)

            messagebox.showinfo(t("info"), t("queue_complete"))
            return

        item = pending_items[0]
        item.status = "downloading"
        self.update_queue_display()

        with self._lock:
            self.is_downloading = True
        self.download_btn.configure(state="disabled", text=t("btn_queue_processing"))

        thread = threading.Thread(target=self.download_queue_item, args=(item,), daemon=True)
        thread.start()

    def download_queue_item(self, item: QueueItem):
        try:
            def progress_update(percent, status, speed):
                self.after(0, lambda: self.update_progress(percent, status, speed))

            callback = ProgressCallback(progress_update)
            result = self._do_download(
                item.url, item.platform, item.as_audio, item.quality,
                item.download_subtitles, item.instagram_content_type,
                item.instagram_media_mode, callback,
            )

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

    # ─────────────── SINGLE DOWNLOAD ───────────────

    def start_download(self):
        url = normalize_media_url(self.url_entry.get())

        if not url:
            messagebox.showwarning(t("warning"), t("error_no_url"))
            return

        platform = detect_platform(url)
        if not platform:
            messagebox.showerror(t("error_title"), t("error_unsupported_url"))
            return

        with self._lock:
            if self.is_downloading:
                return

        as_audio = self.format_var.get() == "audio"
        if as_audio and not self.ffmpeg_available:
            messagebox.showwarning(t("error_ffmpeg_title"), t("error_ffmpeg_required"))
            return

        with self._lock:
            self.is_downloading = True
        self.download_btn.configure(state="disabled", text=t("btn_downloading"))
        self.progress_bar.set(0)
        self.status_label.configure(text=t("status_starting"))

        quality = self.get_selected_quality()
        subtitles = bool(self.subtitles_var.get()) and platform == "youtube" and not as_audio
        ig_content = self.get_instagram_content_type() if platform == "instagram" else "auto"
        ig_media = self.get_instagram_media_mode() if platform == "instagram" else "auto"

        thread = threading.Thread(
            target=self.download_thread,
            args=(url, platform, as_audio, quality, subtitles, ig_content, ig_media),
            daemon=True,
        )
        thread.start()

    def download_thread(self, url, platform, as_audio, quality, subtitles, ig_content, ig_media):
        try:
            def progress_update(percent, status, speed):
                self.after(0, lambda: self.update_progress(percent, status, speed))

            callback = ProgressCallback(progress_update)
            result = self._do_download(url, platform, as_audio, quality, subtitles, ig_content, ig_media, callback)
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
        with self._lock:
            self.is_downloading = False
        self.download_btn.configure(state="normal", text=t("btn_download"))

        if result.success:
            self.progress_bar.set(1)
            self.status_label.configure(text=t("status_completed"))
            self.add_to_history(result)
            self.url_entry.delete(0, "end")
            self.platform_label.configure(text="")
            self.preview_frame.show_empty()
            self.current_video_info = None

            if self.settings.get("notifications", True):
                flash_taskbar_icon(self)
        else:
            self.progress_bar.set(0)
            self.status_label.configure(text=t("status_error", error=result.error[:50]))
            messagebox.showerror(t("error_download"), result.error)

    def handle_download_error(self, error: str):
        with self._lock:
            self.is_downloading = False
        self.download_btn.configure(state="normal", text=t("btn_download"))
        self.progress_bar.set(0)
        self.status_label.configure(text=t("status_error_short"))
        messagebox.showerror(t("error_download"), error)

    # ─────────────── HISTORY ───────────────

    def add_to_history(self, result: DownloadResult):
        item = {
            "filename": result.filename,
            "platform": result.platform,
            "size": format_size(result.filesize),
            "filepath": result.filepath,
            "date": datetime.now().isoformat(),
            "source_url": getattr(result, "source_url", ""),
        }
        self.download_history.insert(0, item)
        self.download_history = self.download_history[:MAX_HISTORY_ITEMS]
        self.save_history()
        self.display_history()
        self.stats_panel.update_stats(self.download_history)

    def display_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        if not self.download_history:
            ctk.CTkLabel(
                self.history_scroll,
                text=t("history_empty"),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["muted_text"],
            ).pack(pady=20)
            return

        search_term = self.history_search_var.get().lower() if hasattr(self, "history_search_var") else ""

        shown = 0
        for item in self.download_history:
            if shown >= MAX_HISTORY_DISPLAY:
                break

            # Filter by search
            if search_term:
                name = item.get("filename", "").lower()
                platform = item.get("platform", "").lower()
                if search_term not in name and search_term not in platform:
                    continue

            history_widget = DownloadHistoryItem(
                self.history_scroll,
                filename=item["filename"],
                platform=item["platform"],
                size=item["size"],
                filepath=item["filepath"],
            )
            history_widget.pack(fill="x", pady=2)
            shown += 1

    def clear_history(self):
        if messagebox.askyesno(t("confirm"), t("history_clear_confirm")):
            self.download_history = []
            self.save_history()
            self.display_history()
            self.stats_panel.update_stats(self.download_history)

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

    # ─────────────── DIALOGS ───────────────

    def show_instagram_login(self):
        if self.instagram_username:
            if messagebox.askyesno(
                t("ig_logout_title"),
                t("ig_logout_confirm", username=self.instagram_username),
            ):
                if self.instagram_downloader:
                    self.instagram_downloader.logout()
                self.instagram_downloader = None
                self.instagram_username = None
                self.instagram_btn.configure(text="📸 Instagram")
                messagebox.showinfo(t("info"), t("ig_logout_success"))
        else:
            InstagramLoginDialog(self, self.on_instagram_login)

    def on_instagram_login(self, username: str, downloader: InstagramDownloader):
        self.instagram_username = username
        self.instagram_downloader = downloader
        self.instagram_btn.configure(text=f"📸 @{username[:10]}")

    def show_settings(self):
        SettingsDialog(self, self.settings, self.on_settings_save)

    def on_settings_save(self, new_settings: dict):
        old_lang = self.settings.get("language", "tr")
        old_theme = self.settings.get("theme", "dark")

        self.settings = new_settings
        self.filename_template = new_settings.get("filename_template", "%(title)s")

        # Apply language change
        new_lang = new_settings.get("language", "tr")
        if new_lang != old_lang:
            set_language(new_lang)
            self._refresh_all_texts()

        # Apply theme change
        new_theme = new_settings.get("theme", "dark")
        if new_theme != old_theme:
            ctk.set_appearance_mode(new_theme)
            if new_theme == "dark":
                self.theme_switch.select()
            else:
                self.theme_switch.deselect()

        self.save_settings()

    def show_batch_import(self):
        BatchImportDialog(self, self.on_batch_import)

    def on_batch_import(self, urls: list[str]):
        """Handle batch import of URLs — add all to queue."""
        for url in urls:
            platform = detect_platform(url)
            if not platform:
                continue

            item = QueueItem(url=url, platform=platform, title=url[:40])

            with self._lock:
                duplicate = False
                for queued in self.download_queue:
                    if queued.status in {"pending", "downloading"} and queued.matches(item):
                        duplicate = True
                        break
                if not duplicate:
                    self.download_queue.append(item)

        self.update_queue_display()

    # ─────────────── FOLDER & THEME ───────────────

    def change_download_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = Path(folder)
            self.folder_btn.configure(text=f"📁 {self.download_path.name}")

            # Sync Instagram downloader path
            if self.instagram_downloader:
                self.instagram_downloader.download_path = self.download_path
                self.instagram_downloader.download_path.mkdir(parents=True, exist_ok=True)

            self.save_settings()
            messagebox.showinfo(t("success"), t("folder_changed", folder=folder))

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.settings["theme"] = new_mode
        self.save_settings()

    # ─────────────── SETTINGS PERSISTENCE ───────────────

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
                self.settings = dict(DEFAULT_SETTINGS)
                self.download_path = get_download_folder()
        except Exception:
            self.settings = dict(DEFAULT_SETTINGS)
            self.download_path = get_download_folder()

    # ─────────────── LANGUAGE REFRESH ───────────────

    def _refresh_all_texts(self):
        """Refresh all translatable UI strings after language change."""
        self.title(f"🎬 {APP_NAME}")
        self.header_title.configure(text=t("app_title"))
        self.header_subtitle.configure(text=t("app_subtitle"))
        self.download_btn.configure(text=t("btn_download"))
        self.add_queue_btn.configure(text=t("btn_add_queue"))
        self.status_label.configure(text=t("status_ready"))
        self.preview_frame.refresh_texts()
        self.stats_panel.refresh_texts()
        self.stats_panel.update_stats(self.download_history)
        self.update_queue_display()
        self.display_history()

    # ─────────────── YT-DLP UPDATE ───────────────

    def _check_updates_bg(self):
        """Background thread: check for yt-dlp updates."""
        new_version = check_ytdlp_update()
        if new_version:
            self.after(0, lambda: self.update_badge.pack(pady=(5, 0)))

    def _do_ytdlp_update(self):
        """Trigger yt-dlp update."""
        if messagebox.askyesno(t("update_title"), t("update_available")):
            success = update_ytdlp()
            if success:
                self.update_badge.pack_forget()
                messagebox.showinfo(t("info"), t("update_success"))
            else:
                messagebox.showerror(t("error_title"), "Update failed.")


def main():
    app = VideoDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
