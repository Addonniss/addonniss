# Translatarr

Translatarr is a Kodi service add-on that detects subtitles during playback, translates them into your selected target language, writes a translated `.srt`, and switches playback to the translated subtitle automatically.

It supports these translation providers:

- Gemini: [model docs](https://ai.google.dev/gemini-api/docs/models/gemini)
- OpenAI: [GPT-4o](https://platform.openai.com/docs/models/gpt-4o), [GPT-4o mini](https://platform.openai.com/docs/models/gpt-4o-mini), [GPT-5 mini](https://platform.openai.com/docs/models/gpt-5-mini/)
- DeepL Free: [API Free plan](https://support.deepl.com/hc/en-us/articles/360021200939-DeepL-API-Free)
- LibreTranslate: [documentation](https://docs.libretranslate.com/)

## What New Users Need To Know

Translatarr runs as a background service in Kodi. Once configured, it watches for subtitles while a video is playing and processes them according to the selected mode.

Main capabilities:

- automatic subtitle translation during playback
- manual subtitle-folder workflow for users who want a fixed watch folder
- optional dual-language display
- optional SDH/HI cue removal
- optional embedded subtitle extraction from MKV and MP4 files
- optional remote embedded-subtitle extraction through the companion [Translatarr Remote Extractor](https://github.com/addonniss/repository.addonniss/blob/main/translatarr-remote-extractor/README.md)

## Basic Setup

Open:

`Kodi -> Add-ons -> Programs -> Translatarr -> Settings`

Configure these items first:

1. Enable the service.
2. Choose `Auto` or `Manual` translation mode.
3. Select a provider.
4. Enter the required provider credentials or server URL.
5. Set source and target languages.
6. Choose a model if you use Gemini or OpenAI.

After that, start video playback and download or load subtitles as you normally would in Kodi.

## Translation Modes

### Auto

Auto mode is the default. Translatarr looks for usable subtitles during playback in the normal locations Kodi and subtitle add-ons use, including sidecar subtitles next to the video when available.

Use Auto if you want the least manual setup.

### Manual

Manual mode watches a specific subtitle folder that you choose in the Translatarr settings.

For Manual mode to work reliably:

- set a writable subtitle folder in Translatarr
- set Kodi's subtitle storage location to the same folder

Use Manual if you want predictable folder-based behavior or if your subtitle add-on saves files into a custom location.

## Providers

### Gemini

Requires a Gemini API key. Model selection is available in settings, including Gemini 2.5 Flash and the fast variant of Gemini 2.5 Flash.

### OpenAI

Requires an OpenAI API key. Model selection is available in settings, including GPT-4o, GPT-4o mini, and GPT-5 mini.

### DeepL Free

Requires a DeepL API key. DeepL API Free includes 500,000 characters per month, which is roughly enough for about 10 movies on average. Available languages depend on what DeepL Free supports.

### LibreTranslate

Requires a LibreTranslate server URL. An API key is optional if your server requires one.

Use a full base URL, for example:

`http://your-server:5000`

## Embedded Subtitle Extraction

Enable embedded subtitle extraction only if you need to work from subtitle tracks stored inside MKV or MP4 files.

There are two supported extraction paths:

- local extraction tools
- remote extraction through Translatarr Remote Extractor

### Local Extraction

If you enable local extraction, configure the tool folders in settings:

- `mkvinfo` and `mkvextract` for MKV
- `ffmpeg` and `ffprobe` for MP4

Local extraction works best when Kodi exposes the video as a real filesystem path.

### Remote Extraction

Use Translatarr Remote Extractor if Kodi cannot run local extraction tools reliably on the playback device, or if the media is better accessed from another machine.

It is the recommended setup for Android and NVIDIA Shield devices.

If you enable it, configure:

- Remote Extractor URL
- bearer token if your remote service uses authentication
- timeout

The remote service must be able to resolve the playing media path to a real mounted media path on the server.

See the companion project here:

[Translatarr Remote Extractor](https://github.com/addonniss/repository.addonniss/blob/main/translatarr-remote-extractor/README.md)

## Optional Settings

These settings are not required for first-time setup, but they affect output:

- `Dual-Language Display`: shows source text together with the translation
- `Translation Style`: controls tone for supported LLM providers
- `Dialogue Lines Per Chunk`: adjusts request size and can help with provider stability
- `Remove SDH/HI Cues`: removes hearing-impaired subtitle cues while keeping dialogue
- `Show Stats` and `Notifications`: controls user-facing feedback in Kodi

## Troubleshooting

If translation does not start:

- confirm the service is enabled
- confirm a video is actively playing
- confirm the correct provider is selected
- confirm the provider key or LibreTranslate URL is valid
- in Manual mode, confirm Kodi and Translatarr use the same subtitle folder

If embedded extraction does not work:

- confirm embedded extraction is enabled
- confirm the required local tools are configured, or the remote extractor is configured
- confirm the media path is accessible to the selected extraction method

If subtitles are detected but translation fails:

- lower the chunk size
- verify the selected source and target languages
- verify the provider-specific configuration for the selected service

## Notes

- Translatarr is designed for subtitle translation during playback, not bulk subtitle processing outside Kodi.
- The add-on includes a changelog viewer in Kodi through the launcher entry point.
