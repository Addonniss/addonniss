# AGENTS.md

## Project identity
This repository is `service.translatarr`, a Kodi service add-on focused on subtitle discovery, translation, generation, storage, and safe reloading during playback.

The project runs inside Kodi's Python environment, so stability and Kodi compatibility matter more than aggressive refactoring.

## Primary goals
- Keep subtitle translation reliable during playback
- Avoid subtitle flicker or repeated reloads
- Avoid duplicate processing of the same subtitle
- Preserve Kodi compatibility and existing user behavior
- Prefer minimal, low-risk patches

## High-priority risks
When making changes, treat these as critical risks to avoid:

- reloading the same subtitle repeatedly
- translating the same subtitle multiple times unnecessarily
- polling loops that trigger too often
- subtitle flicker during playback
- race conditions between detection, translation, and reload
- breaking compatibility with external subtitle add-ons
- breaking path handling for Kodi virtual/special paths
- excessive logging or notifications inside tight loops

## Editing philosophy
- Prefer the smallest safe fix.
- Do not rewrite working parts just for style.
- Do not rename files, functions, classes, or settings unless explicitly requested.
- Preserve current logging style and overall code structure.
- Keep user-visible behavior stable unless the task explicitly changes behavior.
- Be conservative with service-loop logic, playback checks, and subtitle reload actions.

## Environment constraints
This add-on runs inside Kodi, not normal desktop Python.

Be careful with:
- `xbmc`
- `xbmcaddon`
- `xbmcgui`
- `xbmcvfs`
- Kodi monitor lifecycle
- player state checks
- Kodi subtitle APIs
- Kodi special paths

Do not assume:
- unrestricted filesystem access
- normal terminal behavior
- standard long-running daemon patterns outside Kodi lifecycle
- that Python-only solutions are safe if Kodi-specific APIs already handle the task

## Core areas of the repo

### `service.py`
Main service lifecycle and polling logic.

Typical responsibilities:
- startup
- settings reload
- playback monitoring
- subtitle detection
- translation trigger conditions
- translated subtitle apply/reload behavior

Be extremely careful when editing:
- sleep/poll intervals
- state variables
- conditions that decide whether a subtitle is "new"
- logic that triggers re-translation or re-apply
- code that runs every polling cycle

### `launcher.py`
Direct-launch script entry point.

Typical responsibilities:
- opening addon settings when launched directly
- forwarding scripted actions into the addon entry path if supported

Be careful to preserve:
- settings-open behavior
- direct-launch usability from Kodi UI
- compatibility with current `addon.xml` script registration

### `translator.py`
Translation orchestration and provider-facing logic.

Typical responsibilities:
- language selection
- provider/model routing
- chunking
- prompt construction
- response cleanup
- translated text recomposition

Be careful to preserve:
- chunk ordering
- line integrity
- timestamp alignment
- fallback handling
- provider-specific quirks

### `languages.py`
Language mapping and selection compatibility.

Typical responsibilities:
- language names
- ISO codes
- settings interoperability
- mapping between display names and provider-compatible codes

Be careful not to:
- break legacy saved settings
- mismatch display name vs ISO code
- introduce inconsistent mappings across providers

### `file_manager.py`
Subtitle file discovery, read/write, path resolution, and safe output handling.

Typical responsibilities:
- locating subtitle files
- choosing source subtitle
- creating translated subtitle paths
- writing translated SRT files safely

Be careful with:
- duplicate file detection
- translated-vs-source filename distinction
- Kodi path compatibility
- temp/profile folder behavior

### `ui.py`
Notifications, dialogs, user messaging.

Rules:
- keep UI minimal
- do not spam notifications
- distinguish clearly between debug logging and user-facing messages

### `addon.xml`
Kodi add-on metadata and service registration.

Rules:
- preserve addon id and extension points
- do not alter compatibility-related metadata unless explicitly asked
- keep formatting clean and stable

### `resources/settings.xml`
Addon settings definition.

Typical responsibilities:
- provider selection
- API key and model settings
- source/target language selection
- chunk size and translation behavior options
- notification and live-translation toggles

Be careful not to:
- break saved setting compatibility
- silently change setting semantics
- desynchronize setting ids from runtime code

### `resources/language/resource.language.en_gb/strings.po`
Localized labels for settings and UI text.

Rules:
- keep msgctxt/msgid/msgstr structure intact
- avoid changing user-facing text unless the task requires it
- keep settings labels aligned with `resources/settings.xml`

## Subtitle workflow assumptions
Unless clearly shown otherwise, assume the intended flow is:

1. Playback starts or is active
2. Service polls at a controlled interval
3. Service checks whether a suitable subtitle exists
4. A source subtitle is selected only when needed
5. Translation happens only if required
6. A translated subtitle is written safely
7. Kodi reloads/applies subtitle only when there is a real change
8. Service avoids repeating the same action on the next poll

Any patch should protect this flow from repeated or redundant actions.

