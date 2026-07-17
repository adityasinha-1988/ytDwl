"""
YT Downloader Pro
------------------
Ek self-contained Streamlit app jo youtube-dl ke saare useful options ko
ek simple, click-friendly GUI ke peeche wrap karta hai.

Run karne ke liye:
    pip install -r requirements.txt
    streamlit run app.py

Note: video/audio conversion, thumbnail embedding aur subtitle embedding ke
liye system me `ffmpeg` install hona chahiye.
"""

import streamlit as st
import yt_dlp as youtube_dl
import os
import glob
import re
import uuid
import tempfile
import traceback
from datetime import datetime

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
# Har browser session ko apna alag folder milta hai, taaki jab yeh app
# ek shared server (jaise Streamlit Cloud) pe deploy ho to ek user
# doosre user ki downloaded files na dekh/le sake.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid.uuid4().hex[:12]

BASE_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, st.session_state["session_id"])
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cleanup_old_sessions(max_age_hours=6):
    """Purane session folders delete karo taaki server ki disk full na ho."""
    import time
    if not os.path.isdir(BASE_DOWNLOAD_DIR):
        return
    now = time.time()
    for name in os.listdir(BASE_DOWNLOAD_DIR):
        path = os.path.join(BASE_DOWNLOAD_DIR, name)
        if path == DOWNLOAD_DIR:
            continue  # apna current session mat chhedo
        try:
            if os.path.isdir(path) and (now - os.path.getmtime(path)) > max_age_hours * 3600:
                import shutil
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass


cleanup_old_sessions()

st.set_page_config(page_title="YT Downloader Pro", page_icon="🎬", layout="wide")

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button {
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
    }
    .yt-card {
        background: #1a1c24;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #2a2d3a;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 YT Downloader Pro")
st.caption("Powered by yt-dlp — bas link paste karo aur click karo, command yaad rakhne ki zaroorat nahi.")

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def parse_rate_limit(text):
    """Convert '1M', '500K' etc into bytes/sec int for youtube_dl."""
    if not text:
        return None
    text = text.strip().upper()
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1024)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1024 * 1024)
        return int(text)
    except ValueError:
        return None


def parse_time_to_seconds(text):
    """Accepts 'HH:MM:SS', 'MM:SS' or plain seconds -> returns int seconds (or None)."""
    if not text:
        return None
    text = text.strip()
    if re.fullmatch(r"\d+", text):
        return int(text)
    parts = text.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 2:
        m, s = parts
        return m * 60 + s
    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    return None


def save_uploaded_cookies(uploaded_file):
    if uploaded_file is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write(uploaded_file.getvalue())
    tmp.close()
    return tmp.name


def build_format_string(quality: str) -> str:
    mapping = {
        "Best (video+audio)": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "Audio only": "bestaudio/best",
    }
    return mapping.get(quality, "best")


