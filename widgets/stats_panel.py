"""Download statistics panel widget."""

import customtkinter as ctk
from i18n import t
from utils import format_size, get_platform_icon
from constants import COLORS


class StatsPanel(ctk.CTkFrame):
    """Compact statistics panel showing download totals and platform breakdown."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=COLORS["card_bg"], corner_radius=12)

        self.header = ctk.CTkLabel(
            self,
            text=t("stats_title"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.header.pack(fill="x", padx=15, pady=(10, 5))

        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Total downloads
        self.total_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.total_frame.pack(side="left", expand=True)

        self.total_count_label = ctk.CTkLabel(
            self.total_frame,
            text="0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["primary"],
        )
        self.total_count_label.pack()
        self.total_desc_label = ctk.CTkLabel(
            self.total_frame,
            text=t("stats_total_downloads"),
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
        )
        self.total_desc_label.pack()

        # Total size
        self.size_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.size_frame.pack(side="left", expand=True)

        self.total_size_label = ctk.CTkLabel(
            self.size_frame,
            text="0 B",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["success"],
        )
        self.total_size_label.pack()
        self.size_desc_label = ctk.CTkLabel(
            self.size_frame,
            text=t("stats_total_size"),
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
        )
        self.size_desc_label.pack()

        # Platform breakdown
        self.platform_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.platform_frame.pack(side="left", expand=True)

        self.platform_label = ctk.CTkLabel(
            self.platform_frame,
            text="—",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.platform_label.pack()
        self.platform_desc_label = ctk.CTkLabel(
            self.platform_frame,
            text=t("stats_platforms"),
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
        )
        self.platform_desc_label.pack()

    def update_stats(self, history: list) -> None:
        """Update statistics from download history list."""
        if not history:
            self.total_count_label.configure(text="0")
            self.total_size_label.configure(text="0 B")
            self.platform_label.configure(text="—")
            return

        total_count = len(history)
        total_size = 0
        platform_counts: dict[str, int] = {}

        for item in history:
            # Parse size string back to bytes (approximate)
            size_str = item.get("size", "0 B")
            total_size += self._parse_size(size_str)

            platform = item.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        self.total_count_label.configure(text=str(total_count))
        self.total_size_label.configure(text=format_size(total_size))

        # Show top 3 platforms as icons
        sorted_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        icons = " ".join(f"{get_platform_icon(p)}{c}" for p, c in sorted_platforms)
        self.platform_label.configure(text=icons if icons else "—")

    def _parse_size(self, size_str: str) -> int:
        """Parse a human-readable size string back to bytes (approximate)."""
        try:
            parts = size_str.strip().split()
            if len(parts) != 2:
                return 0
            value = float(parts[0])
            unit = parts[1].upper()
            multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
            return int(value * multipliers.get(unit, 1))
        except (ValueError, IndexError):
            return 0

    def refresh_texts(self):
        """Refresh translatable text on language change."""
        self.header.configure(text=t("stats_title"))
        self.total_desc_label.configure(text=t("stats_total_downloads"))
        self.size_desc_label.configure(text=t("stats_total_size"))
        self.platform_desc_label.configure(text=t("stats_platforms"))
