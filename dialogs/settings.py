"""Settings dialog with language, theme, filename templates, and feature toggles."""

import customtkinter as ctk
from i18n import t, get_available_languages
from constants import FILENAME_TEMPLATES, LANGUAGES, COLORS


class SettingsDialog(ctk.CTkToplevel):
    """Application settings dialog."""

    def __init__(self, master, settings: dict, on_save: callable):
        super().__init__(master)
        self.on_save = on_save
        self.settings = settings.copy()

        self.title(t("settings_title"))
        self.geometry("500x580")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.setup_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (250)
        y = (self.winfo_screenheight() // 2) - (290)
        self.geometry(f"500x580+{x}+{y}")

    def setup_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # --- Language ---
        self._add_section_header(scroll, t("settings_language"))
        self.lang_var = ctk.StringVar(value=self.settings.get("language", "tr"))
        lang_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        lang_frame.pack(fill="x", padx=20, pady=(0, 15))

        for code, name in LANGUAGES.items():
            ctk.CTkRadioButton(
                lang_frame,
                text=name,
                variable=self.lang_var,
                value=code,
                font=ctk.CTkFont(size=13),
            ).pack(side="left", padx=(0, 20))

        # --- Theme ---
        self._add_section_header(scroll, t("settings_theme"))
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "dark"))
        theme_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkRadioButton(
            theme_frame,
            text=f"🌙 {t('settings_theme_dark')}",
            variable=self.theme_var,
            value="dark",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(
            theme_frame,
            text=f"☀️ {t('settings_theme_light')}",
            variable=self.theme_var,
            value="light",
            font=ctk.CTkFont(size=13),
        ).pack(side="left")

        # --- Filename Template ---
        self._add_section_header(scroll, t("settings_filename_template"))
        ctk.CTkLabel(
            scroll,
            text=t("settings_filename_desc"),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted_text"],
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.template_var = ctk.StringVar(
            value=self.settings.get("filename_template", "%(title)s")
        )
        for template, desc_key in FILENAME_TEMPLATES.items():
            ctk.CTkRadioButton(
                scroll,
                text=t(desc_key),
                variable=self.template_var,
                value=template,
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=40, pady=3)

        # --- Feature Toggles ---
        self._add_section_header(scroll, "⚡ " + t("settings_title"))

        self.auto_folder_var = ctk.BooleanVar(
            value=self.settings.get("auto_folder", False)
        )
        ctk.CTkCheckBox(
            scroll,
            text=t("settings_auto_folder"),
            variable=self.auto_folder_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=30, pady=4)

        self.notifications_var = ctk.BooleanVar(
            value=self.settings.get("notifications", True)
        )
        ctk.CTkCheckBox(
            scroll,
            text=t("settings_notifications"),
            variable=self.notifications_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=30, pady=4)

        self.auto_update_var = ctk.BooleanVar(
            value=self.settings.get("auto_update_check", True)
        )
        ctk.CTkCheckBox(
            scroll,
            text=t("settings_auto_update"),
            variable=self.auto_update_var,
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=30, pady=4)

        # --- Save Button ---
        ctk.CTkButton(
            scroll,
            text=t("settings_save"),
            width=150,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.save_and_close,
        ).pack(pady=20)

    def _add_section_header(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(15, 5))

    def save_and_close(self):
        self.settings["language"] = self.lang_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["filename_template"] = self.template_var.get()
        self.settings["auto_folder"] = self.auto_folder_var.get()
        self.settings["notifications"] = self.notifications_var.get()
        self.settings["auto_update_check"] = self.auto_update_var.get()
        self.on_save(self.settings)
        self.destroy()