def build_ydl_opts(
    quality, subtitles, sub_langs, embed_subs, embed_thumb, add_metadata,
    output_template, proxy, rate_limit_text, cookies_path,
    playlist=False, playlist_start=None, playlist_end=None, progress_hook=None,
    container_format="mp4", audio_format="mp3", audio_bitrate="192",
    embed_chapters=False, sponsorblock_categories=None, retries=10,
    write_description=False, write_infojson=False,
    clip_start_sec=None, clip_end_sec=None, debug_mode=False, logger=None,
):
    fmt = build_format_string(quality)
    outtmpl = os.path.join(DOWNLOAD_DIR, output_template)
    is_audio_only = quality.startswith("Audio only")

    postprocessors = []
    if is_audio_only:
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": audio_bitrate,
        })
    else:
        postprocessors.append({"key": "FFmpegVideoConvertor", "preferedformat": container_format})

    if add_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_chapters": embed_chapters})
    if embed_thumb:
        postprocessors.append({"key": "EmbedThumbnail"})
    if embed_subs and not is_audio_only and subtitles:
        postprocessors.append({"key": "FFmpegEmbedSubtitle"})
    if sponsorblock_categories:
        postprocessors.append({"key": "SponsorBlock", "categories": sponsorblock_categories})
        postprocessors.append({"key": "ModifyChapters", "remove_sponsor_segments": sponsorblock_categories})

    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "noplaylist": not playlist,
        "writesubtitles": subtitles,
        "writeautomaticsub": subtitles,
        "subtitleslangs": sub_langs if subtitles else [],
        "writethumbnail": embed_thumb,
        "writedescription": write_description,
        "writeinfojson": write_infojson,
        "postprocessors": postprocessors,
        "retries": int(retries) if retries else 10,
        "quiet": not debug_mode,
        "no_warnings": not debug_mode,
        "ignoreerrors": "only_download" if playlist else False,
        "restrictfilenames": False,
        "verbose": debug_mode,
        # Cloud/datacenter IPs often get HTTP 403 from YouTube on the default
        # "web" client. Falling back through android/ios/tv clients (which use
        # different signature logic) fixes this in most cases without cookies.
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "tv", "ios"],
            }
        },
    }
    if logger is not None:
        opts["logger"] = logger

    if proxy:
        opts["proxy"] = proxy
    rl = parse_rate_limit(rate_limit_text)
    if rl:
        opts["ratelimit"] = rl
    if cookies_path:
        opts["cookiefile"] = cookies_path
    if playlist:
        if playlist_start:
            opts["playliststart"] = int(playlist_start)
        if playlist_end:
            opts["playlistend"] = int(playlist_end)
    if clip_start_sec is not None or clip_end_sec is not None:
        # Clip feature temporarily disabled — just skip
        pass
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    return opts


class UILogger:
    """yt-dlp logger jo saari lines ek list me collect karta hai, taaki debug mode me UI me dikhayi ja sakein."""
    def __init__(self):
        self.lines = []
    def debug(self, msg):
        self.lines.append(msg)
    def info(self, msg):
        self.lines.append(msg)
    def warning(self, msg):
        self.lines.append(f"WARNING: {msg}")
    def error(self, msg):
        self.lines.append(f"ERROR: {msg}")


def show_debug_log(logger, debug_mode):
    if debug_mode and logger and logger.lines:
        with st.expander("🐞 Debug log (yt-dlp output)", expanded=False):
            st.code("\n".join(logger.lines), language="text")


def make_progress_hook(progress_bar, status_text):
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                progress_bar.progress(min(downloaded / total, 1.0))
            status_text.text(
                f"⬇️ {d.get('_percent_str', '').strip()} | "
                f"Speed: {d.get('_speed_str', '-').strip()} | "
                f"ETA: {d.get('_eta_str', '-').strip()}"
            )
        elif d["status"] == "finished":
            progress_bar.progress(1.0)
            status_text.text("✅ Download ho gaya, ab processing (convert/embed) ho rahi hai...")
    return hook


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def format_options_ui(key_prefix):
    return st.selectbox(
        "🎚️ Quality",
        ["Best (video+audio)", "1080p", "720p", "480p", "360p", "Audio only"],
        key=f"{key_prefix}_quality",
    )


def advanced_options_ui(key_prefix):
    c1, c2, c3 = st.columns(3)
    with c1:
        subtitles = st.checkbox("📝 Subtitles", key=f"{key_prefix}_subs")
    with c2:
        embed_thumb = st.checkbox("🖼️ Thumbnail embed", key=f"{key_prefix}_thumb")
    with c3:
        add_metadata = st.checkbox("🏷️ Metadata add", value=True, key=f"{key_prefix}_meta")

    sub_langs, embed_subs = [], False
    if subtitles:
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            langs = st.text_input("Subtitle languages (comma-separated codes)", value="en,hi", key=f"{key_prefix}_langs")
            sub_langs = [s.strip() for s in langs.split(",") if s.strip()]
        with sc2:
            embed_subs = st.checkbox("Video me embed karein", key=f"{key_prefix}_embed_subs")
    return subtitles, sub_langs, embed_subs, embed_thumb, add_metadata


