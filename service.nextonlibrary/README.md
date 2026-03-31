# Next On Library

`service.nextonlibrary` is a Kodi service add-on for library TV episodes.

It adds two simple playback helpers:

- `Skip Intro`
- `Next On`

## What it does

- Watches TV episode playback from the Kodi library
- Finds the next episode in the same show
- Uses chapter markers when Kodi exposes them
- Can show `Skip Intro` during early playback
- Can show `Next` near the end of the episode
- Uses simple on-screen overlay buttons

## Scope

This add-on is intentionally small and focused.

It is meant for users who want lightweight playback helpers for library episodes without a large custom interface.

## Settings

- Enable or disable the service
- Prefer chapter-based Next timing
- Set the Next fallback percentage
- Enable or disable Skip Intro
- Set the Skip Intro chapter window
- Optionally enable a manual Skip Intro fallback window
- Enable debug logging

## Notes

- Works with library TV episodes only
- `Next` prefers the last usable chapter before the end
- `Skip Intro` prefers early chapter markers when they are available
- Manual Skip Intro fallback is optional
- Launching the add-on from Programs opens its settings
