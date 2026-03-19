# name_reel_maker.py
# Layout: everything centered on screen, not bottom-heavy

import subprocess
import os
import random
import sys
import logging
import re
import requests
import audio_utils

logging.basicConfig(filename="name_reel_debug.log", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = "output_reels"
TEMP_DIR = "name_temp"
VIDEO_W = 1080
VIDEO_H = 1920
FPS = 60
DEFAULT_VIDEO_DURATION = 35

FONT_STYLES = [
    {"name":"golden_dark",    "bg":"0x0a0800", "pc":"&H0000AAFF", "hc":"&H0000CCFF", "wc":"&H880000AA", "label":"Golden Edition"},
    {"name":"neon_blue_dark", "bg":"0x050510", "pc":"&H00FFEE00", "hc":"&H00FF8800", "wc":"&H88FFEE00", "label":"Neon Edition"},
    {"name":"rose_gold_dark", "bg":"0x0d0508", "pc":"&H00C1B6FF", "hc":"&H00C1B6FF", "wc":"&H88C1B6FF", "label":"Rose Gold Edition"},
    {"name":"white_minimal",  "bg":"white",    "pc":"&H00000000", "hc":"&H00333333", "wc":"&H88000000", "label":"Classic Edition"},
    {"name":"purple_galaxy",  "bg":"0x07010d", "pc":"&H00D670DA", "hc":"&H00D670DA", "wc":"&H88D670DA", "label":"Galaxy Edition"},
    {"name":"fire_dark",      "bg":"0x0d0200", "pc":"&H000066FF", "hc":"&H000088FF", "wc":"&H880066FF", "label":"Fire Edition"},
    {"name":"emerald_dark",   "bg":"0x010d04", "pc":"&H007FFF00", "hc":"&H007FFF00", "wc":"&H887FFF00", "label":"Emerald Edition"},
]

FALLBACK_MEANINGS = {
    "priya":"Beloved one","arjun":"Bright and shining","sneha":"Love and affection",
    "karthik":"Son of the stars","divya":"Divine and heavenly","rahul":"Efficient",
    "ananya":"One of a kind","vikram":"Brave and valiant","pooja":"Prayer and worship",
    "arun":"Dawn, red sky","kavya":"Poem, literature","ravi":"Sun, radiance",
    "deepa":"Light, lamp","sanjay":"Victorious","meera":"Prosperous",
    "raj":"King, ruler","nisha":"Night","amit":"Infinite, boundless",
    "vijay":"Victory","lakshmi":"Goddess of wealth","krishna":"All-attractive",
    "suresh":"Ruler of gods","usha":"Dawn, morning","vallarasu":"King of strength",
    "anand":"Joy and bliss","maya":"Illusion, magic","dev":"God, divine",
    "rohit":"Red, sun","neha":"Love, rain","abhishek":"Anointed one",
    "aishwarya":"Prosperity","aarav":"Peaceful","ishaan":"Sun, lord shiva",
    "akash":"Sky","surya":"Sun","chandra":"Moon","geetha":"Song, hymn",
    "bharath":"Descendant of bharata","vignesh":"Lord of wisdom",
    "prasad":"Divine blessing","ganesh":"Lord of beginnings",
    "harish":"Lord vishnu","ramesh":"Lord rama","mahesh":"Great lord shiva",
    "dinesh":"Sun god","rajesh":"King of kings","kavin":"Handsome",
    "naveen":"New, fresh","vivek":"Wisdom, intellect","santhosh":"Happiness",
    "prakash":"Light, brightness","keerthana":"Song of praise",
    "lavanya":"Grace, beauty","nandhini":"Joyful","dharani":"Earth",
    "pavithra":"Pure, holy","kamala":"Lotus flower","gowri":"Goddess parvathi",
    "senthil":"Young lord murugan","vinoth":"Skillful","ashwin":"Horse tamer",
}

GEMINI_API_KEY = "AIzaSyAixrlIysLeoA7T26_HgB52hinocVGwkgU"
GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]

