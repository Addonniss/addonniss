# 🎬 Translatarr: AI-Powered Subtitle Translator

Any Language to Your Language translation addon.

This project began as a fork of [service.kodilive.translator.ai](https://github.com/Kirek66/service.kodilive.translator.ai) but has since evolved using my own logic for translation and only Gemini as AI.

**Translatarr** is a smart Kodi service that uses Google's Gemini AI to provide high-quality, natural-sounding translations for your movies and TV shows. Unlike traditional translators that work word-for-word, Translatarr understands context, slang, and emotion, giving you subtitles that feel like they were written by a human.

---

## ⚡ Quick Start (Get running in 3 steps)

1. **Get your Key:** Visit [Google AI Studio](https://aistudio.google.com/) and click "Get API Key". It’s free and takes 30 seconds.
2. **Configure:** Open Translatarr settings in Kodi. Paste your API Key and select your Target Language (e.g., Romanian).
3. **Play a Movie:** Start a movie and download an English subtitle using any Kodi subtitle addon. Translatarr will automatically detect it and start the translation!

---

## ⚙️ Configuration Guide

To get the best results, you can fine-tune Translatarr in the settings menu. Here is what each parameter does:

### 1. Gemini API Key
* **What it is:** Your personal "password" to use Google's AI.
* **Pro Tip:** Copy and paste the key directly to avoid typos. If the key is wrong, the addon will stay silent.

### 2. Model AI
* **Options:** Gemini 2.0 Flash, 1.5 Flash, etc.
* **Recommendation:** Gemini 2.0 Flash is the fastest and most cost-effective "brain" available right now.

### 3. Source & Target Language
* **Source:** The language the original subtitles are in. Use "Auto-Detect" if you aren't sure.
* **Target:** Always ensure the Target Language is set to a specific language (e.g., Romanian). Setting the Target to "Auto-Detect" will cause the translation to fail or return the original text.
* **Files:** Translatarr will save files with the correct language code (e.g., `.ro.srt` for Romanian, `.fr.srt` for French).

### 4. Temperature
* **What it is:** The "Creativity" setting.
* **Lower (0.15):** Keeps the translation very accurate and literal. Recommended for subtitles.
* **Higher (0.7+):** Allows the AI to use more creative phrasing and slang.

### 5. Lines per Chunk
* **What it is:** How many lines are translated at once.
* **Recommended:** 50 or 100. Larger chunks are faster, but smaller chunks (50) are more reliable for very long movies.

### 6. Save Folder
* **Description:** The location where your new subtitles are saved.
* **Important:** This should be a folder that Kodi has permission to read/write, like your Downloads or Media folder.

### 7. Notification Modes
* **Show Statistics:** Pops up a summary box at the end showing how many lines were translated.
* **Simple Notifications:** Only shows a small percentage bar at the top of the screen so it doesn't interrupt your viewing.

---

## 🛠 Troubleshooting

* **No translation appears:** Check your API key and ensure the "Save Folder" path is correct in settings.
* **Translation stops midway:** This usually happens if the AI hits a "Safety Filter" (common in movies with heavy profanity). Try lowering the Temperature.
* **Artifacts:** If you see strange characters, ensure you are using the latest version of the addon which includes the "Language-Blind" cleaning logic.

---

## ☕ Support the Project
If you enjoy using Translatarr and want to help keep the development going (or buy a treat for my son Toma!), feel free to support me here:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/addonniss)