def clip_range_ui(key_prefix):
    """Clip feature temporarily disabled due to postprocessor compatibility."""
    st.info(
        "⚠️ **Clip/duration feature is temporarily disabled.** "
        "For now, download the full video and trim locally using: "
        "`ffmpeg -i input.mp4 -ss 00:00:10 -to 00:00:20 -c:v copy -c:a copy output.mp4`"
    )
    return None, None  # Return None for start and end


def more_options_ui(key_prefix, is_audio_only):
    """Container/codec choice, chapters, SponsorBlock, retries, extra metadata files."""
    with st.expander("🧩 More Options (sab settings yahan)"):
        container_format, audio_format, audio_bitrate = "mp4", "mp3", "192"
        mo1, mo2 = st.columns(2)
        if is_audio_only:
            with mo1:
                audio_format = st.selectbox("Audio format", ["mp3", "m4a", "wav", "opus", "vorbis", "flac"], key=f"{key_prefix}_afmt")
            with mo2:
                audio_bitrate = st.selectbox("Audio bitrate (kbps)", ["320", "256", "192", "128", "64"], index=2, key=f"{key_prefix}_abr")
        else:
            with mo1:
                container_format = st.selectbox("Video container", ["mp4", "mkv", "webm"], key=f"{key_prefix}_vfmt")
            with mo2:
                st.checkbox("📑 Chapters embed karein", key=f"{key_prefix}_chapters")

        embed_chapters = st.session_state.get(f"{key_prefix}_chapters", False)

        sb_categories = st.multiselect(
            "🚫 SponsorBlock se hataayein (sponsor/ads segments)",
            ["sponsor", "selfpromo", "intro", "outro", "interaction", "music_offtopic"],
            key=f"{key_prefix}_sponsorblock",
        )

        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            retries = st.number_input("Retries (fail hone par)", min_value=1, max_value=50, value=10, key=f"{key_prefix}_retries")
        with oc2:
            write_description = st.checkbox("📄 Description .txt save karein", key=f"{key_prefix}_desc")
        with oc3:
            write_infojson = st.checkbox("🧾 Info .json save karein", key=f"{key_prefix}_infojson")

        debug_mode = st.checkbox("🐞 Debug mode (poora yt-dlp log dikhaein, agar kuch fail ho raha ho to)", key=f"{key_prefix}_debug")

    return (container_format, audio_format, audio_bitrate, embed_chapters, sb_categories,
            retries, write_description, write_infojson, debug_mode)


# --------------------------------------------------------------------------
# Sidebar — Advanced / global settings
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Advanced Settings")
    output_template = st.text_input("Filename template", value="%(title)s.%(ext)s")
    proxy = st.text_input("Proxy (optional)", placeholder="http://user:pass@host:port")
    rate_limit_text = st.text_input("Speed limit (optional)", placeholder="e.g. 1M or 500K")
    cookies_file = st.file_uploader("Cookies file (optional, .txt — login-required videos ke liye)", type=["txt"])
    st.markdown("---")
    st.caption(f"📁 Download folder: `{DOWNLOAD_DIR}`")
    st.caption("ℹ️ Video convert / thumbnail-subtitle embed ke liye `ffmpeg` installed hona chahiye.")

cookies_path = save_uploaded_cookies(cookies_file)

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📹 Single Video", "📃 Playlist", "📂 Downloaded Files"])

