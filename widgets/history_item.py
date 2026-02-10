"""Download history item widget."""

import os
import sys
import subprocess
import customtkinter as ctk
from utils import get_platform_icon
from constants import COLORS


class DownloadHistoryItem(ctk.CTkFrame):
    """Single entry in the download history list."""

    def __init__(self, master, filename: str, platform: str, size: str, filepath: str, **kwargs):
        super().__init__(master, **kwargs)
        self.filepath = filepath
        self.configure(fg_color=COLORS["card_bg"], corner_radius=8)

        ctk.CTkLabel(
            self,
            text=get_platform_icon(platform),
            font=ctk.CTkFont(size=20),
            width=30,
        ).pack(side="left", padx=(10, 5))

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=5)

        display_name = filename[:40] + "..." if len(filename) > 43 else filename
        ctk.CTkLabel(
            info_frame,
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info_frame,
            text=f"{platform.capitalize()} • {size}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkButton(
            self,
            text="📂",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=("gray80", "gray25"),
            hover_color=("gray70", "gray35"),
            command=self.open_folder,
        ).pack(side="right", padx=10, pady=8)

    def open_folder(self):
        """Open the containing folder — cross-platform safe."""
        if not self.filepath or not os.path.exists(self.filepath):
            return
        folder = os.path.dirname(self.filepath)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