def get_font_path():
    for p in [
        os.path.expanduser("~/.local/share/fonts/google-fonts/ofl/clickerscript/ClickerScript-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(p): return p
    return "sans"

DEFAULT_FONT = get_font_path()

def clean(text, maxl=50):
    text = str(text)
    # Remove common Gemini artifacts
    text = re.sub(r"[*#_~`\[\]]", "", text)
    return text[:maxl].strip()

def fetch_name_data(name):
    api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
    prompt = f"""For the name "{name}", research and generate a deep profile with exactly ten fields.
Provide profound, clear, and culturally significant insights.

1. Essence: (A deep, poetic 4-6 word description of the name's meaning)
2. Legacy: (The historical or cultural root of the name)
3. Aura: (A specific color and the 'vibration' or 'energy' it radiates)
4. Destiny: (The primary life purpose or destiny associated with this name)
5. Strength: (The most powerful character trait or 'superpower')
6. Life Path: (A short sentence on what this person is meant to achieve)
7. Compatible: (Three names or starting letters that resonate with this aura)
8. Element: (The natural element or spirit animal associated with this vibe)
9. Sacred Fact: (A unique historical, spiritual, or linguistic fact)
10. Grand Vision: (A profound spiritual or personality breakdown, 40-50 words. Clear and deep!)

Format as:
Essence: [Value]
Legacy: [Value]
Aura: [Value]
Destiny: [Value]
Strength: [Value]
Life Path: [Value]
Compatible: [Value]
Element: [Value]
Sacred Fact: [Value]
Grand Vision: [Value]

Return ONLY these 10 data lines. Do not use markdown like bolding or lists."""

    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={"contents":[{"parts":[{"text":prompt}]}],
                      "generationConfig":{"temperature":0.7,"maxOutputTokens":1024}},
                timeout=15
            )
            data = r.json()
            # LOG raw Gemini result
            logger.info(f"Gemini raw response for {name}:\n{data}")
            
            if "candidates" in data and data["candidates"]:
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                res = {"essence":"","legacy":"","aura":"","destiny":"","strength":"","path":"","comp":"","element":"","fact":"","vision":""}
                
                for line in raw_text.splitlines():
                    line_clean = re.sub(r"[\\{}'\"*#]", "", line).strip()
                    if ":" in line_clean:
                        parts = line_clean.split(":", 1)
                        tag = parts[0].strip().lower()
                        val = parts[1].strip()
                        
                        if "essence" in tag or "meaning" in tag: res["essence"] = val
                        elif "legacy" in tag or "origin" in tag: res["legacy"] = val
                        elif "aura" in tag or "color" in tag: res["aura"] = val
                        elif "destiny" in tag: res["destiny"] = val
                        elif "strength" in tag: res["strength"] = val
                        elif "life path" in tag or "path" in tag: res["path"] = val
                        elif "comp" in tag: res["comp"] = val
                        elif "element" in tag: res["element"] = val
                        elif "fact" in tag: res["fact"] = val
                        elif "vision" in tag or "deep" in tag: res["vision"] = val

                if res["essence"] or res["vision"]:
                    # Fill missing values with proactive defaults
                    if not res["essence"]: res["essence"] = "A unique and creative soul"
                    if not res["legacy"]:  res["legacy"] = "Ancient Wisdom"
                    if not res["aura"]:    res["aura"] = "Aura Gold | High Frequency"
                    if not res["destiny"]: res["destiny"] = "Success and Harmony"
                    if not res["strength"]: res["strength"] = "Unwavering Courage"
                    if not res["path"]:    res["path"] = "Leading others toward light"
                    if not res["comp"]:    res["comp"] = "A, S, M"
                    if not res["element"]: res["element"] = "Golden Light"
                    if not res["fact"]:    res["fact"] = "A name with timeless roots"
                    if not res["vision"]:  res["vision"] = f"The name {name} carries a vibration of infinite possibility and deep spiritual connection, resonating with those who seek truth and harmony in their surroundings."
                    
                    # LOG parsed profile
                    logger.info(f"Parsed profile for {name}: {res}")
                    print(f"   [Gemini/{model}] {res['essence']}")
                    return list(res.values())
        except Exception as e:
            logger.warning(f"{model}: {e}")

    first = name.split()[0].lower()
    m = FALLBACK_MEANINGS.get(first, "Unique and powerful soul")
    fallback_data = [m, "Ancient Roots", "Emerald Glow | Peace", "Inner Balance", "Compassion", "Spreading kindness and wisdom", "A, S, M", "White Dove", "A name with deep history", "A soul that radiates kindness and wisdom, deeply rooted in traditions while embracing modern innovation with grace and strength."]
    logger.info(f"Using fallback data for {name}: {fallback_data}")
    return fallback_data

def generate_ass(name, style, total, data_list, path):
    pc  = style["pc"]
    hc  = style["hc"]
    wc  = style["wc"]
    label = clean(style["label"], 30)
    
    essence, legacy, aura, destiny, strength, life_path, comp, element, fact, vision = data_list
    safe_name    = clean(name.upper(), 20)
    safe_essence = clean(essence, 55)
    safe_legacy  = clean(legacy, 35)
    safe_aura    = clean(aura, 35)
    safe_destiny = clean(destiny, 35)
    safe_strength= clean(strength, 35)
    safe_path    = clean(life_path, 60)
    safe_comp    = clean(comp, 35)
    safe_element = clean(element, 35)
    safe_fact    = clean(fact, 60)
    safe_vision  = clean(vision, 350)

    title_font = "DejaVu Sans Bold"
    if "Clicker" in DEFAULT_FONT: title_font = "Clicker Script"
    body_font = "DejaVu Sans"
    accent_font = "DejaVu Sans Bold"

    n = len(safe_name)
    if n <= 4:    nfs = 240
    elif n <= 6:  nfs = 210
    elif n <= 8:  nfs = 180
    elif n <= 10: nfs = 155
    elif n <= 13: nfs = 125
    else:         nfs = 100

    delays = []
    for i, ch in enumerate(safe_name):
        if ch == " ":  delays.append(0.2)
        elif i == 0:   delays.append(1.8)
        elif i == 1:   delays.append(0.8)
        else:          delays.append(0.3)

    CX = 540
    # Slide Positions
    Y_LABEL      = 140
    Y_NAME_TYPE  = 960
    
    # Common layout
    Y_TIT        = 280
    Y_L1         = 480
    Y_V1         = 560
    Y_L2         = 720
    Y_V2         = 800
    Y_L3         = 960
    Y_V3         = 1040
    Y_L4         = 1200
    Y_V4         = 1280

    Y_VISION_L   = 500
    Y_VISION_V   = 760
    
    Y_HOLD       = 1740
    Y_BAR        = 1860

    hook_end      = 3.2
    type_start    = 3.7
    type_end      = type_start + sum(delays)
    content_start = type_end + 0.3
    
    # Timing
    available_content_time = total - content_start - 5.5
    slide_dur = available_content_time / 4.0
    
    s1_end = content_start + slide_dur
    s2_end = s1_end + slide_dur
    s3_end = s2_end + slide_dur
    vision_start = s3_end
    vision_end   = total - 5.5
    outro_start  = vision_end

    def t(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02}:{s:05.2f}"

    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_W}
