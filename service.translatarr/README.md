# 🎬 Translatarr v2.4.7
## AI-Powered Subtitle Translator for Kodi  

Translate Any Subtitle → Into Your Language  
Powered by Google Gemini, OpenAI, DeepL Free machine translation, or LibreTranslate  

---

# 🚀 What’s New (v2.4.7)

✔ SMB PATH SUPPORT FOR EXTRACTION OF EMBEDDED SUBTITLES
✔ LONGER TIMEOUTS FOR SLOW NETWORK-BASED EXTRACTION

Latest updates include:

- Expanded the embedded subtitle documentation with more realistic SMB / UNC expectations and practical performance notes from real network tests
- Improved embedded subtitle extraction logging so Manual mode now shows resolved extraction paths, active tool steps, and explicit timeout failures instead of looking stuck
- Added longer extraction timeouts for slow UNC / SMB-backed files so network-based extraction has more time to complete before the add-on gives up

- Embedded subtitle extraction remains best on local files, but Windows UNC-backed playback paths may still work depending on share access and network performance

---

**Previous v2.4.6 highlights** include:

- Added optional embedded subtitle extraction in Manual mode for local MKV files when no external source subtitle is found yet
- Embedded extraction now looks for the selected source-language subtitle track, prefers non-SDH tracks when available, and writes a standard source `.srt` into your configured manual subtitle folder
- Fixed Manual mode so a pre-existing source subtitle can still be translated when no matching translated target subtitle exists yet
- Preserved protection against stale files by skipping old manual source subtitles only when a matching translated target for the current video already exists

**Previous highlights**:

- LibreTranslate support for self-hosted offline or home-network translation
- DeepL Free machine translation support with provider-aware language selection
- Live translation remains always enabled for faster playback
- Added optional Dual-Language Display so users can show the original subtitle on the first line and the translated subtitle below it
- Added optional SDH/HI cue removal while preserving spoken dialogue
- Renamed settings groups to **Mode**, **Provider**, **Translation**, and **Advanced**

---

# ⚡ Quick Start (3 Steps)

## 1️⃣ Get an API Key

Choose your AI provider:

🔹 Google Gemini  
https://aistudio.google.com/

🔹 OpenAI  
https://platform.openai.com/api-keys

🔹 DeepL Free  
https://www.deepl.com/pro-api

🔹 LibreTranslate  
https://libretranslate.com/

Create an API key if your provider needs one and copy it.

---

## 2️⃣ Choose AI Models and Machine Translation Options

### 🧠 Provider Overview

**Gemini**  
Fast and very cost-effective.

**OpenAI**  
Higher linguistic refinement (especially GPT-4o).

**DeepL Free**  
Very fast machine translation with a provider-limited language list.  
The Free tier includes 500,000 characters per month, which is enough for roughly 9 full movies on average.

**LibreTranslate**  
Free self-hosted translation for offline or home-network setups.  
Good for users who want local control, better privacy, and no paid cloud dependency.

---

### 🤖 AI Models

#### 🔹 Gemini Models

- **Gemini 2.5 Flash (recommended)**  
  Best default balance of speed, quality, and subtitle nuance.

- **Fast Mode - Gemini 2.5 Flash**  
  Uses Gemini 2.5 Flash with thinking disabled for faster responses.

- **Gemini 2.0 Flash (Legacy)**  
  Older model kept for compatibility with existing saved settings.

- **Gemini 1.5 Flash (Legacy)**  
  Older budget model kept for compatibility with existing saved settings.

#### 🔹 OpenAI Models

- **gpt-4o-mini (cheap + fast)**  
  Budget-friendly and very fast.

- **gpt-5-mini**  
  Improved nuance while remaining cost-efficient.

- **gpt-4o (premium quality)**  
  Highest refinement and emotional accuracy.

---

### 🌐 Machine Translation Options

#### 🔹 DeepL Free

- No model selection required
- Machine translation, not an LLM
- Very fast
- Free tier includes 500,000 characters per month
- Allows roughly 9 full movies per month on average
- Uses DeepL-supported source and target languages only
- Best if you want a straightforward translation provider without model tuning

#### 🔹 LibreTranslate

- Free self-hosted translation option
- Can run on a home server or local network
- Good fit for offline / LAN-first environments
- Better privacy because translations can stay inside your own network
- No paid cloud API required
- Can be very fast on local network setups
- Requires a full base URL including `http://` or `https://`
- Source and target languages must exist on your LibreTranslate server

