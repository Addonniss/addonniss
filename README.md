# Addonniss Kodi Repository

This repository hosts the Kodi add-ons published by Addonniss, plus the companion service used by Translatarr for remote embedded subtitle extraction.

## What’s Included

### `service.translatarr`
Translatarr is a Kodi service add-on that detects subtitles during playback, translates them into your selected target language, writes a translated `.srt`, and switches playback to the translated subtitle automatically.

It supports these providers:

- Gemini
- OpenAI
- DeepL Free
- LibreTranslate

It also supports optional dual-language display, SDH/HI cue removal, embedded subtitle extraction, and the remote extractor companion service.

Links:

- [README](service.translatarr/README.md)
- [Changelog](service.translatarr/changelog.txt)

### `translatarr-remote-extractor`
This is a Docker-first companion service for `service.translatarr`, not a Kodi add-on.

It provides:

- remote embedded subtitle extraction
- `/health`, `/probe`, and `/extract` endpoints
- bearer-token authentication
- path mapping for `smb://`, UNC, and `dav://` playback paths

Links:

- [README](translatarr-remote-extractor/README.md)
- [Changelog](translatarr-remote-extractor/CHANGELOG.md)


### `service.nextonlibrary`
Skip Intro & Next is a Kodi service add-on that provides two lightweight playback helpers for TV episodes: `Skip Intro` and `Next On`.

It can use:

- online metadata from TheIntroDB and IntroDB.app
- local chapter markers exposed by Kodi
- a manual fallback intro window
- a fallback percentage trigger for the next-episode prompt

Links:

- [README](service.nextonlibrary/README.md)
- [Changelog](service.nextonlibrary/changelog.txt)


### `script.kodiarr.instant`
KodiARR Instant is a Kodi script add-on that adds context menu actions for sending movies to Radarr and TV shows, seasons, or episodes to Sonarr.

It includes:

- instant Radarr and Sonarr context menu entries
- connection test actions
- add-and-search flows for supported items
- a custom settings UI for quick setup

Links:

- [README](script.kodiarr.instant/README.md)
- [Changelog](script.kodiarr.instant/changelog.txt)



## Install

1. Add the repository as a source in Kodi's File Manager:

   `https://addonniss.github.io/repository.addonniss/zips/repository.addonniss/`

2. Or install the current repository zip directly from GitHub Pages:

   `https://addonniss.github.io/repository.addonniss/zips/repository.addonniss/repository.addonniss-1.0.1.zip`

3. In Kodi, go to `Add-ons` > `Install from zip file`, select the repository zip, then install the add-ons you want from `Install from repository`.

## Repository Notes

- This repo is structured for Kodi repository generation and GitHub Pages publishing.
- Each add-on is maintained as an independent project.
- `create_repository.py` builds the repository metadata and zip packages.

## Support

If you enjoy the project and want to support future development, you can donate here:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/addonniss)
