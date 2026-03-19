# Name Reels Creator (V5 Brand Edition) 🚀

Generate stunning, highly-personalized name reels for social media using Gemini AI and FFmpeg. This project creates high-quality vertical videos (9:16) with rich name data, cinematic effects, and professional brand visuals.

## 🌟 Key Features (V5)

### 1. AI-Powered Personalization
- **9 Rich Data Fields**: Meaning, Origin, Lucky Color, Lucky Number, Lucky Day, Compatibility, Personality Traits, Interesting Fact, and a "Visual Scene description".
- **Intelligent Research**: Uses Google Gemini to research every name and generate a unique profile and "Image Prompt" for the background.
- **Robust Parsing**: Advanced parsing ensures all 9 fields are reliably populated with high-quality descriptions and culturally appropriate fallbacks.

### 2. Professional Brand Visuals
- **Dynamic Background Selection**: Automatically selects between premium backgrounds (**Nature Sky**, **Dark Forest**, **Brush Strokes**) based on the name's vibe and color.
- **Cinematic FFmpeg Filters**:
    - **Shimmer & Grain**: Subtle micro-animations for a high-end feel.
    - **Dynamic Blur**: Background is scaled and blurred for maximum text readability.
    - **Vignette**: Focuses attention on the centered content.
- **Centered Premium Layout**: All text is mathematically centered for a clean, professional social media aesthetic.

### 3. Interactive Engagement
- **"Hold to Read" Prompt**: High-engagement overlay encouraging users to interact with the reel.
- **Animated Typing**: Realistic typing effects for the name reveal.
- **Progressive Disclosure**: Information is revealed sequentially with smooth fade-in transitions.
- **Call-to-Action (Outro)**: Encourages comments, following, and saving the reel.

### 4. Customization & Styles
- **7 Unique Editions**: Golden, Neon Blue, Rose Gold, White Minimal, Purple Galaxy, Fire, and Emerald.
- **Font Support**: Supports "Clicker Script" for titles and "DejaVu Sans" for body text.

---

## 🚀 Getting Started

### Prerequisites
1. **FFmpeg**: Must be installed and available in your PATH.
2. **Python 3.7+**: With `requests` library installed (`pip install requests`).
3. **Gemini API Key**: Get your key from [Google AI Studio](https://aistudio.google.com/).

### Installation
```bash
git clone <your-repo-url>
cd name-reels-creator
# Add your GEMINI_API_KEY to the .env file or environment variables
```

### Usage
Generate a single reel or multiple reels by comma-separating names:

```bash
# Basic usage
python3 main.py "Ranjith"

# Multiple names
python3 main.py "Vallarasu, Ranjith, Priya"

# With background music
python3 main.py "Vallarasu" "audio.mp3"
```

The output reels will be saved in the `output_reels/` directory.

---

## 🛠️ Project Structure
- `main.py`: Entry point for batch processing.
- `name_reel_maker.py`: The core engine for AI data fetching and FFmpeg video generation.
- `brand_assets/`: Premium background images and device mockups.
- `output_reels/`: Generated MP4 files.

## 🎨 V5 Visual Preview
- **Golden Edition**: High-contrast gold text on dark textured backgrounds.
- **Nature Sky**: Soft blue gradients for peaceful, airy names.
- **Dark Forest**: Moody, deep-green and starry night themes for powerful names.

---
**Powered by Gemini AI and FFmpeg**
