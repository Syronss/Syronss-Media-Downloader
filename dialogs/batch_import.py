"""Batch URL import dialog."""

import customtkinter as ctk
from tkinter import filedialog
from i18n import t
from utils import extract_urls_from_text
from constants import COLORS


class BatchImportDialog(ctk.CTkToplevel):
    """Dialog for importing multiple URLs at once."""

    def __init__(self, master, on_import: callable):
        super().__init__(master)
        self.on_import = on_import

        self.title(t("batch_title"))
        self.geometry("550x450")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (275)
        y = (self.winfo_screenheight() // 2) - (225)
        self.geometry(f"550x450+{x}+{y}")

    def setup_ui(self):
        # Header
        ctk.CTkLabel(
            self,
            text=t("batch_title"),
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))
        ctk.CTkLabel(
            self,
            text=t("batch_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted_text"],
        ).pack(pady=(0, 15))

        # Text area
        self.text_area = ctk.CTkTextbox(
            self,
            height=220,
            corner_radius=10,
            font=ctk.CTkFont(size=12),
        )
        self.text_area.pack(fill="x", padx=25, pady=(0, 10))
        self.text_area.bind("<KeyRelease>", self._on_text_change)

        # URL count label
        self.url_count_label = ctk.CTkLabel(
            self,
            text=t("batch_url_count", count=0),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        )
        self.url_count_label.pack(pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text=t("batch_load_file"),
            width=160,
            height=40,
            corner_radius=10,
            fg_color=COLORS["button_bg"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["button_text"],
            command=self.load_from_file,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text=t("batch_add_all"),
            width=160,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.add_all,
        ).pack(side="right")

    def _on_text_change(self, event=None):
        text = self.text_area.get("1.0", "end")
        urls = extract_urls_from_text(text)
        self.url_count_label.configure(text=t("batch_url_count", count=len(urls)))

    def load_from_file(self):
        filepath = filedialog.askopenfilename(
            title=t("batch_load_file"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", "end")
                self.text_area.insert("1.0", content)
                self._on_text_change()
            except Exception:
                pass

    def add_all(self):
        text = self.text_area.get("1.0", "end")
        urls = extract_urls_from_text(text)
        if urls:
            self.on_import(urls)
            self.destroy()
