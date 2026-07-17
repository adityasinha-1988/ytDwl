# YT Downloader Pro 🎬

A simple, GUI-friendly Streamlit app built on top of `yt-dlp`. No need for command line — just paste a link and click.

## Setup (one-time)

```bash
pip install -r requirements.txt
```

**Required:** `ffmpeg` must also be installed on your system (for video conversion, thumbnail/subtitle embedding).

- Windows: Download from https://ffmpeg.org/download.html and add to PATH, or use `choco install ffmpeg`
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Running

```bash
streamlit run app.py
```

The app will open automatically in your browser (default: http://localhost:8501).

## Features

- **Single Video tab** — Paste URL → "Fetch Info" to preview title/thumbnail → choose quality → download.
- **Playlist tab** — Download entire playlists or videos within a start/end index range.
- **Downloaded Files tab** — Download saved files to your device, or delete them.
- **Sidebar (Advanced Settings)** — Filename template, proxy, speed limit, cookies file (for login-required/age-restricted videos).
- **Quality options** — Best, 1080p/720p/480p/360p, or Audio-only.
- **Extra options** — Download & embed subtitles, embed thumbnails, add metadata.
- **✂️ Clip / specific duration** — Instead of downloading the entire video/audio, extract only a time range (e.g., 00:30 to 02:15). Available in both Single Video and Playlist tabs.
- **🧩 More Options** (expander) —
  - Video container: mp4 / mkv / webm
  - Audio format: mp3 / m4a / wav / opus / vorbis / flac + bitrate (64–320 kbps)
  - Embed chapters
  - SponsorBlock — automatically remove sponsor/ads/intro/outro segments from videos
  - Retries count, save description `.txt` and info `.json`
  - 🐞 Debug mode — enables verbose yt-dlp logging to troubleshoot issues
- **📚 Batch Download** — Below the Single Video tab, paste multiple URLs (one per line) to download them all at once.

## Deploying to Streamlit Cloud

The app is now multi-user safe — each browser session has its own download folder (`downloads/<session_id>/`), and `packages.txt` includes `ffmpeg` which Streamlit Cloud will automatically install.

**Important before deploying:**

1. Push all three files to your GitHub repo — `app.py`, `requirements.txt`, and `packages.txt`. Streamlit Cloud deploys from your repo.
2. **Storage is temporary.** When the server restarts or redeploys, all downloaded files are deleted. Users should immediately click the "Download" button in the "Downloaded Files" tab to save files to their PC.
3. **YouTube may rate-limit cloud IPs.** Streamlit Cloud uses a shared datacenter IP, which YouTube sometimes blocks as "bot-like" (this doesn't happen on local PCs). Workaround: upload a cookies file (option in sidebar) or set a residential proxy (in Proxy field).
4. **Free tier is resource-limited** (~1GB RAM) — very large playlists or long videos may timeout/crash.
5. **Public deployment means anyone can use this tool** — if you only want personal access, keep the app private/unlisted.

## Troubleshooting

### Clip/time-range download failing

If clip extraction fails with a message like "ffmpeg is not installed":
- When deployed on Streamlit Cloud: Make sure `packages.txt` (with `ffmpeg` inside) is pushed to your GitHub repo. Reboot the app from "Manage app" panel so the container rebuilds and installs ffmpeg.
- Locally: Install ffmpeg on your system (see Setup section above).

### General download failures

Enable **🐞 Debug mode** in the "More Options" expander. After the download attempt, a "Debug log" section will appear showing yt-dlp's internal output. Share this log for faster troubleshooting.

### HTTP Error 403: Forbidden

This means YouTube is blocking the request — very common on cloud platforms like Streamlit Cloud because they use shared datacenter IPs that YouTube flags as suspicious (this usually doesn't happen on a local PC with a residential IP).

The app already tries a workaround (falling back through Android/TV/iOS YouTube clients, which often bypasses this). If it still happens:

1. **Update yt-dlp** — YouTube changes its systems often, and yt-dlp ships fixes frequently. Locally: `pip install -U yt-dlp`. On Streamlit Cloud: bump the version in `requirements.txt` (already pinned to a recent version) and reboot.
2. **Use a cookies file** (most reliable fix) — Export cookies from a logged-in YouTube session in your browser (e.g., using the "Get cookies.txt" extension) and upload the `.txt` file in the sidebar's "Cookies file" field. This makes requests look like they're coming from a real logged-in browser.
3. **Use a proxy** — Set a residential/rotating proxy in the sidebar's Proxy field if cookies alone don't help.
4. This issue is inherent to running scrapers on shared cloud infrastructure — it may recur periodically as YouTube adjusts its blocking rules.

## Note

This app uses `yt-dlp` (actively maintained fork of youtube-dl). Since YouTube changes its page structure frequently, if downloads start failing, update yt-dlp: `pip install -U yt-dlp`. The yt-dlp project releases updates regularly to keep pace with YouTube changes.



