"""Video preview frame widget."""

import customtkinter as ctk
from i18n import t
from utils import format_size
from constants import COLORS


class VideoPreviewFrame(ctk.CTkFrame):
    """Displays video metadata after URL analysis."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=COLORS["card_bg"], corner_radius=12)
        self.video_info = None

        self.title_label = ctk.CTkLabel(
            self,
            text=t("preview_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.title_label.pack(fill="x", padx=15, pady=(12, 5))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=15, pady=(0, 12))

        self.empty_label = ctk.CTkLabel(
            self.content_frame,
            text=t("preview_empty"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )
        self.empty_label.pack(pady=10)

        self.preview_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        self.info_container = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        self.info_container.pack(fill="both", expand=True)

        self.video_title_label = ctk.CTkLabel(
            self.info_container,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            wraplength=400,
        )
        self.video_title_label.pack(fill="x")

        self.uploader_label = ctk.CTkLabel(
            self.info_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
            anchor="w",
        )
        self.uploader_label.pack(fill="x")

        self.duration_label = ctk.CTkLabel(
            self.info_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
            anchor="w",
        )
        self.duration_label.pack(fill="x")

        self.size_label = ctk.CTkLabel(
            self.info_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
            anchor="w",
        )
        self.size_label.pack(fill="x")

        self.loading_label = ctk.CTkLabel(
            self.content_frame,
            text=t("status_loading_info"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )

    def show_loading(self):
        self.empty_label.pack_forget()
        self.preview_container.pack_forget()
        self.loading_label.pack(pady=10)

    def show_empty(self):
        self.loading_label.pack_forget()
        self.preview_container.pack_forget()
        self.duration_label.configure(text="")
        self.size_label.configure(text="")
        self.empty_label.pack(pady=10)

    def show_preview(self, info: dict):
        self.video_info = info
        self.empty_label.pack_forget()
        self.loading_label.pack_forget()

        title = info.get("title", "Bilinmiyor")
        if len(title) > 60:
            title = title[:57] + "..."
        self.video_title_label.configure(text=title)

        uploader = info.get("uploader", "")
        self.uploader_label.configure(text=f"📺 {uploader}" if uploader else "")

        duration = info.get("duration", 0)
        if duration:
            mins, secs = divmod(duration, 60)
            hours, mins = divmod(mins, 60)
            duration_str = (
                f"⏱️ {hours}:{mins:02d}:{secs:02d}"
                if hours
                else f"⏱️ {mins}:{secs:02d}"
            )
            self.duration_label.configure(text=duration_str)
        else:
            self.duration_label.configure(text="")

        file_size = info.get("filesize", 0)
        self.size_label.configure(
            text=f"💾 {format_size(file_size)}" if file_size else ""
        )

        self.preview_container.pack(fill="x", pady=5)

    def get_qualities(self) -> list:
        if self.video_info:
            return self.video_info.get("qualities", ["best"])
        return ["best"]

    def refresh_texts(self):
        """Refresh all translatable text (called on language change)."""
        self.title_label.configure(text=t("preview_title"))
        if not self.video_info:
            self.empty_label.configure(text=t("preview_empty"))
        self.loading_label.configure(text=t("status_loading_info"))
