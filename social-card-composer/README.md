# Social Card Composer 🎨

**A Universal, AI-Powered Social Media Poster Generator with Twin-Engine Architecture.**

`social-card-composer` is an enterprise-grade agent skill designed to automate the creation of high-aesthetic, professional marketing posters, lookbooks, and e-commerce graphics. By seamlessly combining AI background removal with a dual-rendering engine, it transforms raw user photos into studio-quality social media assets in seconds.

---

## 🌟 Core Features

### 1. Zero-Click AI Background Removal
Integrated directly with `rembg`, the workflow automatically detects subjects (products, portraits) in raw images, strips away the background, and outputs high-resolution transparent PNGs ready for composition.

### 2. Twin-Engine Rendering System
To solve the historic trade-off between text-wrapping limits and complex visual effects, this skill introduces a dual-engine architecture:

*   **Satori Engine (Node.js / SVG / HTML/CSS)** 
    *   **Best for:** Text-heavy layouts, notes, polaroid frames, and structured data.
    *   **Why:** Harnesses the power of web CSS (Flexbox, auto-text-wrapping) to generate crisp typography without manual coordinate calculations.
*   **Pillow Engine (Python / Glassmorphism)**
    *   **Best for:** E-commerce hero sections, 1:1 visual comparisons, and spatial layouts.
    *   **Why:** Enables pixel-perfect graphical manipulation, real-time Drop Shadows, Glassmorphism (毛玻璃) overlays, spatial depth floating effects, and dynamic light glowing mappings.

### 3. Production-Ready Templates
Includes cutting-edge visual paradigms out-of-the-box, such as the **"Spatial Floating Centerpiece"** (often used by top-tier 3C and fashion brands) and clean editorial themes.

---

## 🚀 Installation & Prerequisites

Ensure your environment has the following installed:

```bash
# 1. Node.js (v18+) for Satori
npm i -g @vercel/satori satori-html convert-svg-to-png

# 2. Python 3+ for Pillow
pip3 install Pillow

# 3. AI Background Removal tool
pip3 install rembg[cli]
```

*(Note: If running within an OpenClaw Agent workspace, fonts and core dependencies are auto-fetched upon execution.)*

---

## 💻 CLI Usage Guide

The pipeline follows a Unix-like philosophy: **Extract -> Compose -> Output**.

### Step 1: Extract Subjects (Background Removal)
Pass one or multiple raw images to the removal script.
```bash
bash scripts/remove_bg.sh /path/to/raw_product1.jpg /path/to/raw_product2.jpg
```
*Result: Extracted transparent PNGs are saved to `/tmp/openclaw/social_card_assets/`.*

### Step 2: Render via Target Engine

**Scenario A: Generating a Satori-based Layout (Text-Driven)**
Use the `generate.sh` wrapper, specifying `--engine satori` along with your copy.
```bash
bash scripts/generate.sh --engine satori \
  --img1 "/tmp/openclaw/social_card_assets/raw_product1_transparent.png" \
  --maintitle "电商超级大促" \
  --subtitle "2026.06.23 - 2026.06.30" \
  --box1-title "新人福利" \
  --box1-desc1 "注册即领 2000 积分" \
  --output "/tmp/final_poster.png"
```

**Scenario B: Generating an E-Commerce Spatial Layout (Visual-Driven)**
Invoke the dedicated high-end Python design script. (The script will automatically pick up the transparent PNGs generated in Step 1 and apply glassmorphism and drop-shadows).
```bash
python3 scripts/generate_ecommerce_glassmorphism.py
```
*Result: A highly stylized, perspective-floating JPEG poster.*

---

## 🤖 Usage for AI Agents (Standard Prompts)

If you are a user commanding the Agent, you do not need to write code. Provide the images and directly use natural language:

*   **For E-Commerce / Glossy effects:** 
    > "我这里有一张手机的高清图，帮我抠图并设计一张高奢电商海报（带玻璃悬浮那种），主标题写'年终超级补贴'。"
*   **For Text/Editorial effects:**
    > "把这两张产品做成一张社交媒体分享卡片，排版文字多一些，使用 Satori 引擎，列出这几条核心卖点..."

---

## 📁 Directory Structure
```text
social-card-composer/
├── scripts/
│   ├── remove_bg.sh                        # AI Background Removal wrapper
│   ├── generate.sh                         # Unified entry point & Engine router
│   ├── generate_ecommerce_glassmorphism.py # Pillow engine: Pro E-commerce template
│   └── generate_card_satori.js             # Satori engine: Flexbox templates
├── templates/                              # JSON / layout definitions
├── README.md                               # This document
└── SKILL.md                                # OpenClaw Agent prompt/context directives
```

---
*Built for OpenClaw / UnifAI Network Skills Ecosystem.*
