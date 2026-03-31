# Next On Library

`service.nextonlibrary` is a Kodi service add-on that offers the next library episode near the end of the current one.

## What it does

- Watches TV episode playback from the Kodi library
- Finds the next episode in the same show
- Prefers the last chapter marker as the trigger point
- Falls back to a user-defined playback percentage when chapter data is unavailable
- Shows a simple on-screen `Next` button

## Scope

This add-on is intentionally small and focused.

It is meant for users who want a lightweight next-episode prompt for library playback with chapter-aware timing.

## Settings

- Enable or disable the service
- Prefer chapter-based triggering
- Set the fallback trigger percentage
- Enable debug logging

## Notes

- Works with library TV episodes only
- If chapter data is not exposed by Kodi for a given item, the fallback percentage is used
- Launching the add-on from Programs opens its settings
