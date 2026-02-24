# 🎬 Translatarr  
## AI-Powered Subtitle Translator for Kodi  

Translate Any Subtitle → Into Your Language  
Powered by Google Gemini or OpenAI

---

## 🧠 What Is Translatarr?

Translatarr is a background Kodi service that automatically translates subtitles using modern AI models.

Unlike traditional word-by-word translators, it understands:

- Context  
- Slang  
- Emotion  
- Tone  
- Cultural nuance  

Result: subtitles that feel natural and human-written.

---

# 🚀 What’s New

✔ Gemini AND OpenAI support  
✔ Automatic adaptive chunk resizing  
✔ Token usage tracking  
✔ Real cost calculation per movie per model selection  
✔ Translation Style control  
✔ Real-time settings reload (no Kodi restart required)  
✔ Very fast subtitle detection & translation start  

Translation now begins almost immediately after a subtitle appears in your configured folder.

---

# ⚡ Quick Start (3 Steps)

## 1️⃣ Get an API Key

Choose your AI provider:

🔹 Google Gemini  
https://aistudio.google.com/

🔹 OpenAI  
https://platform.openai.com/api-keys

Create an API key and copy it.

---

## 2️⃣ Configure Translatarr

Kodi → Add-ons → Programs → Translatarr → Settings

Set:

- Provider (Gemini or OpenAI)
- API Key
- Model
- Target Language
- Subtitle Folder (IMPORTANT – see below)

---

## 3️⃣ Play a Movie 🎥

1. Start playing a movie.
2. Download subtitles using any Kodi subtitle addon  
   OR manually place an `.srt` file in your configured subtitle folder.

Translatarr will:

- Detect the subtitle automatically
- Translate it
- Save a new file (e.g. `.ro.srt`, `.fr.srt`)
- Activate it instantly

No manual switching required.

---

# 📁 Subtitle Folder (IMPORTANT)

This is the most important setup step.

Translatarr monitors a specific folder and automatically processes any new subtitle that appears there.

If this folder is not configured correctly, translation will not start.

---

## ✅ How To Set It Properly

### Step 1 — Create a Folder

Create a folder anywhere Kodi can access.

Examples:

**Android**
```
/storage/emulated/0/Download/sub
```

**Windows**
```
C:\KodiSubtitles
```

**Linux**
```
/home/username/subtitles
```

The folder must:
- Exist  
- Be writable  
- Be accessible by Kodi  

---

### Step 2 — Configure Kodi (Very Important)

Go to:

Kodi Settings → Player Settings → Subtitles

Set:

- **Subtitle storage location** → `Custom location`
- **Custom subtitle folder** → Select the folder path you created

Both settings must point to the same folder.

This ensures subtitle addons download `.srt` files directly into the monitored folder.

---

### Step 3 — Set It Inside Translatarr

Kodi → Add-ons → Programs → Translatarr → Settings

Set:

📁 Subtitle Folder → Select the SAME folder

Now both:
- Kodi subtitle system  
- Translatarr  

are using the exact same location.

That’s the key.

---

## 📥 How Subtitles Enter the Folder

There are two ways:

### 1️⃣ Automatic (Recommended)

Use a subtitle addon while playing a movie.

The downloaded `.srt` file will appear in the folder → Translatarr detects it immediately → Translation starts.

---

### 2️⃣ Manual

You can manually copy an `.srt` file into the folder.

As soon as the file appears (and matches the playing movie name), translation starts.

---

## 📝 Important Naming Rule

The subtitle file must match the movie filename.

Example:

Movie:
```
The.Dutchman.2025.mkv
```

Subtitle:
```
The.Dutchman.2025.eng.srt
```

Translatarr will generate:
```
The.Dutchman.2025.ro.srt
```

---

# 🎭 Translation Style

Translatarr allows you to control how subtitles are adapted stylistically.

This does NOT affect translation accuracy.  
It controls tone, profanity handling, and dialogue intensity.

Default mode: **Family-Friendly**

---

## 🔹 0 — Family-Friendly (Default)

Clean, neutral, broadcast-safe translation.

- Avoids profanity  
- Replaces strong insults with mild alternatives  
- Keeps dialogue suitable for general audiences  
- Safe for watching with children or family  

Best for:
- Home viewing  
- Family environments  
- General audiences  

---

## 🔹 1 — Natural

Conversational and realistic tone.

- Sounds fluid and natural  
- Avoids overly literal translation  
- Keeps dialogue authentic  
- Balanced realism  

Best for:
- Everyday viewing  
- TV shows  
- Mixed audiences  

---

## 🔹 2 — Gritty / Adult

Raw and unfiltered.

- Preserves profanity  
- Keeps strong insults intact  
- Maintains emotional intensity  
- No softening of harsh dialogue  

Best for:
- Crime dramas  
- Action films  
- Mature content  

---

⚠ Translation Style does not significantly increase cost.  
It only modifies the AI instruction prompt sent to the model.

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

- MovieName.ro.srt  
- MovieName.fr.srt  
- MovieName.es.srt  

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

You can enable one or both.

---

# 💰 Cost Transparency

Translatarr calculates the real API cost per movie based on official token pricing.

You always know exactly what you spend.

---

Example (OpenAI – gpt-4o-mini)

Model: gpt-4o-mini  
Total Tokens: 52,000  
Estimated Cost: $0.0124  

Fast and extremely affordable for full-length movies.

---

Example (Gemini – Gemini 2.0 Flash)

Model: Gemini 2.0 Flash  
Total Tokens: 52,000  
Estimated Cost: $0.0080  

Very cost-efficient and ideal for everyday subtitle translation.

---

Cost depends on:
- Model selected  
- Total tokens used  
- Subtitle length  

Tip:  
For lowest cost per movie, use:
- Gemini 2.0 Flash  
- gpt-4o-mini  

---

# 🛠 Troubleshooting

No translation appears:
- Check API key  
- Check provider selected  
- Verify subtitle folder exists  
- Verify Kodi subtitle location matches Translatarr folder  
- Make sure a video is playing  

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

# ☕ Support the Project

If you enjoy Translatarr and want to support development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/addonniss)

