# name_reel_maker.py
# Layout: everything centered on screen, not bottom-heavy

import subprocess
import os
import random
import sys
import logging
import re
import requests

logging.basicConfig(filename="name_reel_debug.log", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = "output_reels"
TEMP_DIR = "name_temp"
VIDEO_W = 1080
VIDEO_H = 1920
FPS = 60
DEFAULT_VIDEO_DURATION = 22

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

GEMINI_API_KEY = "AIzaSyB2my5WTnZURK0TCCBCYmyxUNPk9IntT3g"
GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
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
    prompt = f"""For the name "{name}", research and generate a profile with exactly nine fields.
If a historical field is not certain, provide a creative and culturally appropriate value.

1. Meaning: (A beautiful 4-6 word description)
2. Origin: (Language or culture of origin)
3. Lucky Color: (A vibrant, specific color and why)
4. Lucky Number: (A single auspicious number)
5. Lucky Day: (A significant day for this name)
6. Compatibility: (Three starting letters of compatible names, e.g. 'Best with: A, S, R')
7. Personality: (A positive trait summary, max 8 words)
8. Fact: (A unique or historical fact, max 10 words)
9. Visual: (Describe a high-quality cinematic background scene for this name. No text. 10 words max.)

Format as:
Meaning: [Value]
Origin: [Value]
Lucky Color: [Value]
Lucky Number: [Value]
Lucky Day: [Value]
Compatibility: [Value]
Personality: [Value]
Fact: [Value]
Visual: [Value]

Return ONLY these 9 data lines. Do not use markdown like bolding or lists."""

    for model in GEMINI_MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={"contents":[{"parts":[{"text":prompt}]}],
                      "generationConfig":{"temperature":0.7,"maxOutputTokens":450}},
                timeout=15
            )
            data = r.json()
            if "candidates" in data and data["candidates"]:
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                res = {"meaning":"","origin":"","color":"","num":"","day":"","comp":"","traits":"","fact":"","visual":""}
                
                # Robust parsing considering Line X:, labels, and colons
                for line in raw_text.splitlines():
                    line_clean = re.sub(r"[\\{}'\"*#]", "", line).strip()
                    if ":" in line_clean:
                        parts = line_clean.split(":", 1)
                        tag = parts[0].strip().lower()
                        val = parts[1].strip()
                        
                        # Match tags within the first part
                        if "meaning" in tag: res["meaning"] = val
                        elif "origin" in tag: res["origin"] = val
                        elif "color" in tag: res["color"] = val
                        elif "num" in tag or "number" in tag: res["num"] = val
                        elif "day" in tag: res["day"] = val
                        elif "comp" in tag or "compatibility" in tag: res["comp"] = val
                        elif "person" in tag or "trait" in tag: res["traits"] = val
                        elif "fact" in tag: res["fact"] = val
                        elif "visual" in tag or "scene" in tag: res["visual"] = val
                
                # If essential fields are missing, try a second split level (Gemini sometimes duplicates)
                if not (res["meaning"] and res["origin"]):
                     # Attempt fallback parsing if formatting was weird
                     pass

                if res["meaning"] or res["origin"]:
                    # Fill missing values with proactive defaults
                    if not res["meaning"]: res["meaning"] = "A unique and creative soul"
                    if not res["origin"]:  res["origin"] = "Traditional Origin"
                    if not res["color"]:   res["color"] = "Aura Gold"
                    if not res["num"]:     res["num"] = str(random.randint(1,9))
                    if not res["day"]:     res["day"] = "Friday"
                    if not res["comp"]:    res["comp"] = "Best with: A, S, M"
                    if not res["traits"]:  res["traits"] = "Compassionate, Bold and Intelligent"
                    if not res["fact"]:    res["fact"] = "A name with ancient roots"
                    if not res["visual"]:  res["visual"] = "Ethereal sunrise over mystical mountain peaks"
                    
                    print(f"   [Gemini/{model}] {res['meaning']}")
                    return list(res.values())
        except Exception as e:
            logger.warning(f"{model}: {e}")

    first = name.split()[0].lower()
    m = FALLBACK_MEANINGS.get(first, "Unique and powerful soul")
    return [m, "Ancient Origin", "Emerald Green", "7", "Friday", "A, S, M", "Compassionate and strong", "A name with deep history", "Abstract glowing cosmic nebulae in deep space"]