PlayResY: {VIDEO_H}
WrapStyle: 0

[v4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{title_font},60,{pc},&H00000000,&H00000000,&H66000000,1,0,0,0,100,100,2,0,1,2,2,5,60,60,0,1
Style: Body,{body_font},45,{hc},&H00000000,&H00000000,&H66000000,1,0,0,0,100,100,1,0,1,1,2,5,100,100,0,1
Style: DeepBody,{body_font},45,{hc},&H00000000,&H00000000,&H33000000,1,0,0,0,100,100,1,0,1,1,1,5,100,100,150,1
Style: Accent,{accent_font},48,{pc},&H00000000,&H00000000,&H66000000,1,0,0,0,100,100,2,0,1,1,1,5,100,100,0,1
Style: Highlight,DejaVu Sans,45,&H00FFFFFF,&H00000000,&H00000000,&H00000000,1,0,0,0,100,100,1,0,1,1,0,5,80,80,0,1
Style: Base,DejaVu Sans,10,&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Watermark
    ass += f"Dialogue: 0,{t(0)},{t(total)},Body,,0,0,0,,{{\\pos(1040,75)\\fs32\\c{hc[2:]}AA\\an3}}@space_gallary\n"

    # Edition label
    ass += f"Dialogue: 0,{t(0)},{t(hook_end)},Title,,0,0,0,,{{\\pos({CX},{Y_LABEL})\\fs45\\c{pc[2:]}\\an5\\fad(300,300)}}{label}\n"

    # Hook
    ass += f"Dialogue: 1,{t(0)},{t(hook_end)},Title,,0,0,0,,{{\\pos({CX},900)\\fs95\\c{hc[2:]}\\an5\\fad(400,400)}}COMMENT YOUR NAME\n"
    ass += f"Dialogue: 1,{t(0)},{t(hook_end)},Title,,0,0,0,,{{\\pos({CX},1050)\\fs82\\c{hc[2:]}\\an5\\fad(600,400)}}TO GET YOURS! 🚀\n"

    # Name Typing
    cur = type_start
    for i in range(len(safe_name)):
        ls = cur
        d = delays[i]
        shown = safe_name[:i+1]
        end = ls + d if i < len(safe_name)-1 else content_start
        cur += d
        cursor = "|" if i < len(safe_name)-1 else ""
        ass += f"Dialogue: 1,{t(ls)},{t(end)},Title,,0,0,0,,{{\\pos({CX},{Y_NAME_TYPE})\\fs{nfs}\\c{pc[2:]}\\an5}}{shown}{cursor}\n"

    # SLIDE 1: THE ESSENCE
    ass += f"Dialogue: 1,{t(content_start)},{t(s1_end)},Title,,0,0,0,,{{\\pos({CX},{Y_TIT})\\fs{int(nfs*0.75)}\\c{pc[2:]}\\an5\\fad(300,300)}}{safe_name}\n"
    ass += f"Dialogue: 1,{t(content_start+0.4)},{t(s1_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L1})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}✨ THE CORE ESSENCE\n"
    ass += f"Dialogue: 1,{t(content_start+0.6)},{t(s1_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V1})\\fs52\\c{hc[2:]}\\an5\\fad(500,300)\\i1}}\"{safe_essence}\"\n"
    ass += f"Dialogue: 1,{t(content_start+0.9)},{t(s1_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L2})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}🗺️ ROOT LEGACY\n"
    ass += f"Dialogue: 1,{t(content_start+1.1)},{t(s1_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V2})\\fs48\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_legacy}\n"
    ass += f"Dialogue: 1,{t(content_start+1.4)},{t(s1_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L3})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}🔮 SOUL AURA\n"
    ass += f"Dialogue: 1,{t(content_start+1.6)},{t(s1_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V3})\\fs48\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_aura}\n"
    ass += f"Dialogue: 1,{t(content_start+1.9)},{t(s1_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L4})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}💎 RESONATES WITH\n"
    ass += f"Dialogue: 1,{t(content_start+2.1)},{t(s1_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V4})\\fs48\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_comp}\n"

    # SLIDE 2: HIDDEN POWERS
    ass += f"Dialogue: 1,{t(s1_end)},{t(s2_end)},Title,,0,0,0,,{{\\pos({CX},{Y_TIT})\\fs{int(nfs*0.75)}\\c{pc[2:]}\\an5\\fad(300,300)}}{safe_name}\n"
    ass += f"Dialogue: 1,{t(s1_end+0.4)},{t(s2_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L1})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}⚡ INNER STRENGTH\n"
    ass += f"Dialogue: 1,{t(s1_end+0.6)},{t(s2_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V1})\\fs52\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_strength}\n"
    ass += f"Dialogue: 1,{t(s1_end+0.9)},{t(s2_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L2})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}🎯 DESTINY\n"
    ass += f"Dialogue: 1,{t(s1_end+1.1)},{t(s2_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V2})\\fs48\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_destiny}\n"
    ass += f"Dialogue: 1,{t(s1_end+1.4)},{t(s2_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L3})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}🚀 LIFE PATH\n"
    ass += f"Dialogue: 1,{t(s1_end+1.6)},{t(s2_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V3})\\fs45\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_path}\n"

    # SLIDE 3: SACRED ELEMENTS
    ass += f"Dialogue: 1,{t(s2_end)},{t(s3_end)},Title,,0,0,0,,{{\\pos({CX},{Y_TIT})\\fs{int(nfs*0.75)}\\c{pc[2:]}\\an5\\fad(300,300)}}{safe_name}\n"
    ass += f"Dialogue: 1,{t(s2_end+0.4)},{t(s3_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L1})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}🌿 SPIRIT ELEMENT\n"
    ass += f"Dialogue: 1,{t(s2_end+0.6)},{t(s3_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V1})\\fs52\\c{hc[2:]}\\an5\\fad(500,300)}}{safe_element}\n"
    ass += f"Dialogue: 1,{t(s2_end+0.9)},{t(s3_end)},Accent,,0,0,0,,{{\\pos({CX},{Y_L2})\\fs35\\c{pc[2:]}\\an5\\fad(500,300)}}📚 SACRED FACT\n"
    
    # Wrap sacred fact
    wrapped_fact = ""
    f_words = safe_fact.split()
    f_line = 0
    for w in f_words:
        if f_line + len(w) > 35:
            wrapped_fact += "\\N"
            f_line = 0
        wrapped_fact += w + " "
        f_line += len(w) + 1

    ass += f"Dialogue: 1,{t(s2_end+1.1)},{t(s3_end)},Body,,0,0,0,,{{\\pos({CX},{Y_V2})\\fs45\\c{hc[2:]}\\an5\\fad(500,300)}}{wrapped_fact}\n"

    # GRAND VISION SLIDE
    ass += f"Dialogue: 1,{t(vision_start)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_VISION_L})\\fs65\\c{pc[2:]}\\an5\\fad(500,500)}}💫 GRAND VISION\n"
    
    # Wrap vision
    wrapped_vision = ""
    v_words = safe_vision.split()
    v_line = 0
    for w in v_words:
        if v_line + len(w) > 32:
            wrapped_vision += "\\N"
            v_line = 0
        wrapped_vision += w + " "
        v_line += len(w) + 1

    ass += f"Dialogue: 1,{t(vision_start+0.5)},{t(outro_start)},DeepBody,,0,0,0,,{{\\pos({CX},{Y_VISION_V})\\fs50\\c{hc[2:]}\\an5\\fad(800,500)}}{wrapped_vision}\n"

    # Hold to read
    ass += f"Dialogue: 2,{t(content_start+2.5)},{t(outro_start)},Highlight,,0,0,0,,{{\\pos({CX},{Y_HOLD})\\fs42\\c&H00FFFFFF\\3c&H66000000\\an5\\fad(600,0)}}👉 {name.upper()} SOUL REVEALED\n"

    # Progress bar
    bar_start = content_start
    bar_end   = vision_end
    ass += f"Dialogue: 0,{t(bar_start)},{t(bar_end)},Base,,0,0,0,,{{\\pos({CX},{Y_BAR})\\p1}}m 0 0 l 840 0 l 840 6 l 0 6{{\\c&HFFFFFF55\\an5}}\n"
    bar_dur = (bar_end - bar_start) * 1000
    ass += f"Dialogue: 1,{t(bar_start)},{t(bar_end)},Base,,0,0,0,,{{\\pos(120,{Y_BAR})\\p1\\t(0,{bar_dur},\\fscx100)}}m 0 0 l 8 0 l 8 6 l 0 6{{\\fscx0\\c{pc[2:]}\\an4}}\n"

    # Outro
    ass += f"Dialogue: 2,{t(outro_start)},{t(total)},Title,,0,0,0,,{{\\pos({CX},800)\\fs95\\c{pc[2:]}\\an5\\fad(500,0)}}COMMENT YOUR NAME! 👇\n"
    ass += f"Dialogue: 2,{t(outro_start+0.6)},{t(total)},Title,,0,0,0,,{{\\pos({CX},960)\\fs72\\c{hc[2:]}\\an5\\fad(400,0)}}Follow @space_gallary for your reveal 🔔\n"
    ass += f"Dialogue: 2,{t(outro_start+1.2)},{t(total)},Title,,0,0,0,,{{\\pos({CX},1120)\\fs52\\c{pc[2:]}\\an5\\fad(400,0)}}📌 SAVE THIS REEL\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(ass)
    return path

def get_brand_background(color_vibe, visual_desc):
    v = (color_vibe + " " + visual_desc).lower()
    assets = "brand_assets"
    if any(x in v for x in ["gold", "dark", "night", "power", "forest", "black"]):
        path = os.path.join(assets, "dark_forest.png")
    elif any(x in v for x in ["sky", "blue", "peace", "nature", "cloud", "day"]):
        path = os.path.join(assets, "nature_sky.png")
    else:
        path = os.path.join(assets, "brush_strokes.png")
    
    if os.path.exists(path): return path
    return None

def build_name_reel(name, style, music_path, output_path):
    os.makedirs(TEMP_DIR, exist_ok=True)
    bg_color = style["bg"]
    n = len(name)
    typing_time = 1.8 + 0.8 + max(0, n-2) * 0.3
    # Calculate required time: Intro(3.7 + typing) + 3 Slides(6.5 each) + Vision(7.5) + Outro(5.5)
    required_time = 3.7 + typing_time + (3 * 6.5) + 7.5 + 5.5
    total = int(max(DEFAULT_VIDEO_DURATION, min(45, required_time)))

    print(f"📖 Getting data for: {name}")
    data_list = fetch_name_data(name)
    essence, legacy, aura, destiny, strength, life_path, comp, element, fact, vision = data_list
    print(f"   Essence : {essence}")
    print(f"   Vision  : {vision[:50]}...")

    ass_path = os.path.abspath(os.path.join(TEMP_DIR, f"{re.sub(r'[^a-z0-9]','_',name.lower())}.ass"))
    font_dir = os.path.dirname(DEFAULT_FONT) if "/" in DEFAULT_FONT else "/usr/share/fonts"
    generate_ass(name, style, total, data_list, ass_path)

    bg_img = get_brand_background(aura, vision)
    # Escape path for FFmpeg filter: replace ":" with "\:" and "'" with "\'"
    escaped_ass_path = ass_path.replace(":", "\\:").replace("'", "'\\\\''")
    sub_filter = f"subtitles='{escaped_ass_path}':fontsdir='{font_dir}'"
    
    # Auto-fetch music if not provided
    temp_music = None
    if music_path is None or not os.path.exists(music_path):
        print(f"🎵 Fetching background music for {total}s...")
        temp_music = audio_utils.get_background_music(total)
        final_music = temp_music
    else:
        final_music = music_path

    has_music = final_music is not None and os.path.exists(final_music)

    inputs = []
    if has_music: inputs.append(final_music)
    if bg_img:    inputs.append(bg_img)
    
    bg_idx = 1 if (has_music and bg_img) else 0 if bg_img else -1
    music_idx = 0 if has_music else -1

    filter_parts = []
    if bg_img:
        filter_parts.append(f"[{bg_idx}:v]scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=increase,crop={VIDEO_W}:{VIDEO_H},boxblur=15:5[bgbase]")
    else:
        filter_parts.append(f"color=c={bg_color}:s={VIDEO_W}x{VIDEO_H}:r={FPS}:d={total}[bgbase]")

    filter_parts.extend([
        f"[bgbase]split[v1][v2]",
        f"[v1]geq=r='if(gt(random(1)*random(2),0.9997),200,0)':g='if(gt(random(3)*random(4),0.9997),200,0)':b='if(gt(random(5)*random(6),0.9997),200,0)':a=255[grain]",
        f"[v2][grain]blend=all_mode='addition':all_opacity=0.25[shimmer]",
        f"[shimmer]vignette=angle=0.4[vignetted]",
        f"[vignetted]{sub_filter}[vout]"
    ])

    if has_music:
        fo = max(0, total-2)
        filter_parts.append(f"[{music_idx}:a]atrim=0:{total:.2f},volume=0.4,afade=t=in:st=0:d=1.5,afade=t=out:st={fo:.2f}:d=2[aout]")

    cmd = ["ffmpeg", "-y"]
    for inp in inputs: cmd += ["-i", inp]
    cmd += ["-filter_complex", ";".join(filter_parts), "-map", "[vout]"]
    if has_music: cmd += ["-map", "[aout]"]
    cmd += ["-t", str(total), "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if has_music: cmd += ["-c:a", "aac", "-b:a", "128k"]
    cmd.append(output_path)

    print(f"🎬 Building: {name} [{style['name']}] ({total}s)")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path)/(1024*1024)
            print(f"✅ Done: {output_path} ({size_mb:.1f} MB)")
            return output_path
        else:
            print(f"❌ FFmpeg Error:\n{result.stderr[-600:]}")
            return None
    except Exception as e:
        logger.error(f"FFmpeg Exception: {e}")
        return None
    finally:
        if os.path.exists(ass_path):
            try:
                os.remove(ass_path)
            except:
                pass
        if temp_music and os.path.exists(temp_music):
            audio_utils.cleanup_audio(temp_music)

def create_name_reel(name, style_index=None, music_path=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    style = FONT_STYLES[style_index % len(FONT_STYLES)] if style_index is not None else random.choice(FONT_STYLES)
    safe_fn = re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))
    output_path = os.path.join(OUTPUT_DIR, f"{safe_fn}_{style['name']}.mp4")
    print(f"\n{'='*50}\n🎨 {name} | {style['name']}\n{'='*50}")
    return build_name_reel(name, style, music_path, output_path)

def create_multiple_reels(names, music_path=None):
    results = []
    for i, name in enumerate(names):
        path = create_name_reel(name, style_index=i, music_path=music_path)
        if path: results.append((name, path))
    return results

def cleanup_temp():
    import shutil
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 name_reel_maker.py 'Vallarasu'")
        sys.exit(1)
    names = [n.strip() for n in sys.argv[1].split(",") if n.strip()]
    music = sys.argv[2] if len(sys.argv) > 2 else None
    for name, path in create_multiple_reels(names, music):
        print(f"✅ {name} → {path}")