Example use case:

- a local server such as `http://192.168.x.x:5000`
- language loading restricted with something like `LT_LOAD_ONLY=en,ro`
- batch limit set above the selected chunk size

---

## 3️⃣ Configure Translatarr

Kodi → Add-ons → Programs → Translatarr → Settings

Set:

- Translation Mode (`Auto` or `Manual`)
- Dual-Language Display (`Off` by default, optional source-above-translation output)
- Provider (Gemini, OpenAI, DeepL Free machine translation, or LibreTranslate)
- API Key
- Base URL for LibreTranslate if using a self-hosted server
- Source Language
- Target Language
- Model (Gemini/OpenAI only)
- Subtitle Folder (IMPORTANT for Manual mode – see below)

---

## 4️⃣ Play a Movie 🎥

1. Start playing a movie.  
2. Download subtitles using any Kodi subtitle addon  
   OR manually place an `.srt` file in your configured subtitle folder.

Translatarr will:

- Detect the subtitle automatically in the active mode  
- Translate it  
- Show progressive real-time subtitle updates while translation is running
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

# 📦 Extract Embedded SRT (Manual Mode)

This feature is for users who keep subtitles embedded inside local MKV files and want Translatarr to create the source `.srt` automatically when Manual mode does not find one yet.

How it works:

- Manual mode first checks your configured subtitle folder as usual
- If no usable external source subtitle is found yet, Translatarr can try extracting the configured **source-language** subtitle track from the currently playing **local MKV**
- The extracted subtitle is saved into your manual subtitle folder using the movie filename and your selected source language suffix
- After that, the normal Manual mode translation flow continues and Translatarr can create the translated target subtitle as usual

Requirements:

- This is **Manual mode only**
- The playing video must be a **local MKV file** exposed as a normal filesystem path
- You must enable **Embedded Subtitle Extraction** in settings
- External tools are required:
  - `mkvinfo`
  - `mkvextract`
  - `ffmpeg` only when the extracted subtitle must be converted from ASS/SSA to SRT

Current limitations:

- Local filesystem paths are supported
- USB-attached HDDs and SSDs are supported when Kodi exposes them as normal file paths
- Windows `smb://server/share/...` library paths can also work when they resolve to an accessible UNC network path for `mkvinfo` and `mkvextract`, but extraction on network-backed files can be much slower than local playback and may not feel practical for instant live use
- `plugin://`, `http://`, and similar non-filesystem playback paths are not currently supported for extraction
- Extraction currently targets **MKV** files only

Observed network-path performance note:

- Over SMB/UNC, extraction can be significantly slower than local files, but it may still be usable depending on your setup. In real tests on a 1 Gbps network, `mkvextract` advanced at roughly 10-20% per minute, so users should expect some lag before extraction completes depending on file layout, share performance, and network speed

Practical note:

- If a source `.srt` already exists in your manual subtitle folder, Manual mode still uses the normal subtitle-folder workflow first
- If a translated target subtitle for the current video already exists, Manual mode skips unnecessary retranslation

Tested result:

- Verified successfully with a local embedded-subtitle MKV workflow: Translatarr detected the newly extracted source subtitle immediately and produced a target-language `.srt` through DeepL in about 2 seconds, then displayed it during playback

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

- Total tokens or characters used  
- Estimated API cost  
- Model selected  
- Total chunks  
- Processing time  

You always know exactly what you spend.

For LibreTranslate self-hosted setups, estimated API cost remains $0.0000 inside Translatarr because the provider itself is intended as a no-cost self-hosted option.

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
- DeepL Free (when supported languages fit your use case)
- LibreTranslate on your own server for a no-cost self-hosted workflow

Both are extremely affordable for full-length films.

---

# 🛠 Troubleshooting

**No translation appears:**

- Check API key  
- Check provider selected  
- If using DeepL, verify the selected languages are available in the DeepL-only pickers
- If using LibreTranslate, verify the full URL starts with `http://` or `https://`
- If using LibreTranslate, verify the server actually loaded the selected languages
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
- DeepL Free for supported-language subtitle translation
- LibreTranslate on your own LAN or offline server

---

# ☕ Support the Project

If you enjoy Translatarr and want to support development:

https://www.buymeacoffee.com/addonniss








