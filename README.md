# YT Downloader Pro 🎬

`youtube-dl` ke upar bana hua ek simple, GUI-friendly Streamlit app. Command
line ki zaroorat nahi — bas URL paste karo aur click karo.

## Setup (ek baar)

```bash
pip install -r requirements.txt
```

**Zaroori:** `ffmpeg` bhi system me install hona chahiye (video convert,
thumbnail/subtitle embed karne ke liye).

- Windows: https://ffmpeg.org/download.html se download karke PATH me daalein,
  ya `choco install ffmpeg`
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Run karna

```bash
streamlit run app.py
```

Browser me apne aap khul jayega (default: http://localhost:8501).

## Features

- **Single Video tab** — URL paste karo → "Info Fetch Karein" se title/thumbnail
  preview dekho → quality choose karo → download.
- **Playlist tab** — poori playlist ya start/end index ke beech ke videos
  download karo.
- **Downloaded Files tab** — jitni bhi files download hui hain, unhe yahan se
  download button se apne device pe le jao, ya delete karo.
- **Sidebar (Advanced Settings)** — filename template, proxy, speed limit,
  cookies file (login-required videos ke liye jaise private/age-restricted).
- **Quality options** — Best, 1080p/720p/480p/360p, ya Audio-only.
- **Extra options** — subtitles download + embed, thumbnail embed, metadata add.
- **✂️ Clip / specific duration** — poora video/audio download karne ki jagah
  sirf ek time-range (e.g. 00:30 se 02:15 tak) hi nikalo. Single Video aur
  Playlist dono tabs me available hai.
- **🧩 More Options** (expander) —
  - Video container: mp4 / mkv / webm
  - Audio format: mp3 / m4a / wav / opus / vorbis / flac + bitrate (64–320 kbps)
  - Chapters embed karna
  - SponsorBlock — video se sponsor/ads/intro/outro segments hataana
  - Retries count, description `.txt` aur info `.json` save karna
- **📚 Batch Download** — Single Video tab ke neeche, ek saath multiple URLs
  (ek line me ek link) daal ke sab download kar sakte ho.

## Note

`youtube-dl` kaafi purana project ho chuka hai aur kai baar naye YouTube
changes ke saath fail karta hai. Agar downloads fail hone lagein, to isi app
ka structure `yt-dlp` (actively maintained fork, same options) ke saath bhi
kaam karta hai — bas `requirements.txt` me `youtube-dl` ki jagah `yt-dlp`
likh dena aur `app.py` me `import youtube_dl` ko `import yt_dlp as youtube_dl`
kar dena, baaki sab code same rahega.
