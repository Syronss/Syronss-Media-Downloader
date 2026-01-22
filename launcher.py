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

def get_required_packages():
    """requirements.txt dosyasından gerekli paketleri oku."""
    req_file = Path(__file__).parent / "requirements.txt"
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
        self.root.title("Syronss's Media Downloader Hazırlanıyor")
        self.root.geometry("450x200")
        self.root.resizable(False, False)
        
        # Ekranın ortasında aç
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 200) // 2
        self.root.geometry(f"+{x}+{y}")
        
        self.status_label = tk.Label(self.root, text="Sistem kontrolleri yapılıyor...", font=("Segoe UI", 10))
        self.status_label.pack(pady=(20, 10))
        
        self.progress = ttk.Progressbar(self.root, length=350, mode='determinate')
        self.progress.pack(pady=10)
        
        self.detail_label = tk.Label(self.root, text="", font=("Segoe UI", 8), fg="gray")
        self.detail_label.pack(pady=5)
        
        self.app_ready = False

    def update_status(self, text, detail="", progress_val=None, mode="determinate"):
        # UI güncellemelerini ana thread'de yap
        self.root.after(0, lambda: self._update_ui(text, detail, progress_val, mode))

    def _update_ui(self, text, detail, progress_val, mode):
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

    def start(self):
        threading.Thread(target=self.run_checks, daemon=True).start()
        self.root.mainloop()

    def run_checks(self):
        # 0. Frozen (Compiled) Kontrolü
        if getattr(sys, 'frozen', False):
            # Derlenmiş uygulamada paketler zaten içindedir, sadece FFmpeg kontrolü yap
            self.ensure_ffmpeg()
            return

        # 1. Python Paketlerini Kontrol Et
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
        
        # 2. FFmpeg Kontrol Et ve İndir
        self.ensure_ffmpeg()

    def install_packages(self, packages):
        total = len(packages)
        for i, pkg in enumerate(packages):
            pkg_name = pkg.split(">=")[0].split("==")[0].strip()
            self.update_status(f"Gerekli kütüphaneler kuruluyor ({i+1}/{total})", f"Kuruluyor: {pkg_name}", (i/total)*100)
            
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--no-warn-script-location"])
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Kütüphane kurulamadı:\n{pkg}\n\nHata: {str(e)}"))
                sys.exit(1)
        
        self.update_status("Kütüphaneler hazır", "", 100)

    def ensure_ffmpeg(self):
        self.update_status("FFmpeg kontrol ediliyor...", mode="indeterminate")
        
        # Sistemde var mı?
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.launch_app()
            return
        except FileNotFoundError:
            pass
            
        # Lokal bin klasöründe var mı?
        bin_dir = Path(__file__).parent / "bin"
        ffmpeg_exe = bin_dir / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            # PATH'e ekle
            os.environ["PATH"] += os.pathsep + str(bin_dir)
            self.launch_app()
            return

        # İndir
        self.download_ffmpeg(bin_dir)

    def download_ffmpeg(self, bin_dir):
        bin_dir.mkdir(exist_ok=True)
        # Windows için gyan.dev'den essentials build (daha küçük)
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = bin_dir / "ffmpeg.zip"
        
        self.update_status("FFmpeg indiriliyor (Bu işlem biraz sürebilir)...", "İndiriliyor: ffmpeg-release-essentials.zip", 0, "determinate")
        
        try:
            def report_progress(block_num, block_size, total_size):
                percent = (block_num * block_size / total_size) * 100
                self.update_status("FFmpeg indiriliyor...", f"%{percent:.1f} tamamlandı", percent)

            urllib.request.urlretrieve(url, zip_path, report_progress)
            
            self.update_status("FFmpeg kuruluyor...", "Arşivden çıkarılıyor...", mode="indeterminate")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Zip içindeki ffmpeg.exe'yi bul
                ffmpeg_src = None
                for name in zip_ref.namelist():
                    if name.endswith("bin/ffmpeg.exe"):
                        ffmpeg_src = name
                        break
                
                if ffmpeg_src:
                    # Sadece exe'yi çıkar
                    source = zip_ref.open(ffmpeg_src)
                    target = open(bin_dir / "ffmpeg.exe", "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                        
                # ffprobe da lazım olabilir
                ffprobe_src = None
                for name in zip_ref.namelist():
                    if name.endswith("bin/ffprobe.exe"):
                        ffprobe_src = name
                        break
                
                if ffprobe_src:
                    source = zip_ref.open(ffprobe_src)
                    target = open(bin_dir / "ffprobe.exe", "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)

            # Temizlik
            zip_path.unlink()
            
            # PATH'e ekle
            os.environ["PATH"] += os.pathsep + str(bin_dir)
            
            self.launch_app()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"FFmpeg indirilemedi:\n{str(e)}"))
            sys.exit(1)

    def launch_app(self):
        self.update_status("Uygulama başlatılıyor...", mode="indeterminate")
        self.app_ready = True
        self.root.after(1000, self.close_and_start)

    def close_and_start(self):
        self.progress.stop()  # Progress bar'ı durdur
        self.root.destroy()
        try:
            import main
            app = main.VideoDownloaderApp()
            app.mainloop()
        except Exception as e:
            messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı:\n{str(e)}")

if __name__ == "__main__":
    LauncherUI().start()
