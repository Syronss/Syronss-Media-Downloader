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
  Video and MP3 downloader application • Modern, fast, secure
</p>

---

## ✨ What's New in v2.0

| Feature | Description |
| --- | --- |
| 🌍 **Multi-Language** | Full support for Turkish and English, dynamic switching |
| 📊 **Statistics Panel** | Total downloads, size, and platform distribution |
| 🔍 **History Search** | Search and filter within download history |
| 📄 **Batch Import** | Add multiple URLs to the queue at once |
| 📂 **Auto-Folder** | Automatically sort downloads into platform-based subfolders |
| 📋 **Paste Button** | One-click URL pasting from clipboard |
| 🔔 **Notifications** | Taskbar notification upon download completion |
| ⚙️ **Advanced Settings** | Language, theme, template, notification, and update settings |
| 🔄 **yt-dlp Update** | Automatic update check and updater |
| 🧵 **Thread Safety** | Safe state management for concurrent downloads |
| 🏗️ **Modular Architecture** | Clean, easy-to-maintain code structure |

---

## 🚀 Features

### 📥 Supported Platforms

* **YouTube** — Video, MP3, subtitles, playlists
* **TikTok** — Video downloading
* **Instagram** — Post, Reel, Story (Login with 2FA support)
* **Facebook** — Video downloading
* **X (Twitter)** — Video downloading
* **Vimeo** — Video downloading
* **Dailymotion** — Video downloading
* **Twitch** — VODs and clips

### 🎨 Modern Interface

* Stylish design based on CustomTkinter
* Dark / Light theme support (persistent)
* Video preview panel
* Download queue system
* Download history (with search support)
* Statistics panel

### 📸 Instagram Integration

* Secure login via username/password
* 2FA (Two-Factor Authentication) support
* Post, Reel, Story downloading
* Video/Image mode selection
* Secure session management

### 🌍 Multi-Language Support

* 🇹🇷 Turkish (default)
* 🇬🇧 English
* One-click language switching from settings

---

## 📦 Installation

### Requirements

* Python 3.8+
* FFmpeg (for MP3 conversion — automatically downloaded)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Syronss/Syronss-Media-Downloader.git
cd Syronss-Media-Downloader

# Install dependencies
pip install -r requirements.txt

# Start the application
python launcher.py

```

### Standalone EXE

```bash
python build_app.py

```

> The EXE file is created in the `dist/SyronssMediaDownloader/` folder.

---

## 📁 Project Structure

```
📂 Syronss-Media-Downloader/
├── 🚀 launcher.py          # Launcher and dependency management
├── 🎯 main.py              # Main application (VideoDownloaderApp)
├── ⬇️ downloader.py         # Download backends (yt-dlp + instaloader)
├── 🔧 utils.py             # Utility functions
├── 📋 constants.py          # Constants and configuration
├── 🏗️ build_app.py          # PyInstaller build script
│
├── 🌍 i18n/                 # Multi-language support
│   ├── __init__.py          # Language manager
│   ├── tr.json              # Turkish translations
│   └── en.json              # English translations
│
├── 🧩 widgets/              # UI components
│   ├── queue_item.py        # Queue item widget
│   ├── video_preview.py     # Video preview frame
│   ├── history_item.py      # History item widget
│   └── stats_panel.py       # Statistics panel
│
├── 💬 dialogs/              # Dialog windows
│   ├── instagram_login.py   # Instagram login (2FA supported)
│   ├── settings.py          # Settings dialog
│   └── batch_import.py      # Batch URL import
│
├── 🧪 tests/                # Tests
│   ├── conftest.py          # Shared fixtures
│   ├── test_downloader.py   # Downloader tests
│   ├── test_utils.py        # Utility function tests
│   └── test_constants_i18n.py # Constants and i18n tests
│
├── 📄 requirements.txt
├── 📄 LICENSE (MIT)
└── 📄 README.md

```

---

## 🧪 Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_utils.py -v

```

---

## ⚙️ Settings

Application settings are stored in the `~/.video_downloader_settings.json` file:

| Setting | Description | Default |
| --- | --- | --- |
| `language` | Interface language | `tr` |
| `theme` | Theme (dark/light) | `dark` |
| `filename_template` | Filename template | `%(title)s` |
| `auto_folder` | Platform-based folder organization | `false` |
| `notifications` | Download notifications | `true` |
| `auto_update_check` | yt-dlp update check | `true` |

---

## 🔒 Security

* Instagram passwords are not stored in memory; they are cleared immediately after login.
* Session files are securely deleted upon exit.
* Session information is protected via `.gitignore`.

---

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Added new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

---

## 📃 License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).

---

## 👤 Developer

**Syronss** — [GitHub](https://github.com/Syronss)
