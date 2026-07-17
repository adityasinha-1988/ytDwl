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

## Streamlit Cloud pe deploy karna

App ab multi-user ke liye safe hai — har browser session ka apna alag
download folder hota hai (`downloads/<session_id>/`), aur `packages.txt` me
`ffmpeg` add kiya hai jo Streamlit Cloud automatically install kar lega.

**Zaroori baatein deploy karne se pehle:**

1. `app.py`, `requirements.txt`, aur `packages.txt` teeno files GitHub repo me
   push karo — Streamlit Cloud repo se hi deploy karta hai.
2. **Storage temporary hai.** Server restart/redeploy hone par saari
   downloaded files delete ho jaati hain. User ko turant "Download" button se
   file apne PC pe le lena chahiye.
3. **YouTube cloud IPs block/rate-limit kar sakta hai.** Streamlit Cloud ka
   shared datacenter IP kabhi kabhi YouTube ko "bot jaisa" lagta hai aur wo
   "Sign in to confirm you're not a bot" jaisa error de sakta hai — yeh
   local PC pe nahi hota. Iska fix cookies file upload karna ho sakta hai
   (sidebar me already option hai), ya ek residential/rotating proxy use
   karna (Proxy field me daal sakte ho).
4. **Free tier resource-limited hai** (~1GB RAM) — bahut badi playlist ya
   lambi videos timeout/crash kar sakti hain.
5. Public URL pe deploy karne ka matlab koi bhi is tool ka use karke content
   download kar payega — agar sirf apne personal use ke liye chahiye to app
   ko private/unlisted rakhna behtar hoga.


## Note

Ye app already `yt-dlp` (actively maintained fork) use kar raha hai, isliye
purane `youtube-dl` wali "page needs to be reloaded" jaisi dikkat nahi aani
chahiye. Agar kabhi downloads fail hone lagein, pehle `pip install -U yt-dlp`
se update kar lena — YouTube changes hone par yt-dlp bhi jaldi update hota hai.

**Clip / specific-duration download troubleshoot karna:** Agar clip theek se
kaam na kare, "More Options" expander me "🐞 Debug mode" on karke dobara try
karo — download poora hone (ya fail hone) ke baad ek "Debug log" expander
dikhega jisme yt-dlp ka poora internal log hoga. Wo error message share karna
sabse jaldi diagnose karne me madad karega.


