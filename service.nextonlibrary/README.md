# Skip.Intro.Next (S.I.N.)

`service.nextonlibrary` is a Kodi service add-on that adds two lightweight playback helpers for TV episodes:

- `Skip Intro`
- `Next On`

## Current Status

As of `0.0.5`, the add-on can use both local chapter markers and online metadata.

- `Skip Intro` can use:
  - online metadata from `TheIntroDB`
  - online metadata from `IntroDB.app`
  - local chapter markers exposed by Kodi
  - an optional manual fallback intro window
- `Next On` can use:
  - online metadata from `TheIntroDB`
  - online metadata from `IntroDB.app`
  - local chapter markers near the end of playback
  - a fallback percentage trigger

## What It Does

- Monitors episode playback in Kodi
- Shows a `Skip Intro` overlay when an intro or recap end can be determined
- Shows a `Next` overlay near the end of playback
- Uses simple on-screen overlay buttons instead of a heavy custom interface
- Supports online-metadata-first or chapter-first behavior through settings
- Includes an `Advanced` settings group with debug logging and `View Changelog`

## Playback Scope

- `Next On` is designed for Kodi library episode playback
- `Skip Intro` also works on non-library playback, including streaming or add-on playback, when Kodi exposes usable chapter markers or the add-on can resolve remote metadata

## Settings

### Next On

- `Enable Service`
- `Prefer Chapter Trigger`
- `Online Metadata Priority`
- `Fallback Trigger Percent`

Default behavior:
- `Online Metadata Priority` is `On`
- remote metadata is tried first
- local chapters are used as fallback

### Skip Intro

- `Enable Skip Intro`
- `Online Metadata Priority`
- `Enable Fallback Intro Window`
- `Intro Max Percent`
- `Fallback Intro Start`
- `Fallback Intro End`

Default behavior:
- `Enable Skip Intro` is `On`
- `Online Metadata Priority` is `On`
- remote metadata is tried first
- local chapters are used as fallback

### Advanced

- `Enable Debug Logging`
- `View Changelog`

## Online Metadata Sources

The add-on currently uses:

- `TheIntroDB`
- `IntroDB.app`

For TV episode lookups:

- `TheIntroDB` is queried with `tmdb_id`, `season`, and `episode`
- `IntroDB.app` is queried with the show `imdb_id`, `season`, and `episode`

## API Limits

### TheIntroDB

Documented limits used by the add-on integration:

- `/media` rate limit: `30 requests per 10 seconds`
- authenticated `/media` usage limit: `500 requests per day`
- unauthenticated `/media` usage limit: `100 requests per day`

The API also documents response headers for both rate and usage limits:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `X-UsageLimit-Limit`
- `X-UsageLimit-Remaining`
- `X-UsageLimit-Reset`

### IntroDB.app

This repository currently documents the lookup format used by the add-on, but not a published rate-limit policy for `IntroDB.app`.

## Notes

- Chapter markers remain valuable even when online metadata is enabled
- If remote metadata is unavailable, the add-on falls back to local chapter timing when possible
- If neither remote metadata nor usable chapter timing is available, `Next On` falls back to the configured percentage trigger
- `Skip Intro` can optionally fall back to a manual start/end window
- Launching the add-on from Programs opens its settings
