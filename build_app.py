"""
Syronss's Media Downloader - Build Script
PyInstaller ile standalone EXE oluşturma
"""
import os
import sys
import shutil
from pathlib import Path


def build_exe():
    print("🚀 Syronss's Media Downloader derleniyor...")
    print("=" * 50)
    
    # Temizlik
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            print(f"🧹 {folder}/ temizleniyor...")
            shutil.rmtree(folder)
    
    for spec_file in Path(".").glob("*.spec"):
        print(f"🧹 {spec_file} siliniyor...")
        spec_file.unlink()
    
    # PyInstaller'ı import et
    try:
        import PyInstaller.__main__
    except ImportError:
        print("📦 PyInstaller kuruluyor...")
        os.system(f"{sys.executable} -m pip install pyinstaller -q")
        import PyInstaller.__main__
    
    # CustomTkinter path
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
    except ImportError:
        print("❌ CustomTkinter bulunamadı! Önce 'pip install customtkinter' çalıştırın.")
        sys.exit(1)
    
    print("\n📦 Derleme başlıyor...")
    
    # PyInstaller argümanları
    args = [
        'launcher.py',
        '--name=SyronssMediaDownloader',
        '--noconfirm',
        '--clean',
        '--windowed',
        f'--add-data={ctk_path};customtkinter',
        '--collect-all=customtkinter',
        '--collect-all=yt_dlp',
        '--collect-all=instaloader',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
    ]
    
    # İkon varsa ekle
    icon_files = ["icon.ico", "app.ico", "logo.ico"]
    for ico in icon_files:
        if os.path.exists(ico):
            args.append(f'--icon={ico}')
            print(f"🎨 İkon: {ico}")
            break
    
    # Derle
    PyInstaller.__main__.run(args)
    
    # Sonuç
    dist_path = Path("dist") / "SyronssMediaDownloader"
    if dist_path.exists():
        print("\n" + "=" * 50)
        print("✅ Derleme başarıyla tamamlandı!")
        print(f"📂 Uygulama: {dist_path.absolute()}")
        print(f"🚀 Çalıştırmak için: {dist_path / 'SyronssMediaDownloader.exe'}")
        
        # ZIP oluştur
        print("\n📦 Release için ZIP oluşturuluyor...")
        zip_name = "SyronssMediaDownloader_v1.0.0_Windows"
        shutil.make_archive(f"dist/{zip_name}", 'zip', "dist", "SyronssMediaDownloader")
        print(f"✅ ZIP: dist/{zip_name}.zip")
        
        print("\n" + "=" * 50)
        print("🎉 Tamamlandı! GitHub Releases'a yükleyebilirsiniz.")
    else:
        print("\n❌ Derleme başarısız oldu!")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