def generate_ass(name, style, total, data_list, path):
    pc  = style["pc"]
    hc  = style["hc"]
    wc  = style["wc"]
    label = clean(style["label"], 30)
    
    meaning, origin, color, num, day, comp, traits, fact, visual = data_list
    safe_name    = clean(name.upper(), 20)
    safe_meaning = clean(meaning, 55)
    safe_origin  = clean(origin, 35)
    safe_color   = clean(color, 25)
    safe_num     = clean(num, 15)
    safe_day     = clean(day, 20)
    safe_comp    = clean(comp, 35)
    safe_traits  = clean(traits, 60)
    safe_fact    = clean(fact, 60)

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
    # Premium Centered Layout
    Y_LABEL      = 140
    Y_NAME_TYPE  = 960
    Y_NAME_REV   = 280
    
    Y_MEANING    = 440
    Y_ORIGIN     = 580
    Y_LUCKY      = 710
    Y_DAY_COMP   = 840
    
    Y_TRAITS_L   = 1040
    Y_TRAITS_V   = 1120
    Y_FACT_L     = 1260
    Y_FACT_V     = 1340
    
    Y_HOLD       = 1740
    Y_BAR        = 1860

    hook_end      = 3.2
    type_start    = 3.7
    type_end      = type_start + sum(delays)
    content_start = type_end + 0.3
    outro_start   = total - 5.5

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
    ass += f"Dialogue: 1,{t(0)},{t(hook_end)},Title,,0,0,0,,{{\\pos({CX},900)\\fs95\\c{hc[2:]}\\an5\\fad(400,400)\\fscx95\\fscy95\\t(0,2500,\\fscx105\\fscy105)}}COMMENT YOUR NAME\n"
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

    # Reveal - Premium Centered Content
    ass += f"Dialogue: 1,{t(content_start)},{t(outro_start)},Title,,0,0,0,,{{\\pos({CX},{Y_NAME_REV})\\fs{int(nfs*0.75)}\\c{pc[2:]}\\an5\\fad(300,300)}}{safe_name}\n"
    
    # Meaning
    m_fs = 65 if len(safe_meaning) < 20 else 55
    ass += f"Dialogue: 1,{t(content_start+0.4)},{t(outro_start)},Body,,0,0,0,,{{\\pos({CX},{Y_MEANING})\\fs{m_fs}\\c{hc[2:]}\\an5\\fad(500,300)\\i1}}\"{safe_meaning}\"\n"
    
    # Origin
    ass += f"Dialogue: 1,{t(content_start+0.7)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_ORIGIN})\\fs45\\c{pc[2:]}\\an5\\fad(500,300)}}🗺️ {safe_origin}\n"
    
    # Color & Number
    vibe_text = f"Color: {safe_color}  |  Number: {safe_num}"
    ass += f"Dialogue: 1,{t(content_start+1.0)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_LUCKY})\\fs45\\c{hc[2:]}\\an5\\fad(500,300)}}🍀 {vibe_text}\n"
    
    # Day & Compatibility
    day_comp = f"Day: {safe_day}  |  {safe_comp}"
    ass += f"Dialogue: 1,{t(content_start+1.3)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_DAY_COMP})\\fs45\\c{pc[2:]}\\an5\\fad(500,300)}}☀️ {day_comp}\n"
    
    # Traits
    traits_split = [tr.strip() for tr in safe_traits.split(",")]
    bullets = "  •  ".join(traits_split[:3])
    if len(bullets) > 50: bullets = bullets.replace("  •  ", "\\N• ", 1)
    
    ass += f"Dialogue: 1,{t(content_start+1.6)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_TRAITS_L})\\fs42\\c{hc[2:]}\\an5\\fad(500,300)}}✦ PERSONALITY TRAITS ✦\n"
    ass += f"Dialogue: 1,{t(content_start+1.8)},{t(outro_start)},Body,,0,0,0,,{{\\pos({CX},{Y_TRAITS_V})\\fs45\\c{pc[2:]}\\an5\\fad(500,300)}}• {bullets}\n"
    
    # Fact
    wrapped_fact = safe_fact
    if len(safe_fact) > 40:
        mid = len(safe_fact) // 2
        sp = safe_fact.find(" ", mid-10)
        if sp != -1: wrapped_fact = safe_fact[:sp] + "\\N" + safe_fact[sp+1:]
    ass += f"Dialogue: 1,{t(content_start+2.1)},{t(outro_start)},Accent,,0,0,0,,{{\\pos({CX},{Y_FACT_L})\\fs42\\c{hc[2:]}\\an5\\fad(500,300)}}✦ UNIQUE FACT ✦\n"
    ass += f"Dialogue: 1,{t(content_start+2.3)},{t(outro_start)},Body,,0,0,0,,{{\\pos({CX},{Y_FACT_V})\\fs45\\c{pc[2:]}\\an5\\fad(500,300)}}{wrapped_fact}\n"

    # Hold to read
    ass += f"Dialogue: 2,{t(content_start+3.0)},{t(outro_start)},Highlight,,0,0,0,,{{\\pos({CX},{Y_HOLD})\\fs42\\c&H00FFFFFF\\3c&H66000000\\an5\\fad(600,0)}}👉 HOLD TO READ FULL PROFILE\n"

    # Progress bar
    ass += f"Dialogue: 0,{t(content_start)},{t(outro_start)},Base,,0,0,0,,{{\\pos({CX},{Y_BAR})\\p1}}m 0 0 l 840 0 l 840 6 l 0 6{{\\c&HFFFFFF55\\an5}}\n"
    bar_dur = (outro_start - content_start) * 1000
    ass += f"Dialogue: 1,{t(content_start)},{t(outro_start)},Base,,0,0,0,,{{\\pos(120,{Y_BAR})\\p1\\t(0,{bar_dur},\\fscx100)}}m 0 0 l 8 0 l 8 6 l 0 6{{\\fscx0\\c{pc[2:]}\\an4}}\n"

    # Outro
    ass += f"Dialogue: 2,{t(outro_start)},{t(total)},Title,,0,0,0,,{{\\pos({CX},800)\\fs95\\c{pc[2:]}\\an5\\fad(500,0)\\fscx80\\fscy80\\t(0,700,\\fscx100\\fscy100)}}COMMENT YOUR NAME! 👇\n"
    ass += f"Dialogue: 2,{t(outro_start+0.6)},{t(total)},Title,,0,0,0,,{{\\pos({CX},960)\\fs62\\c{hc[2:]}\\an5\\fad(400,0)}}Want yours? Follow @space_gallary 🔔\n"
    ass += f"Dialogue: 2,{t(outro_start+1.2)},{t(total)},Title,,0,0,0,,{{\\pos({CX},1120)\\fs52\\c{pc[2:]}\\an5\\fad(400,0)}}🔔 SAVE THIS REEL 📌\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(ass)
    return path

