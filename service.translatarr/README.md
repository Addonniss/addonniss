# 🎬 Translatarr v2.3.0
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

# 🚀 What’s New (v2.3.0)

✔ AUTO MODE
✔ REAL-TIME TRANSLATION

Translations are now safer, smarter, and protected against duplicates, unwanted overwrites, and unnecessary API usage — while allowing you to download and switch subtitles freely during playback.

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
- Source Language
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

- **Gemini 2.0 Flash (recommended)**  
  Best balance of speed, cost, and subtitle quality.

- **Gemini 1.5 Flash**  
  Stable and budget-friendly.

- **Gemini 2.5 Flash**  
  Stronger contextual understanding and nuance.

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

### Example (Gemini – Gemini 2.0 Flash)

Model: Gemini 2.0 Flash  
Total Tokens: 52,000  
Estimated Cost: $0.0080  

---

For lowest cost per movie, use:

- Gemini 2.0 Flash  
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

- Gemini 2.0 Flash  
- gpt-4o-mini  

---

# ☕ Support the Project

If you enjoy Translatarr and want to support development:

https://www.buymeacoffee.com/addonniss






