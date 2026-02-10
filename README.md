# 🎬 Syronss's Media Downloader v2.0

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg?style=for-the-badge&logo=windows&logoColor=black" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg?style=for-the-badge" alt="UI Framework">
  <img src="https://img.shields.io/badge/Version-2.0.0-orange.svg?style=for-the-badge" alt="Version">
  <a href="https://github.com/Syronss/Syronss-Media-Downloader"><img src="https://img.shields.io/badge/GitHub-Syronss-181717.svg?style=for-the-badge&logo=github" alt="GitHub"></a>
</p>

<p align="center">
  <b>YouTube, TikTok, Instagram, Facebook, X, Vimeo, Dailymotion, Twitch</b><br>
  Video ve MP3 indirme uygulaması • Modern, hızlı, güvenli
</p>

---

## ✨ v2.0 Yenilikler

| Özellik | Açıklama |
|---------|----------|
| 🌍 **Çoklu Dil** | Türkçe ve İngilizce tam destek, dinamik geçiş |
| 📊 **İstatistik Paneli** | Toplam indirme, boyut ve platform dağılımı |
| 🔍 **Geçmiş Arama** | İndirme geçmişinde arama ve filtreleme |
| 📄 **Toplu İçe Aktarma** | Birden fazla URL'yi tek seferde kuyruğa ekleme |
| 📂 **Otomatik Klasörleme** | Platform bazlı alt klasörlere otomatik ayırma |
| 📋 **Yapıştır Butonu** | Tek tıkla panodan URL yapıştırma |
| 🔔 **Bildirimler** | İndirme tamamlandığında görev çubuğu bildirimi |
| ⚙️ **Gelişmiş Ayarlar** | Dil, tema, şablon, bildirim ve güncelleme ayarları |
| 🔄 **yt-dlp Güncelleme** | Otomatik güncelleme kontrolü ve güncelleme |
| 🧵 **Thread Güvenliği** | Çoklu indirme için güvenli durum yönetimi |
| 🏗️ **Modüler Mimari** | Temiz, bakımı kolay kod yapısı |

---

## 🚀 Özellikler

### 📥 Desteklenen Platformlar
- **YouTube** — Video, MP3, altyazı, playlist
- **TikTok** — Video indirme
- **Instagram** — Post, Reel, Story (2FA desteği ile giriş)
- **Facebook** — Video indirme
- **X (Twitter)** — Video indirme
- **Vimeo** — Video indirme
- **Dailymotion** — Video indirme
- **Twitch** — VOD ve klip

### 🎨 Modern Arayüz
- CustomTkinter tabanlı şık tasarım
- Koyu / Açık tema desteği (kalıcı)
- Video önizleme paneli
- İndirme kuyruğu sistemi
- İndirme geçmişi (arama destekli)
- İstatistik paneli

### 📸 Instagram Entegrasyonu
- Kullanıcı adı/şifre ile güvenli giriş
- 2FA (iki faktörlü kimlik doğrulama) desteği
- Post, Reel, Story indirme
- Video/Görsel modu seçimi
- Güvenli oturum yönetimi

### 🌍 Çoklu Dil Desteği
- 🇹🇷 Türkçe (varsayılan)
- 🇬🇧 English
- Ayarlardan tek tıkla dil değiştirme

---

## 📦 Kurulum

### Gereksinimler
- Python 3.8+
- FFmpeg (MP3 dönüşümü için — otomatik indirilir)

### Hızlı Kurulum

```bash
# Depoyu klonla
git clone https://github.com/Syronss/Syronss-Media-Downloader.git
cd Syronss-Media-Downloader

# Bağımlılıkları kur
pip install -r requirements.txt

# Uygulamayı başlat
python launcher.py
```

### Standalone EXE

```bash
python build_app.py
```

> EXE dosyası `dist/SyronssMediaDownloader/` klasöründe oluşturulur.

---

## 📁 Proje Yapısı

```
📂 Syronss-Media-Downloader/
├── 🚀 launcher.py          # Launcher ve bağımlılık yönetimi
├── 🎯 main.py              # Ana uygulama (VideoDownloaderApp)
├── ⬇️ downloader.py         # İndirme backend'leri (yt-dlp + instaloader)
├── 🔧 utils.py             # Yardımcı fonksiyonlar
├── 📋 constants.py          # Sabit değerler ve yapılandırma
├── 🏗️ build_app.py          # PyInstaller build scripti
│
├── 🌍 i18n/                 # Çoklu dil desteği
│   ├── __init__.py          # Dil yöneticisi
│   ├── tr.json              # Türkçe çeviriler
│   └── en.json              # İngilizce çeviriler
│
├── 🧩 widgets/              # UI bileşenleri
│   ├── queue_item.py        # Kuyruk öğesi widget'ı
│   ├── video_preview.py     # Video önizleme çerçevesi
│   ├── history_item.py      # Geçmiş öğesi widget'ı
│   └── stats_panel.py       # İstatistik paneli
│
├── 💬 dialogs/              # Diyalog pencereleri
│   ├── instagram_login.py   # Instagram giriş (2FA destekli)
│   ├── settings.py          # Ayarlar diyaloğu
│   └── batch_import.py      # Toplu URL içe aktarma
│
├── 🧪 tests/                # Testler
│   ├── conftest.py          # Paylaşılan fixture'lar
│   ├── test_downloader.py   # İndirici testleri
│   ├── test_utils.py        # Yardımcı fonksiyon testleri
│   └── test_constants_i18n.py # Sabitler ve i18n testleri
│
├── 📄 requirements.txt
├── 📄 LICENSE (MIT)
└── 📄 README.md
```

---

## 🧪 Testler

```bash
# Tüm testleri çalıştır
python -m pytest tests/ -v

# Belirli bir test dosyasını çalıştır
python -m pytest tests/test_utils.py -v
```

---

## ⚙️ Ayarlar

Uygulama ayarları `~/.video_downloader_settings.json` dosyasında saklanır:

| Ayar | Açıklama | Varsayılan |
|------|----------|------------|
| `language` | Arayüz dili | `tr` |
| `theme` | Tema (dark/light) | `dark` |
| `filename_template` | Dosya adı şablonu | `%(title)s` |
| `auto_folder` | Platform bazlı klasörleme | `false` |
| `notifications` | İndirme bildirimleri | `true` |
| `auto_update_check` | yt-dlp güncelleme kontrolü | `true` |

---

## 🔒 Güvenlik

- Instagram şifreleri bellekte saklanmaz, giriş sonrası temizlenir
- Oturum dosyaları çıkışta güvenli şekilde silinir
- Oturum bilgileri `.gitignore` ile korunur

---

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'e push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

---

## 📃 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

## 👤 Geliştirici

**Syronss** — [GitHub](https://github.com/Syronss)
