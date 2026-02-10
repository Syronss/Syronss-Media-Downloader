"""Queue item data model and widget."""

import customtkinter as ctk
from i18n import t
from utils import get_platform_icon
from constants import COLORS


class QueueItem:
    """Data model for a download queue entry."""

    def __init__(
        self,
        url: str,
        platform: str,
        quality: str = "best",
        as_audio: bool = False,
        title: str = "",
        download_subtitles: bool = False,
        instagram_content_type: str = "auto",
        instagram_media_mode: str = "auto",
    ):
        self.url = url
        self.platform = platform
        self.quality = quality
        self.as_audio = as_audio
        self.title = title or url[:50]
        self.download_subtitles = download_subtitles
        self.instagram_content_type = instagram_content_type
        self.instagram_media_mode = instagram_media_mode
        self.status = "pending"
        self.progress = 0
        self.error = ""

    def matches(self, other: "QueueItem") -> bool:
        """Check if another queue item is a duplicate of this one."""
        return (
            self.url == other.url
            and self.as_audio == other.as_audio
            and self.quality == other.quality
            and self.download_subtitles == other.download_subtitles
            and self.instagram_content_type == other.instagram_content_type
            and self.instagram_media_mode == other.instagram_media_mode
        )


class QueueItemWidget(ctk.CTkFrame):
    """Visual representation of a queue item."""

    def __init__(self, master, item: QueueItem, on_remove: callable, **kwargs):
        super().__init__(master, **kwargs)
        self.item = item
        self.on_remove = on_remove
        self.configure(fg_color=COLORS["card_bg"], corner_radius=8)

        icon = get_platform_icon(item.platform)
        ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=18), width=30).pack(
            side="left", padx=(8, 5)
        )

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)

        title = item.title[:35] + "..." if len(item.title) > 38 else item.title
        ctk.CTkLabel(
            info_frame,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        quality_text = self._build_quality_text(item)
        ctk.CTkLabel(
            info_frame,
            text=quality_text,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
            anchor="w",
        ).pack(fill="x")

        self._add_status_indicator(item)

    def _build_quality_text(self, item: QueueItem) -> str:
        if item.as_audio:
            text = "MP3"
        elif item.quality != "best":
            text = f"{item.quality}p"
        else:
            text = t("quality_best")

        if item.download_subtitles and not item.as_audio:
            text += " • SUB"
        if item.platform == "instagram":
            text += f" • {t(f'ig_{item.instagram_content_type}')}"
            if item.instagram_media_mode != "auto":
                text += f"/{t(f'ig_media_{item.instagram_media_mode}')}"
        return text

    def _add_status_indicator(self, item: QueueItem):
        status_map = {
            "pending": ("✕", True),
            "downloading": ("⏳", False),
            "completed": ("✅", False),
            "error": ("❌", False),
        }
        symbol, is_button = status_map.get(item.status, ("?", False))

        if is_button:
            ctk.CTkButton(
                self,
                text=symbol,
                width=30,
                height=30,
                corner_radius=6,
                fg_color=("gray80", "gray25"),
                hover_color=COLORS["danger"],
                command=lambda: self.on_remove(item),
            ).pack(side="right", padx=8, pady=6)
        else:
            ctk.CTkLabel(self, text=symbol, font=ctk.CTkFont(size=16)).pack(
                side="right", padx=12
            )
