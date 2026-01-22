import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_exe():
    print("🚀 Syronss's Media Downloader derleniyor...")
    
    # Temizlik
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
        
    # PyInstaller komutu
    # --noconsole: Konsol penceresi açılmaz
    # --onefile: Tek dosya (eğer isterseniz) ama --onedir daha hızlı açılır ve güncellemesi kolaydır
    # Biz burada launcher.py'yi giriş noktası yapıyoruz
    
    args = [
        'launcher.py',  # Giriş dosyası
        '--name=SyronssMediaDownloader',
        '--noconfirm',
        '--clean',
        '--windowed',  # GUI uygulaması
        '--icon=NONE', # İkon yoksa varsayılan
        '--add-data=requirements.txt;.', # requirements.txt'yi kök dizine kopyala
    ]
    
    # İkon varsa ekle (varsayım)
    if os.path.exists("icon.ico"):
        args.append('--icon=icon.ico')
        
    # CustomTkinter veri dosyalarını bul ve ekle
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    args.append(f'--add-data={ctk_path};customtkinter')
    
    # Derle
    PyInstaller.__main__.run(args)
    
    print("\n✅ Derleme tamamlandı!")
    print(f"📂 Uygulamanız burada: {os.path.abspath('dist/VideoDownloaderPro')}")

if __name__ == "__main__":
    # PyInstaller kurulu mu?
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller kuruluyor...")
        os.system("pip install pyinstaller")
        
    build_exe()