# ---------------- Tab 1: Single video ----------------
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        url = st.text_input("🔗 Video URL paste karein", key="single_url")
        quality = format_options_ui("single")
        subtitles, sub_langs, embed_subs, embed_thumb, add_metadata = advanced_options_ui("single")
        clip_start_sec, clip_end_sec = clip_range_ui("single")
        (container_format, audio_format, audio_bitrate, embed_chapters,
         sb_categories, retries, write_description, write_infojson, debug_mode) = more_options_ui(
            "single", quality.startswith("Audio only")
        )

        if st.button("🔍 Info Fetch Karein", use_container_width=True, key="fetch_single"):
            if not url:
                st.warning("Pehle URL daalein.")
            else:
                with st.spinner("Video ki info la rahe hain..."):
                    try:
                        with youtube_dl.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                            info = ydl.extract_info(url, download=False)
                        st.session_state["video_info"] = info
                        st.session_state["video_url"] = url
                    except Exception as e:
                        st.error(f"Info nahi mil payi: {e}")

    with col2:
        info = st.session_state.get("video_info")
        if info:
            st.markdown('<div class="yt-card">', unsafe_allow_html=True)
            if info.get("thumbnail"):
                st.image(info["thumbnail"], use_container_width=True)
            st.markdown(f"**{info.get('title', '')}**")
            dur = info.get("duration") or 0
            st.caption(f"⏱️ {dur // 60}:{dur % 60:02d}  |  👤 {info.get('uploader', '-')}")
            if info.get("view_count"):
                st.caption(f"👁️ {info['view_count']:,} views")
            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("video_info"):
        if st.button("⬇️ Download Karein", type="primary", use_container_width=True, key="download_single"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            opts = build_ydl_opts(
                quality, subtitles, sub_langs, embed_subs, embed_thumb, add_metadata,
                output_template, proxy, rate_limit_text, cookies_path,
                container_format=container_format, audio_format=audio_format, audio_bitrate=audio_bitrate,
                embed_chapters=embed_chapters, sponsorblock_categories=sb_categories, retries=retries,
                write_description=write_description, write_infojson=write_infojson,
                clip_start_sec=clip_start_sec, clip_end_sec=clip_end_sec, debug_mode=debug_mode,
                logger=(dbg_logger := UILogger()),
                progress_hook=make_progress_hook(progress_bar, status_text),
            )
            try:
                with youtube_dl.YoutubeDL(opts) as ydl:
                    ydl.download([st.session_state["video_url"]])
                status_text.text("🎉 Download poori tarah complete!")
                st.success("Ho gaya! 'Downloaded Files' tab me jaake file uthayein.")
                st.balloons()
            except Exception as e:
                st.error(f"Download fail ho gaya: {e}")
                st.code(traceback.format_exc())
            show_debug_log(dbg_logger, debug_mode)

    st.markdown("---")
    with st.expander("📚 Batch Download — ek se zyada links ek saath"):
        batch_text = st.text_area("Har line me ek URL daalein", height=120, key="batch_urls")
        if st.button("⬇️ Sab Download Karein", use_container_width=True, key="download_batch"):
            urls = [u.strip() for u in batch_text.splitlines() if u.strip()]
            if not urls:
                st.warning("Kam se kam ek URL daalein.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                opts = build_ydl_opts(
                    quality, subtitles, sub_langs, embed_subs, embed_thumb, add_metadata,
                    output_template, proxy, rate_limit_text, cookies_path,
                    container_format=container_format, audio_format=audio_format, audio_bitrate=audio_bitrate,
                    embed_chapters=embed_chapters, sponsorblock_categories=sb_categories, retries=retries,
                    write_description=write_description, write_infojson=write_infojson,
                    clip_start_sec=clip_start_sec, clip_end_sec=clip_end_sec, debug_mode=debug_mode,
                    logger=(dbg_logger := UILogger()),
                    progress_hook=make_progress_hook(progress_bar, status_text),
                )
                try:
                    with youtube_dl.YoutubeDL(opts) as ydl:
                        ydl.download(urls)
                    st.success(f"🎉 {len(urls)} link(s) process ho gaye! 'Downloaded Files' tab check karein.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Batch download me dikkat aayi: {e}")
                    st.code(traceback.format_exc())
                show_debug_log(dbg_logger, debug_mode)

# ---------------- Tab 2: Playlist ----------------
with tab2:
    p_url = st.text_input("🔗 Playlist URL paste karein", key="playlist_url")
    p_quality = format_options_ui("playlist")
    p_subtitles, p_sub_langs, p_embed_subs, p_embed_thumb, p_add_metadata = advanced_options_ui("playlist")
    p_clip_start_sec, p_clip_end_sec = clip_range_ui("playlist")
    st.caption("ℹ️ Clip range set hone par playlist ke har video se yeh time-range hi nikala jayega.")
    (p_container_format, p_audio_format, p_audio_bitrate, p_embed_chapters,
     p_sb_categories, p_retries, p_write_description, p_write_infojson, p_debug_mode) = more_options_ui(
        "playlist", p_quality.startswith("Audio only")
    )

    pc1, pc2 = st.columns(2)
    with pc1:
        p_start = st.number_input("Start index (optional)", min_value=1, value=1, step=1)
    with pc2:
        p_end = st.number_input("End index (0 = end tak)", min_value=0, value=0, step=1)

    if st.button("🔍 Playlist Fetch Karein", use_container_width=True, key="fetch_playlist"):
        if not p_url:
            st.warning("Pehle playlist URL daalein.")
        else:
            with st.spinner("Playlist ki entries la rahe hain..."):
                try:
                    with youtube_dl.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True}) as ydl:
                        pinfo = ydl.extract_info(p_url, download=False)
                    st.session_state["playlist_info"] = pinfo
                    st.session_state["playlist_url"] = p_url
                except Exception as e:
                    st.error(f"Playlist load nahi ho payi: {e}")

    pinfo = st.session_state.get("playlist_info")
    if pinfo and pinfo.get("entries"):
        entries = [e for e in pinfo["entries"] if e]
        st.write(f"**{pinfo.get('title', 'Playlist')}** — {len(entries)} videos mile")
        with st.expander("📋 Videos dekhein", expanded=False):
            for i, e in enumerate(entries[:50], start=1):
                st.write(f"{i}. {e.get('title', 'Untitled')}")
            if len(entries) > 50:
                st.caption(f"...aur {len(entries) - 50} videos")

        if st.button("⬇️ Poori Playlist Download Karein", type="primary", use_container_width=True, key="download_playlist"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            opts = build_ydl_opts(
                p_quality, p_subtitles, p_sub_langs, p_embed_subs, p_embed_thumb, p_add_metadata,
                output_template, proxy, rate_limit_text, cookies_path,
                playlist=True,
                playlist_start=p_start if p_start > 1 else None,
                playlist_end=p_end if p_end > 0 else None,
                container_format=p_container_format, audio_format=p_audio_format, audio_bitrate=p_audio_bitrate,
                embed_chapters=p_embed_chapters, sponsorblock_categories=p_sb_categories, retries=p_retries,
                write_description=p_write_description, write_infojson=p_write_infojson,
                clip_start_sec=p_clip_start_sec, clip_end_sec=p_clip_end_sec, debug_mode=p_debug_mode,
                logger=(dbg_logger := UILogger()),
                progress_hook=make_progress_hook(progress_bar, status_text),
            )
            try:
                with youtube_dl.YoutubeDL(opts) as ydl:
                    ydl.download([st.session_state["playlist_url"]])
                status_text.text("🎉 Playlist download complete!")
                st.success("Ho gaya! 'Downloaded Files' tab me saari files milengi.")
                st.balloons()
            except Exception as e:
                st.error(f"Download fail ho gaya: {e}")
                st.code(traceback.format_exc())
            show_debug_log(dbg_logger, p_debug_mode)

# ---------------- Tab 3: Downloaded files ----------------
with tab3:
    files = sorted(glob.glob(os.path.join(DOWNLOAD_DIR, "*")), key=os.path.getmtime, reverse=True)
    files = [f for f in files if os.path.isfile(f)]

    if not files:
        st.info("Abhi tak koi file download nahi hui. 'Single Video' ya 'Playlist' tab se download karein.")
    else:
        st.write(f"**{len(files)} file(s)** mili `downloads/` folder me")
        for f in files:
            fname = os.path.basename(f)
            fsize = human_size(os.path.getsize(f))
            fmtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d-%b %H:%M")
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.write(f"🎞️ **{fname}**")
                st.caption(f"{fsize} · {fmtime}")
            with c2:
                with open(f, "rb") as fh:
                    st.download_button("⬇️ Download", fh.read(), file_name=fname, key=f"dl_{fname}", use_container_width=True)
            with c3:
                if st.button("🗑️ Delete", key=f"del_{fname}", use_container_width=True):
                    os.remove(f)
                    st.rerun()
