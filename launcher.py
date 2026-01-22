"""
Syronss's Media Downloader - Launcher & Dependency Manager
Robust error handling, FFmpeg auto-download, and graceful startup
"""
import sys
import os
import subprocess
import importlib.util
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import urllib.request
import zipfile
import shutil
import ssl
import traceback


def get_app_dir():
    """Uygulama dizinini al (frozen veya normal)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_ffmpeg_dir():
    """FFmpeg'in kaydedileceği dizini al."""
    # AppData'da sakla - böylece uygulama güncellendiğinde tekrar indirmek zorunda kalmaz
    app_data = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    ffmpeg_dir = app_data / 'SyronssMediaDownloader' / 'ffmpeg'
    return ffmpeg_dir


def get_required_packages():
    """requirements.txt dosyasından gerekli paketleri oku."""
    req_file = get_app_dir() / "requirements.txt"
    if not req_file.exists():
        return []
    
    packages = []
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                packages.append(line)
    return packages


class LauncherUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Syronss's Media Downloader")
        self.root.geometry("500x250")
        self.root.resizable(False, False)
        
        # Modern görünüm
        self.root.configure(bg="#1a1a2e")
        
        # Ekranın ortasında aç
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 250) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Ana frame
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Logo/Başlık
        title_label = tk.Label(main_frame, text="🎬 Syronss's Media Downloader", 
                               font=("Segoe UI", 16, "bold"), fg="#e94560", bg="#1a1a2e")
        title_label.pack(pady=(10, 5))
        
        subtitle_label = tk.Label(main_frame, text="YouTube • TikTok • Instagram", 
                                  font=("Segoe UI", 10), fg="#888888", bg="#1a1a2e")
        subtitle_label.pack(pady=(0, 20))
        
        # Durum
        self.status_label = tk.Label(main_frame, text="Başlatılıyor...", 
                                     font=("Segoe UI", 11), fg="#ffffff", bg="#1a1a2e")
        self.status_label.pack(pady=(10, 5))
        
        # Progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", 
                       troughcolor='#16213e', background='#e94560',
                       darkcolor='#e94560', lightcolor='#e94560',
                       bordercolor='#16213e')
        
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate',
                                        style="Custom.Horizontal.TProgressbar")
        self.progress.pack(pady=15)
        
        # Detay
        self.detail_label = tk.Label(main_frame, text="", font=("Segoe UI", 9), 
                                     fg="#666666", bg="#1a1a2e")
        self.detail_label.pack(pady=5)
        
        self.app_ready = False
        self.ffmpeg_declined = False

    def update_status(self, text, detail="", progress_val=None, mode="determinate"):
        self.root.after(0, lambda: self._update_ui(text, detail, progress_val, mode))

    def _update_ui(self, text, detail, progress_val, mode):
        try:
            self.status_label.config(text=text)
            self.detail_label.config(text=detail)
            if mode:
                self.progress["mode"] = mode
                if mode == "indeterminate":
                    self.progress.start(10)
                else:
                    self.progress.stop()
            
            if progress_val is not None:
                self.progress["value"] = progress_val
        except tk.TclError:
            pass  # Widget destroyed

    def start(self):
        threading.Thread(target=self.run_checks, daemon=True).start()
        self.root.mainloop()

    def run_checks(self):
        try:
            # Frozen (Compiled) Kontrolü
            if getattr(sys, 'frozen', False):
                # Derlenmiş uygulamada paketler zaten içindedir
                self.ensure_ffmpeg()
                return

            # Python Paketlerini Kontrol Et
            packages = get_required_packages()
            missing_packages = []
            
            map_pkg_to_import = {
                "Pillow": "PIL",
                "customtkinter": "customtkinter",
                "yt-dlp": "yt_dlp",
                "instaloader": "instaloader"
            }
            
            for pkg_line in packages:
                pkg_name = pkg_line.split(">=")[0].split("==")[0].split("<")[0].strip()
                import_name = map_pkg_to_import.get(pkg_name, pkg_name)
                
                if importlib.util.find_spec(import_name) is None:
                    missing_packages.append(pkg_line)
            
            if missing_packages:
                self.install_packages(missing_packages)
            
            # FFmpeg Kontrol
            self.ensure_ffmpeg()
            
        except Exception as e:
            error_msg = f"Başlatma hatası:\n{str(e)}\n\n{traceback.format_exc()}"
            self.root.after(0, lambda: self.show_error_and_exit(error_msg))

    def show_error_and_exit(self, msg):
        messagebox.showerror("Kritik Hata", msg)
        self.root.destroy()
        sys.exit(1)

    def install_packages(self, packages):
        total = len(packages)
        for i, pkg in enumerate(packages):
            pkg_name = pkg.split(">=")[0].split("==")[0].strip()
            self.update_status(f"Kütüphaneler kuruluyor ({i+1}/{total})", 
                             f"Kuruluyor: {pkg_name}", (i/total)*100)
            
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, 
                                      "--no-warn-script-location", "-q"],
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", 
                    f"Kütüphane kurulamadı:\n{pkg}\n\nHata: {str(e)}"))
                sys.exit(1)
        
        self.update_status("Kütüphaneler hazır", "", 100)

    def ensure_ffmpeg(self):
        self.update_status("FFmpeg kontrol ediliyor...", mode="indeterminate")
        
        # 1. Sistemde kurulu mu?
        if self.check_ffmpeg_in_path():
            self.launch_app()
            return
        
        # 2. AppData'da var mı?
        ffmpeg_dir = get_ffmpeg_dir()
        ffmpeg_exe = ffmpeg_dir / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
            self.launch_app()
            return
        
        # 3. Uygulama yanında bin/ klasöründe var mı?
        app_bin = get_app_dir() / "bin"
        if (app_bin / "ffmpeg.exe").exists():
            os.environ["PATH"] = str(app_bin) + os.pathsep + os.environ.get("PATH", "")
            self.launch_app()
            return
        
        # 4. FFmpeg yok - kullanıcıya sor
        self.root.after(0, self.ask_ffmpeg_download)

    def check_ffmpeg_in_path(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   capture_output=True, 
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def ask_ffmpeg_download(self):
        result = messagebox.askyesno(
            "FFmpeg Gerekli",
            "Bu uygulama video işleme için FFmpeg kullanır.\n\n"
            "FFmpeg sisteminizde bulunamadı.\n\n"
            "FFmpeg'i otomatik olarak indirmek ister misiniz?\n"
            "(~100 MB, bir kerelik indirme)\n\n"
            "NOT: FFmpeg olmadan sadece bazı videolar indirilebilir,\n"
            "kalite seçimi ve MP3 dönüşümü çalışmaz.",
            icon='question'
        )
        
        if result:
            threading.Thread(target=self.download_ffmpeg, daemon=True).start()
        else:
            self.ffmpeg_declined = True
            # FFmpeg olmadan devam et
            messagebox.showwarning(
                "FFmpeg Atlandı",
                "FFmpeg olmadan devam ediliyor.\n\n"
                "Bazı özellikler (MP3 dönüşümü, kalite seçimi) çalışmayabilir."
            )
            self.launch_app()

    def download_ffmpeg(self):
        ffmpeg_dir = get_ffmpeg_dir()
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        
        # Windows için gyan.dev'den essentials build
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = ffmpeg_dir / "ffmpeg_download.zip"
        
        self.update_status("FFmpeg indiriliyor...", "Bu işlem biraz sürebilir", 0, "determinate")
        
        try:
            # SSL context for HTTPS
            ssl_context = ssl.create_default_context()
            
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min((block_num * block_size / total_size) * 100, 100)
                    downloaded_mb = (block_num * block_size) / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    self.update_status("FFmpeg indiriliyor...", 
                                      f"{downloaded_mb:.1f} / {total_mb:.1f} MB (%{percent:.0f})", 
                                      percent)

            urllib.request.urlretrieve(url, zip_path, report_progress)
            
            self.update_status("FFmpeg kuruluyor...", "Arşivden çıkarılıyor...", mode="indeterminate")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Zip içindeki exe'leri bul ve çıkar
                for name in zip_ref.namelist():
                    if name.endswith("bin/ffmpeg.exe"):
                        self.extract_file(zip_ref, name, ffmpeg_dir / "ffmpeg.exe")
                    elif name.endswith("bin/ffprobe.exe"):
                        self.extract_file(zip_ref, name, ffmpeg_dir / "ffprobe.exe")

            # Zip'i sil
            try:
                zip_path.unlink()
            except:
                pass
            
            # PATH'e ekle
            os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")
            
            self.update_status("FFmpeg kuruldu!", "", 100, "determinate")
            self.root.after(500, self.launch_app)
            
        except Exception as e:
            error_msg = f"FFmpeg indirilemedi:\n{str(e)}"
            self.root.after(0, lambda: self.handle_ffmpeg_error(error_msg))

    def extract_file(self, zip_ref, src_name, dest_path):
        with zip_ref.open(src_name) as source:
            with open(dest_path, "wb") as target:
                shutil.copyfileobj(source, target)

    def handle_ffmpeg_error(self, error_msg):
        result = messagebox.askyesno(
            "FFmpeg İndirme Hatası",
            f"{error_msg}\n\n"
            "FFmpeg olmadan devam etmek ister misiniz?\n"
            "(Bazı özellikler çalışmayabilir)"
        )
        
        if result:
            self.ffmpeg_declined = True
            self.launch_app()
        else:
            self.root.destroy()
            sys.exit(1)

    def launch_app(self):
        self.update_status("Uygulama başlatılıyor...", mode="indeterminate")
        self.app_ready = True
        self.root.after(800, self.close_and_start)

    def close_and_start(self):
        try:
            self.progress.stop()
        except:
            pass
        
        self.root.destroy()
        
        try:
            # Ana uygulamayı import et ve başlat
            import main
            app = main.VideoDownloaderApp()
            app.mainloop()
        except Exception as e:
            # Hata penceresini göster
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror(
                "Kritik Hata", 
                f"Uygulama başlatılamadı:\n\n{str(e)}\n\n"
                f"Detaylar:\n{traceback.format_exc()}"
            )
            error_root.destroy()
            sys.exit(1)


def main():
    try:
        LauncherUI().start()
    except Exception as e:
        # Son çare - herhangi bir hata olursa
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Kritik Hata", f"Launcher başlatılamadı:\n{str(e)}")
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    main()
