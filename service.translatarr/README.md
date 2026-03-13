# 🎬 Translatarr v2.3.12
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

**Result:** subtitles that feel natural and human-written.

---

# 🚀 What’s New (v2.3.12)

✔ SMARTER AUTO MODE
✔ STRONGER MANUAL MODE
✔ REAL-TIME TRANSLATION
✔ GEMINI 2.5 FLASH FAST MODE

Recent updates include:

- Auto mode detects subtitles from next-to-video, Kodi temp folders, A4K temp folders, and Kodi Custom subtitle folder when active
- Auto mode handles generic temp subtitle names and UUID-style filenames more safely
- Manual mode still prioritizes exact video-name matches, but can now fall back to fresh session subtitles in the configured folder
- Translation aborts safely if the subtitle file changes while it is being translated
- Polling runs only during active video playback

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

- Translation Mode (`Auto` or `Manual`)
- Provider (Gemini or OpenAI)
- API Key
- Model
- Source Language
- Target Language
- Subtitle Folder (IMPORTANT for Manual mode – see below)

---

## 3️⃣ Play a Movie 🎥

1. Start playing a movie.  
2. Download subtitles using any Kodi subtitle addon  
   OR manually place an `.srt` file in your configured subtitle folder.

Translatarr will:

- Detect the subtitle automatically in the active mode  
- Translate it  
- Save a new file (e.g. `.ro.srt`, `.fr.srt`)  
- Activate it instantly  

No manual switching required.

---

# 🌍 Language Safety (Simple Explanation)

Translatarr uses international language codes to make sure translations are correct.

You don’t need to understand what ISO means — here’s what matters:

Some languages have multiple code variations.

For example:

Romanian can appear as:
- `ro`
- `ron`
- `rum`

French can appear as:
- `fr`
- `fra`
- `fre`

Italian:
- `it`
- `ita`

Translatarr understands all of these safely.

### What this means for you:

- It correctly detects your source subtitle language  
- It never translates a subtitle twice  
- It never confuses similar language codes  
- It only translates the exact language you selected  

This prevents:

- Wrong language processing  
- Double translations  
- Infinite translation loops  

Both **Source** and **Target** languages must be selected explicitly for maximum accuracy.

---

# 📁 Subtitle Folder (IMPORTANT IN MANUAL MODE)

This is the most important setup step for manual mode.

In Manual mode, Translatarr monitors a specific folder and processes subtitle files that appear there during playback.

If this folder is not configured correctly, translation will not start.

---

## ✅ How To Set It Properly

### Step 1 — Create a Folder

Create a folder anywhere Kodi can access.

Examples:

**Android**
```
/storage/emulated/0/Download/
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

Both settings should point to the same folder for the most reliable Manual mode behavior.

---

### Step 3 — Set It Inside Translatarr

Kodi → Add-ons → Programs → Translatarr → Settings

Set:

📁 Subtitle Folder → Select the SAME folder

Now both:

- Kodi subtitle system  
- Translatarr  

are using the same location.

This matters because some subtitle add-ons save subtitles there using generic temporary names or UUID-like filenames instead of the movie title. Translatarr now handles those cases more safely if the files belong to the current playback session.

---

# 🤖 Auto Mode vs Manual Mode

## Auto Mode

Auto mode looks for subtitles during playback from locations such as:

- next to the video file
- Kodi temp subtitle folders
- A4K temporary subtitle folder
- Kodi Custom subtitle folder when that storage mode is active

It is designed for users who want subtitle add-ons to work normally and have Translatarr react automatically.

## Manual Mode

Manual mode watches only your configured subtitle folder.

Priority order:

- exact video-name matches first
- fresh current-session subtitles in that folder as a fallback

This keeps Manual mode predictable while still supporting subtitle add-ons that save files with generic names.

---

# 🎭 Translation Style

Translation Style controls tone and intensity — not accuracy.

Default mode: **Family-Friendly**

### 🔹 0 — Family-Friendly (Default)

- Avoids profanity  
- Softens strong insults  
- Suitable for general audiences  

### 🔹 1 — Natural

- Conversational  
- Realistic tone  
- Balanced authenticity  

### 🔹 2 — Gritty / Adult

- Preserves profanity  
- Keeps emotional intensity  
- No softening  

⚠ Translation Style does **not significantly increase cost**.  
It only modifies the AI instruction prompt.

---

# ⚙️ Full Configuration Guide

## 🧠 Provider

**Gemini**  
Fast and very cost-effective.

**OpenAI**  
Higher linguistic refinement (especially GPT-4o).

---

## 🤖 Model AI Options

### 🔹 Gemini Models

- **Gemini 2.5 Flash (recommended)**  
  Best default balance of speed, quality, and subtitle nuance.

- **Fast Mode - Gemini 2.5 Flash**  
  Uses Gemini 2.5 Flash with thinking disabled for faster responses.

- **Gemini 2.0 Flash (Legacy)**  
  Older model kept for compatibility with existing saved settings.

- **Gemini 1.5 Flash (Legacy)**  
  Older budget model kept for compatibility with existing saved settings.

---

### 🔹 OpenAI Models

- **gpt-4o-mini (cheap + fast)**  
  Budget-friendly and very fast.

- **gpt-5-mini**  
  Improved nuance while remaining cost-efficient.

- **gpt-4o (premium quality)**  
  Highest refinement and emotional accuracy.

---

## 📦 Dialogue Lines Per Chunk

How many subtitle lines are sent per API request.

Recommended:

- 50  → safer  
- 100 → faster  
- 150 → aggressive  

### Adaptive chunk behavior (v2.0.1)

- Starts with your selected chunk size  
- If the API rejects it, automatically halves the chunk  
- Retries up to 3 times  

Prevents "all chunks rejected" failures — especially useful for free-tier API users.

---

# 💰 Cost Transparency & Smart Token Usage

Translatarr is built to **save you money**.

When translating subtitles, we send to the AI:

✔ ONLY dialogue lines  

We DO NOT send:

✘ Subtitle indexes  
✘ Timestamps  

After translation:

- Timestamps and numbering are rebuilt locally  
- Only translated dialogue is reinserted  

This dramatically reduces:

- Token usage  
- API cost  
- Processing time  

You are paying only for meaningful dialogue — not technical subtitle metadata.

---

## 📊 Real Cost Per Movie

After each translation, Translatarr shows:

- Total tokens used  
- Estimated API cost  
- Model selected  
- Total chunks  
- Processing time  

You always know exactly what you spend.

---

### Example (OpenAI – gpt-4o-mini)

Model: gpt-4o-mini  
Total Tokens: 52,000  
Estimated Cost: $0.0124  

---

### Example (Gemini – Gemini 2.5 Flash)

Model: Gemini 2.5 Flash  
Total Tokens: 52,000  
Estimated Cost: $0.0080  

---

For lowest cost per movie, use:

- Fast Mode - Gemini 2.5 Flash  
- gpt-4o-mini  

Both are extremely affordable for full-length films.

---

# 🛠 Troubleshooting

**No translation appears:**

- Check API key  
- Check provider selected  
- Verify subtitle folder exists  
- Verify Kodi subtitle location matches Translatarr folder  
- Make sure a video is playing  

**Translation stops midway:**

Adaptive chunking retries smaller sizes automatically.  
If still failing:

- Lower chunk size  
- Lower temperature  

**Cost seems high:**

Use:

- Fast Mode - Gemini 2.5 Flash  
- gpt-4o-mini  

---

# ☕ Support the Project

If you enjoy Translatarr and want to support development:

https://www.buymeacoffee.com/addonniss








