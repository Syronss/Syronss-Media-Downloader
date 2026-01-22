

\# 🎬 Syronss's Media Downloader



<p align="center">

&nbsp; <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg?style=for-the-badge\&logo=python\&logoColor=white" alt="Python">

&nbsp; <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg?style=for-the-badge\&logo=windows\&logoColor=black" alt="Platform">

&nbsp; <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License">

&nbsp; <img src="https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg?style=for-the-badge" alt="UI Framework">

</p>



<p align="center">

&nbsp; <strong>A modern, powerful, and user-friendly media downloader application built with Python.</strong>

&nbsp; <br>

&nbsp; Download videos and audio from YouTube, TikTok, and Instagram with ease.

</p>



<p align="center">

&nbsp; <a href="#-features">Features</a> •

&nbsp; <a href="#-installation">Installation</a> •

&nbsp; <a href="#-usage">Usage</a> •

&nbsp; <a href="#-building-executable">Build EXE</a> •

&nbsp; <a href="#-tech-stack">Tech Stack</a>

</p>



---



\## ✨ Features



Syronss's Media Downloader offers a sleek GUI and robust backend to handle various media platforms.



\* 📺 \*\*YouTube Downloader\*\*

&nbsp;   \* Download Videos (up to 4K/2160p resolution).

&nbsp;   \* Convert to MP3 (High Quality).

\* 🎵 \*\*TikTok Support\*\*

&nbsp;   \* Download viral TikTok videos effortlessly.

\* 📸 \*\*Instagram Integration\*\*

&nbsp;   \* Download Posts, Reels, and IGTV.

&nbsp;   \* \*\*Advanced Auth:\*\* Supports login with 2FA (Two-Factor Authentication) for private content.

&nbsp;   \* Secure session management.

\* 🎨 \*\*Modern UI\*\*

&nbsp;   \* Built with `CustomTkinter` for a clean, dark-themed experience.

&nbsp;   \* Real-time progress bars and status updates.

\* 📥 \*\*Queue System\*\*

&nbsp;   \* Add multiple links to a queue and batch download them automatically.

\* ⚡ \*\*Smart Dependencies\*\*

&nbsp;   \* \*\*Auto-FFmpeg:\*\* Automatically checks, downloads, and configures FFmpeg on the first run. No manual setup required!



\## 📋 Prerequisites



\* \*\*OS:\*\* Windows 10 / 11

\* \*\*Python:\*\* Version 3.8 or higher



\## 🚀 Installation



\### Running from Source



1\.  \*\*Clone the Repository\*\*

&nbsp;   ```bash

&nbsp;   git clone \[https://github.com/Syronss/video-downloader.git](https://github.com/Syronss/video-downloader.git)

&nbsp;   cd video-downloader

&nbsp;   ```



2\.  \*\*Set up a Virtual Environment (Recommended)\*\*

&nbsp;   ```bash

&nbsp;   python -m venv .venv

&nbsp;   # Activate the virtual environment:

&nbsp;   .venv\\Scripts\\activate

&nbsp;   ```



3\.  \*\*Install Dependencies\*\*

&nbsp;   ```bash

&nbsp;   pip install -r requirements.txt

&nbsp;   ```



4\.  \*\*Launch the Application\*\*

&nbsp;   ```bash

&nbsp;   python launcher.py

&nbsp;   ```

&nbsp;   \*(Note: Run `launcher.py` instead of `main.py` to ensure FFmpeg is handled correctly.)\*



\## 📖 Usage



1\.  \*\*Paste URL:\*\* Copy a link from YouTube, TikTok, or Instagram and paste it into the input field.

2\.  \*\*Select Format:\*\* Choose between \*\*Video\*\* (MP4) or \*\*Audio\*\* (MP3).

3\.  \*\*Choose Quality:\*\* Select your preferred resolution (from 360p up to 4K).

4\.  \*\*Download:\*\* Click the \*\*DOWNLOAD\*\* button or \*\*Add to Queue\*\*.



\### 📸 Instagram Login (For Private Content)

To download content from private accounts or verify age-restricted content:

1\.  Click the \*\*"📸 Instagram"\*\* button at the bottom left.

2\.  Enter your username and password.

3\.  If 2FA is enabled, the app will prompt you for the verification code.

> 🔒 \*\*Privacy Note:\*\* Your credentials are used locally for the session and are not stored permanently strictly beyond the session file.



\## 🔧 Building (Create Standalone .exe)



You can convert this Python script into a standalone Windows executable file.



1\.  \*\*Install PyInstaller\*\*

&nbsp;   ```bash

&nbsp;   pip install pyinstaller

&nbsp;   ```



2\.  \*\*Run the Build Script\*\*

&nbsp;   ```bash

&nbsp;   python build\_app.py

&nbsp;   ```



3\.  \*\*Locate the App\*\*

&nbsp;   The compiled application will be available in the `dist/SyronssMediaDownloader/` directory.



\## 📁 Project Structure



```text

video-downloader/

├── main.py           # Main GUI application logic

├── downloader.py     # Backend logic (yt-dlp \& instaloader wrappers)

├── launcher.py       # Entry point (Handles FFmpeg checks \& dependencies)

├── utils.py          # Helper functions (URL detection, formatting)

├── build\_app.py      # Automated PyInstaller build script

├── requirements.txt  # Project dependencies

└── README.md         # Documentation



```



\## 🛠️ Tech Stack



\* \*\*GUI:\*\* \[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

\* \*\*Core Downloading:\*\* \[yt-dlp](https://github.com/yt-dlp/yt-dlp)

\* \*\*Instagram API:\*\* \[Instaloader](https://instaloader.github.io/)

\* \*\*Media Processing:\*\* \[FFmpeg](https://ffmpeg.org/)



\## 🐛 Troubleshooting



\*\*FFmpeg not found?\*\*

\- The app automatically downloads FFmpeg on first run

\- Manual download: \[FFmpeg.org](https://ffmpeg.org/download.html)



\*\*Instagram login fails?\*\*

\- Check your username/password

\- Verify 2FA code is correct

\- Try again after a few minutes

&nbsp; 

\## 📄 License



This project is licensed under the MIT License. See the \[LICENSE](LICENSE) file for details.



\## ⚠️ Disclaimer



This application is developed for educational purposes only. Users are responsible for ensuring that their downloads comply with copyright laws and the terms of service of the respective platforms. The developer assumes no liability for misuse.



\## 🤝 Contributing



Contributions are welcome! Please feel free to submit a Pull Request.



1\. Fork the Project

2\. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)

3\. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)

4\. Push to the Branch (`git push origin feature/AmazingFeature`)

5\. Open a Pull Request

---



<p align="center">

Made by  <a href="https://github.com/Syronss">Syronss</a>

</p>



```





