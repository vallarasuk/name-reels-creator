# audio_utils.py
# Dynamically fetches calm/ambient tracks from YouTube Free Audio Library API
# Filters to avoid dramatic/organ music (per viewer feedback)
# Uses pure FFmpeg for audio processing — no pydub, works on Python 3.14+

import os
import random
import logging
import subprocess
import requests

logger = logging.getLogger(__name__)

API_URL = "https://thibaultjanbeyer.github.io/YouTube-Free-Audio-Library-API/api.json"
TEMP_DIR = "audio_temp"
MAX_TRACKS_TO_TRY = 5
MIN_TRACK_DURATION = 30

# Prefer calm/ambient — avoid dramatic organ music (viewer feedback)
PREFERRED_KEYWORDS = [
    "ambient", "electronic", "calm", "atmospheric", "cinematic",
    "space", "meditation", "soft", "peaceful", "relaxing", "lo-fi", "chill"
]
AVOIDED_KEYWORDS = [
    "organ", "dramatic", "intense", "heavy", "rock", "metal", "choir"
]

def score_track(track):
    name = track.get("name", "").lower()
    genre = track.get("genre", "").lower()
    mood = track.get("mood", "").lower()
    combined = f"{name} {genre} {mood}"
    for avoided in AVOIDED_KEYWORDS:
        if avoided in combined:
            return -1
    return sum(1 for p in PREFERRED_KEYWORDS if p in combined)

_track_cache = None

def fetch_all_tracks():
    global _track_cache
    if _track_cache is not None:
        return _track_cache
    try:
        logger.info("Fetching audio library metadata...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        tracks = response.json().get("all", [])
        logger.info(f"Audio library loaded: {len(tracks)} tracks")
        _track_cache = tracks
        return tracks
    except Exception as e:
        logger.error(f"Failed to fetch audio metadata: {e}")
        return []

def download_track(track):
    os.makedirs(TEMP_DIR, exist_ok=True)
    track_id = track.get("id")
    track_name = track.get("name", "unknown").replace("/", "_").replace(" ", "_")
    if not track_id:
        return None
    try:
        download_url = f"https://drive.google.com/uc?export=download&id={track_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
        for key, value in response.cookies.items():
            if "download_warning" in key:
                confirm_url = download_url + "&confirm=" + value
                response = session.get(confirm_url, stream=True, timeout=60)
                break
        temp_path = os.path.join(TEMP_DIR, f"track_{track_name}.mp3")
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded track: {track_name}")
        return temp_path
    except Exception as e:
        logger.error(f"Failed to download track {track_name}: {e}")
        return None

def get_track_duration(track_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", track_path],
            capture_output=True, text=True, timeout=30
        )
        import json
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception as e:
        logger.error(f"ffprobe failed: {e}")
        return None

def find_best_segment_ffmpeg(track_path, duration_secs):
    try:
        total_duration = get_track_duration(track_path)
        if not total_duration:
            return None
        if total_duration < MIN_TRACK_DURATION or total_duration < duration_secs:
            logger.warning(f"Track too short: {total_duration:.1f}s")
            return None
        step = 10
        best_start = 0
        best_volume = -999
        pos = 0
        while pos + duration_secs <= total_duration:
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", str(pos), "-t", str(min(duration_secs, 30)),
                 "-i", track_path, "-af", "volumedetect", "-f", "null", "/dev/null"],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stderr.splitlines():
                if "mean_volume" in line:
                    try:
                        vol = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                        if vol > best_volume:
                            best_volume = vol
                            best_start = pos
                    except:
                        pass
            pos += step
        logger.info(f"Best segment start: {best_start}s (volume: {best_volume}dB)")
        return best_start
    except Exception as e:
        logger.error(f"Segment analysis failed: {e}")
        return None

def extract_clip(track_path, start_secs, duration_secs, output_path):
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(start_secs), "-t", str(duration_secs),
             "-i", track_path, "-c:a", "libmp3lame", "-q:a", "2", output_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        logger.error(f"Clip extraction failed: {result.stderr[-500:]}")
        return None
    except Exception as e:
        logger.error(f"Extract clip error: {e}")
        return None

def get_background_music(duration_secs):
    os.makedirs(TEMP_DIR, exist_ok=True)
    tracks = fetch_all_tracks()
    if not tracks:
        logger.error("No tracks available from API")
        return None

    # Filter: remove avoided tracks, sort preferred first
    scored = [(score_track(t), t) for t in tracks if score_track(t) >= 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [t for _, t in scored]
    pool = filtered[:100] if len(filtered) >= 100 else filtered
    candidates = random.sample(pool, k=min(MAX_TRACKS_TO_TRY, len(pool)))

    for track in candidates:
        track_name = track.get("name", "unknown")
        genre = track.get("genre", "")
        print(f"🎵 Trying track: {track_name} [{genre}]")
        logger.info(f"Trying track: {track_name} [{genre}]")
        track_path = download_track(track)
        if not track_path:
            continue
        try:
            start_secs = find_best_segment_ffmpeg(track_path, duration_secs)
            if start_secs is None:
                continue
            clip_name = track.get("name", "clip").replace("/", "_").replace(" ", "_")
            clip_path = os.path.join(TEMP_DIR, f"clip_{clip_name}.mp3")
            result = extract_clip(track_path, start_secs, duration_secs, clip_path)
            if result:
                print(f"✅ Music clip ready: {track_name} [{genre}] ({duration_secs:.1f}s)")
                logger.info(f"Clip ready: {clip_path}")
                return clip_path
            else:
                logger.warning(f"Clip extraction failed for {track_name}")
        except Exception as e:
            logger.error(f"Failed processing {track_name}: {e}")
            continue
        finally:
            if os.path.exists(track_path):
                os.remove(track_path)

    print("⚠️  No background music — Reel will be silent")
    logger.error("All track attempts failed")
    return None

def cleanup_audio(clip_path=None):
    if clip_path and os.path.exists(clip_path):
        os.remove(clip_path)
        logger.info(f"Cleaned up: {clip_path}")
    if os.path.exists(TEMP_DIR) and not os.listdir(TEMP_DIR):
        os.rmdir(TEMP_DIR)