## Anti-flicker rules
Any change touching subtitle reload/application logic must try to ensure:

- the same subtitle file is not reapplied on every poll
- unchanged subtitle content does not trigger reload
- state survives across polling cycles where appropriate
- "subtitle found" and "subtitle already processed" are not treated as the same problem
- external subtitle add-on temporary files do not cause false "new subtitle" events every cycle

When investigating flicker, check for:
- unstable file path comparisons
- temporary file regeneration by other add-ons
- missing last-processed markers
- missing content/hash/path guard checks
- repeated reload calls even when no effective change happened

## External subtitle add-on awareness
This project may interact with subtitles coming from external sources or add-ons.

Known relevant locations may include:
- Translatarr profile subtitle folder
- A4KSubtitles temp/profile-related folders
- OpenSubtitles-related temp folders
- subtitle files next to the media file
- network paths / SMB paths / DAV paths surfaced through Kodi

Important rule:
Do not assume subtitles always come from one stable folder. Detection logic should be careful and conservative.

## Translation-provider rules
This project may support multiple providers such as OpenAI and Gemini.

When editing provider-related logic:
- preserve provider-specific settings
- preserve current model-selection behavior
- avoid breaking fallback defaults
- keep prompt/response parsing provider-aware
- only normalize malformed output where necessary
- do not overgeneralize one provider's quirks to all providers

### Gemini-specific caution
If stripping prefixes such as `Lxxx`, only do so in a controlled way that does not destroy valid subtitle content.

### OpenAI-specific caution
Do not change model or temperature behavior unless explicitly requested.

## SRT integrity rules
When editing subtitle text handling:
- preserve subtitle order
- preserve timestamps exactly unless the task explicitly changes them
- avoid inserting duplicate sequence numbers
- avoid leaving model artifacts like `L123`, accidental numbering, or formatting noise
- preserve intentional multiline subtitles
- ensure output remains valid SRT

## State-management rules
When editing service logic, prefer explicit state guards such as:
- last processed subtitle path
- last applied translated subtitle path
- last content hash
- playback session markers
- per-file processed flags where appropriate

Do not add complex state unless needed, but do not rely solely on repeated directory scans without a stable guard.

## Logging policy
Logging should help diagnose behavior without flooding logs.

Rules:
- preserve existing logging style
- add debug logs only where they clarify a state transition or branch decision
- avoid logging every polling cycle unless debugging is explicitly requested
- avoid noisy logs inside tight loops
- user notifications should be sparse and meaningful

Good log examples:
- source subtitle changed
- translated subtitle written
- reload skipped because file unchanged
- translation skipped because already processed
- playback state changed

Bad log examples:
- generic spam every poll
- duplicate logs for the same unchanged condition

## Settings compatibility
When editing settings handling:
- preserve backward compatibility where possible
- clamp numeric values safely
- support sensible defaults
- do not silently repurpose existing settings
- be careful with older numeric/string language setting formats

## Safe coding guidelines
- Keep patches local and easy to review.
- Prefer guard conditions over nested complexity.
- Avoid speculative cleanup unrelated to the task.
- Avoid architectural rewrites unless explicitly requested.
- Keep imports and naming stable.
- Watch for accidental dead code or duplicate returns.
- Validate indentation and Kodi-safe syntax carefully.

## Validation checklist after edits
After any meaningful change, validate:

1. Python syntax is valid
2. imports still resolve logically
3. no duplicate or unreachable return paths were introduced
4. polling loop still sleeps correctly
5. no obvious repeated-action path exists
6. subtitle detection logic still distinguishes source vs translated files
7. no user-notification spam was added
8. output subtitle generation still preserves SRT structure
9. launcher.py still opens settings correctly when launched directly
10. settings ids still match runtime setting lookups

## Preferred work pattern for agents
For non-trivial tasks:
1. Read relevant files first
2. Summarize likely root cause briefly
3. Identify smallest safe patch
4. Modify only the minimum necessary code
5. Re-check nearby logic for regressions
6. Clearly state risks or assumptions

## What to avoid
- broad rewrites
- changing many subsystems at once
- replacing Kodi-specific APIs with generic Python APIs without strong reason
- changing polling cadence casually
- introducing heavy abstractions
- unnecessary settings migrations
- altering visible behavior during playback unless required

## Good prompts for this repo
- Explain the Translatarr service lifecycle from startup to subtitle reload.
- Identify likely causes of repeated subtitle reloads or flicker.
- Find where duplicate subtitle processing may happen.
- Review source subtitle discovery logic across movie-folder, temp-folder, and profile-folder cases.
- Check translation recomposition for malformed line-prefix cleanup.
- Review settings.xml and strings.po for configuration compatibility risks.
- Suggest the smallest safe patch only.

## Output expectations
When asked to modify code:
- explain the root cause briefly
- propose the smallest safe fix
- preserve behavior outside scope
- mention assumptions clearly
- avoid unnecessary rewrites
