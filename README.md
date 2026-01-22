# 🎬 Syronss's Media Downloader

Modern ve kullanıcı dostu bir video indirme uygulaması. YouTube, TikTok ve Instagram'dan video ve MP3 indirebilirsiniz.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## ✨ Özellikler

- 📺 **YouTube** - Video ve MP3 indirme (4K dahil tüm kaliteler)
- 🎵 **TikTok** - Filigranlı veya filigranlı video indirme
- 📸 **Instagram** - Post, Reel ve IGTV indirme (2FA desteği ile giriş)
- 🎨 **Modern UI** - CustomTkinter ile şık karanlık tema
- 📥 **Kuyruk Sistemi** - Birden fazla video sıraya ekleyin
- ⚡ **Otomatik FFmpeg** - İlk çalıştırmada otomatik indirilir
- 📊 **Kalite Seçimi** - 360p'den 4K'ya kadar kalite seçeneği
- 🔄 **İlerleme Takibi** - Gerçek zamanlı indirme durumu

## 📋 Gereksinimler

- Python 3.8+
- Windows 10/11

## 🚀 Kurulum

### Kaynak Koddan Çalıştırma

```bash
# Repo'yu klonlayın
git clone https://github.com/Syronss/video-downloader.git
cd video-downloader

# Sanal ortam oluşturun (önerilen)
python -m venv .venv
.venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python launcher.py
```

### İlk Çalıştırma

Uygulama ilk başlatıldığında:
1. Gerekli Python kütüphanelerini kontrol eder
2. FFmpeg'i otomatik olarak indirir (~100MB)
3. Ana uygulamayı başlatır

## 📖 Kullanım

1. **URL Yapıştırın** - YouTube, TikTok veya Instagram video linkini girin
2. **Format Seçin** - Video veya MP3
3. **Kalite Seçin** - Mevcut kalite seçeneklerinden birini seçin
4. **İndirin** - "İNDİR" butonuna tıklayın

### Instagram Giriş

Private içeriklere erişmek için:
1. Sol alttaki "📸 Instagram" butonuna tıklayın
2. Kullanıcı adı ve şifrenizi girin
3. 2FA etkinse doğrulama kodunu girin

> ⚠️ Giriş bilgileriniz sadece oturumunuz süresince saklanır

## 🔧 Build (EXE Oluşturma)

Standalone .exe oluşturmak için:

```bash
# PyInstaller'ı yükleyin
pip install pyinstaller

# Build script'ini çalıştırın
python build_app.py
```

Oluşturulan uygulama `dist/SyronssMediaDownloader/` klasöründe bulunur.

## 📁 Proje Yapısı

```
video-downloader/
├── main.py           # Ana UI uygulaması
├── downloader.py     # İndirme modülleri (YouTube, TikTok, Instagram)
├── utils.py          # Yardımcı fonksiyonlar
├── launcher.py       # Bağımlılık yönetimi ve başlatıcı
├── build_app.py      # PyInstaller build script
├── requirements.txt  # Python bağımlılıkları
└── README.md
```

## 🛠️ Teknik Detaylar

- **UI Framework**: CustomTkinter
- **Video İndirme**: yt-dlp
- **Instagram API**: Instaloader
- **MP3 Dönüşüm**: FFmpeg

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## ⚠️ Sorumluluk Reddi

Bu uygulama yalnızca eğitim amaçlıdır. İndirdiğiniz içeriklerin telif hakkı yasalarına uygun olduğundan emin olun. Uygulama geliştiricileri, kullanıcıların yasa dışı kullanımından sorumlu değildir.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Syronss">Syronss</a>
</p>