def get_brand_background(color_vibe, visual_desc):
    v = (color_vibe + " " + visual_desc).lower()
    assets = "brand_assets"
    # Map vibes to assets
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
    total = int(max(22, min(28, 3.7 + typing_time + 8.0 + 5.5)))

    print(f"📖 Getting data for: {name}")
    data_list = fetch_name_data(name)
    meaning, origin, color, num, day, comp, traits, fact, visual = data_list
    print(f"   Meaning : {meaning}")
    print(f"   Origin  : {origin}")
    print(f"   Vibe    : {color} | {num}")
    print(f"   Day/Comp: {day} | {comp}")
    print(f"   Visual  : {visual}")

    ass_path = os.path.join(TEMP_DIR, f"{re.sub(r'[^a-z0-9]','_',name.lower())}.ass")
    font_dir = os.path.dirname(DEFAULT_FONT) if "/" in DEFAULT_FONT else "/usr/share/fonts"
    generate_ass(name, style, total, data_list, ass_path)

    bg_img = get_brand_background(color, visual)
    sub_filter = f"subtitles='{ass_path}':fontsdir='{font_dir}'"
    has_music = music_path is not None and os.path.exists(music_path)

    inputs = []
    if has_music: inputs.append(music_path)
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
            os.remove(ass_path)

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