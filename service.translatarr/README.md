# 🎬 Translatarr: AI-Powered Subtitle Translator for Kodi

Translate Any Subtitle → Into Your Language  
Powered by Gemini or OpenAI

Translatarr is an intelligent Kodi background service that automatically translates subtitles using modern AI models like Google Gemini and OpenAI GPT-4o.

Unlike traditional word-by-word translators, Translatarr understands:

- Context  
- Slang  
- Emotion  
- Tone  
- Cultural nuance  

Result: subtitles that feel human-written.

---

## 🚀 What’s New

✔ Gemini AND OpenAI support  
✔ Automatic adaptive chunk resizing (Bazarr-style)  
✔ Token usage tracking  
✔ Real cost calculation per movie  
✔ Model selection  
✔ Smart subtitle detection  
✔ Professional line-locking system  

---

# ⚡ Quick Start (3 Steps)

## 1️⃣ Get an API Key

Choose your AI provider:

🔹 Google Gemini  
https://aistudio.google.com/

🔹 OpenAI  
https://platform.openai.com/api-keys

---

## 2️⃣ Configure Translatarr

Kodi → Addons → Services → Translatarr → Settings

- Select Provider (Gemini or OpenAI)
- Paste API Key
- Choose Model
- Choose Target Language

---

## 3️⃣ Play a Movie 🎥

Download any subtitle using any Kodi subtitle addon.

Translatarr will:

- Detect the subtitle
- Translate it automatically
- Save it as .ro.srt, .fr.srt, etc.
- Activate it instantly

No manual steps required.

---

# ⚙️ Full Configuration Guide

## 🧠 Provider

Choose your AI backend:

Gemini  
Fast and very cost-effective.

OpenAI  
Higher linguistic refinement (especially GPT-4o).

---

## 🤖 Model AI Options

### 🔹 Gemini Models

- Gemini 2.0 Flash (recommended)  
  Best overall balance of speed, cost, and subtitle quality. Fast, stable, and ideal for most movies and TV shows.

- Gemini 1.5 Flash  
  Lightweight and reliable model. Slightly older generation, very stable, good for conservative or low-cost usage.

- Gemini 2.5 Flash  
  Newer-generation model with improved contextual understanding and better nuance handling. Slightly more expensive, but stronger with slang and complex dialogue.


### 🔹 OpenAI Models

- gpt-4o-mini (cheap + fast)  
  Budget-friendly and very fast. Great for bulk subtitle translation with solid quality at minimal cost.

- gpt-5-mini  
  Next-generation balanced model. Smarter contextual understanding than 4o-mini, improved nuance and dialogue flow, while remaining cost-efficient.

- gpt-4o (premium quality)  
  Highest refinement and linguistic precision. Best choice for maximum naturalness, emotional tone accuracy, and complex scripts.

---

## 🌍 Source & Target Language

Source:
Use Auto-Detect unless you know the exact language.

Target:
Must be a specific language (not Auto).

Generated files follow ISO codes:
MovieName.ro.srt
MovieName.fr.srt
MovieName.es.srt

---

## 🌡 Temperature

Controls creativity:

0.15  → Accurate & stable (recommended)  
0.5   → Slightly more natural  
0.7+  → More creative / risky  

For subtitles, 0.15 is ideal.

---

## 📦 Lines Per Chunk

How many subtitle lines are sent per API request.

Recommended:
- 50  → safer
- 100 → faster
- 150 → aggressive

Smart Adaptive Mode:
If a chunk fails, Translatarr automatically retries with:

Initial → 50 → 25

No manual retry needed.

---

## 📁 Save Folder

Folder where translated subtitles are written.

Must be writable by Kodi.

---

## 🔔 Notification Modes

Show Statistics:
Displays:
- Model used
- Total tokens
- Estimated cost
- Total chunks
- Lines translated

Simple Notifications:
Minimal progress bar only.

---

# 💰 Cost Transparency

Translatarr calculates real API cost per movie.

Example:

Model: gpt-4o-mini  
Total Tokens: 52,000  
Cost: $0.0124  

This is calculated from official token pricing.

You always know what you spend.

---

# 🛠 How It Works (Technical Overview)

1. Subtitle detected  
2. Parsed into timestamps + text  
3. Text split into chunks  
4. Each chunk is:
   - Line-anchored (L000 format)
   - Strictly validated
   - Scrubbed for artifacts  
5. AI response validated  
6. Written back into new SRT  
7. Activated instantly  

Line count must match exactly or chunk is retried automatically.

---

# 🛠 Troubleshooting

No translation appears:
- Check API key
- Check provider selected
- Verify save folder exists

Translation stops midway:
Adaptive chunking retries smaller sizes automatically.
If still failing:
- Lower chunk size
- Lower temperature

Cost seems high:
Use:
- Gemini 2.0 Flash
- gpt-4o-mini

---

# 🏗 Architecture

service.py  
    ↓  
translator.py  
    ↓  
GeminiTranslator / OpenAITranslator  

Clean provider abstraction.
Single translation core.
Production-safe batching.

---

# ☕ Support the Project

If you enjoy Translatarr and want to support development:

https://www.buymeacoffee.com/addonniss

---
