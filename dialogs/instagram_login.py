"""Instagram login dialog with 2FA support."""

import threading
import customtkinter as ctk
from i18n import t
from utils import get_download_folder
from constants import COLORS
from downloader import InstagramDownloader


class InstagramLoginDialog(ctk.CTkToplevel):
    """Instagram login window with 2FA support."""

    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.title(t("ig_login_title"))
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
        main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            main_container,
            text=t("ig_login_title"),
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(10, 5))
        ctk.CTkLabel(
            main_container,
            text=t("ig_login_subtitle"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted_text"],
        ).pack(pady=(0, 15))

        form_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)

        # Username
        ctk.CTkLabel(
            form_frame, text=t("ig_username"), font=ctk.CTkFont(size=12), anchor="w"
        ).pack(fill="x")
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("ig_username_placeholder"),
            height=40,
            corner_radius=10,
        )
        self.username_entry.pack(fill="x", pady=(5, 12))

        # Password
        ctk.CTkLabel(
            form_frame, text=t("ig_password"), font=ctk.CTkFont(size=12), anchor="w"
        ).pack(fill="x")
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text=t("ig_password_placeholder"),
            show="•",
            height=40,
            corner_radius=10,
        )
        self.password_entry.pack(fill="x", pady=(5, 12))

        # 2FA (initially hidden)
        self.twofa_frame = ctk.CTkFrame(form_frame, fg_color="transparent")

        ctk.CTkLabel(
            self.twofa_frame,
            text=t("ig_2fa_title"),
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            text_color=COLORS["instagram"],
        ).pack(fill="x")
        ctk.CTkLabel(
            self.twofa_frame,
            text=t("ig_2fa_subtitle"),
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
            anchor="w",
        ).pack(fill="x")
        self.twofa_entry = ctk.CTkEntry(
            self.twofa_frame,
            placeholder_text=t("ig_2fa_placeholder"),
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=16),
            justify="center",
        )
        self.twofa_entry.pack(fill="x", pady=(8, 12))

        # Login button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text=t("ig_btn_login"),
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["instagram"],
            hover_color=COLORS["instagram_hover"],
            command=self.do_login,
        )
        self.login_btn.pack(fill="x", pady=(8, 0))

        # Status
        self.status_label = ctk.CTkLabel(
            main_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["error_text"],
            wraplength=350,
        )
        self.status_label.pack(pady=15)

        # Warning
        ctk.CTkLabel(
            main_container,
            text=t("ig_session_warning"),
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted_text"],
        ).pack(pady=(0, 10))

    def show_2fa_input(self):
        self.awaiting_2fa = True
        self.twofa_frame.pack(fill="x", pady=(0, 12), before=self.login_btn)
        self.twofa_entry.focus()
        self.login_btn.configure(text=t("ig_btn_verify"))
        self.status_label.configure(
            text=t("ig_status_2fa_prompt"),
            text_color=COLORS["instagram"],
        )

    def do_login(self):
        if self.awaiting_2fa:
            self.verify_2fa()
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.status_label.configure(
                text=t("ig_fill_all_fields"), text_color=COLORS["error_text"]
            )
            return

        self.temp_username = username
        self.temp_password = password
        self.login_btn.configure(state="disabled", text=t("ig_btn_logging_in"))
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
            # Security: clear password from memory
            self.temp_password = None
            self.destroy()
        elif message == "2FA_REQUIRED":
            self.login_btn.configure(state="normal")
            self.show_2fa_input()
        else:
            self.status_label.configure(text=message, text_color=COLORS["error_text"])
            self.login_btn.configure(state="normal", text=t("ig_btn_login"))
            # Security: clear password on failure too
            self.temp_password = None

    def verify_2fa(self):
        code = self.twofa_entry.get().strip()

        if not code or len(code) != 6 or not code.isdigit():
            self.status_label.configure(
                text=t("ig_enter_6digit"), text_color=COLORS["error_text"]
            )
            return

        self.login_btn.configure(state="disabled", text=t("ig_btn_verifying"))

        def verify_thread():
            success, message = self.downloader.login_with_2fa(
                self.temp_username, self.temp_password, code
            )
            self.after(0, lambda: self.handle_2fa_result(success, message))

        threading.Thread(target=verify_thread, daemon=True).start()

    def handle_2fa_result(self, success: bool, message: str):
        if success:
            self.downloader.save_session(self.temp_username)
            self.on_login_success(self.temp_username, self.downloader)
            # Security: clear password from memory
            self.temp_password = None
            self.destroy()
        else:
            self.status_label.configure(text=message, text_color=COLORS["error_text"])
            self.login_btn.configure(state="normal", text=t("ig_btn_verify"))
            self.twofa_entry.delete(0, "end")
