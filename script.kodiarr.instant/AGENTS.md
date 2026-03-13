# AGENTS.md

## Project identity

This project is a Kodi add-on that provides **instant context-menu integration with Radarr and Sonarr**.

It allows users to send movies or TV shows directly from Kodi to their media managers.

Primary design goals:

- simplicity
- reliability
- minimal UI friction
- fast execution
- safe API calls

## Add-on type

This is a **Kodi script addon** triggered through **context menu actions**.

Typical execution flow:

1. User opens Kodi context menu
2. User selects "Add to Radarr" or "Add to Sonarr"
3. Script receives selected media item
4. Script extracts metadata
5. Script sends API request to Radarr or Sonarr
6. User receives notification about success or failure

The script should **exit quickly after execution**.

## Key files

### `addon.xml`

Defines:

- addon metadata
- context menu integration
- script entry point

Agents must be careful when editing:

- context menu visibility rules
- extension points
- addon id
- addon version

### `default.py`

Context menu entry point of the script.

Responsibilities typically include:

- delegating execution into router logic
- preserving Kodi context-menu invocation behavior

Agents should preserve:

- action routing
- compatibility with Kodi list items
- existing command arguments

### `launcher.py`

Secondary script entry point.

Responsibilities typically include:

- opening addon settings when launched directly
- forwarding scripted `action=` calls into the router

Agents should preserve:

- settings-open behavior
- action detection from `sys.argv`

### `resources/lib/router.py`

Main runtime dispatcher.

Responsibilities typically include:

- parsing Kodi/script arguments
- handling test actions
- routing to Radarr or Sonarr flows
- fallback routing based on Kodi item type

Agents should preserve:

- current action names
- fallback behavior for movie vs TV items
- fast script exit after dispatch

### `resources/lib/context.py`

Kodi metadata extraction layer.

Responsibilities typically include:

- reading TMDb / IMDb / TVDb identifiers
- inspecting `ListItem` and container properties
- determining whether the current item is a movie, show, season, or episode

Agents should preserve:

- compatibility with Kodi info labels
- plugin path parsing behavior
- TV item classification logic

### `resources/lib/radarr.py`

Radarr integration layer.

Responsibilities typically include:

- testing Radarr connectivity
- movie lookup by external ID
- adding missing movies
- triggering movie search for existing or newly added entries

Agents should preserve:

- request payload structure
- notification behavior
- graceful handling of missing settings or lookup failures

### `resources/lib/sonarr.py`

Sonarr integration layer.

Responsibilities typically include:

- testing Sonarr connectivity
- series lookup by external ID
- add-or-search logic for shows, seasons, and episodes
- episode lookup before targeted episode search

Agents should preserve:

- per-item-type behavior
- season and episode validation
- graceful failure paths

### `resources/lib/common.py`

Shared helper module.

Responsibilities typically include:

- logging
- notifications and dialogs
- settings access
- URL normalization

Agents should preserve:

- current log prefix and tone
- lightweight helper behavior

### `resources/settings.xml`

Addon settings definition.

Responsibilities typically include:

- Radarr/Sonarr server configuration
- API key storage
- root folder and quality profile selection
- connection test actions if present

### API interaction

The addon interacts with:

- Radarr API
- Sonarr API

Typical operations include:

- sending movie title and year to Radarr
- sending series title to Sonarr
- triggering search or monitoring behavior

Agents should ensure:

- API requests remain simple
- errors are handled gracefully
- failures show user notifications

## Kodi-specific constraints

This addon runs inside Kodi's Python environment.

Agents must respect:

- `xbmc`
- `xbmcgui`
- `xbmcaddon`

Do not replace Kodi APIs with standard Python equivalents when Kodi provides a native method.

## Context menu behavior

Visibility rules in `addon.xml` determine when menu items appear.

Typical conditions involve:

- movie items
- TV show items
- library entries

Agents should avoid breaking these conditions.

Changes to visibility rules must be tested carefully.

## Metadata extraction

The script may read metadata from:

- Kodi ListItem properties
- Kodi database metadata
- library item type

Agents should:

- preserve compatibility with Kodi's metadata model
- avoid fragile string parsing
- prefer Kodi properties when available

## Error handling

Failures may occur when:

- Radarr/Sonarr server is unreachable
- API key is invalid
- media metadata is incomplete

Rules:

- show clear user notification
- avoid crashing the script
- fail gracefully

## Notifications

User notifications should be:

- clear
- short
- informative

Avoid notification spam.

Examples:

Good:
- "Added to Radarr"
- "Failed to contact Sonarr"

Bad:
- verbose debug logs
- repeated notifications

## Editing philosophy

Agents should:

- keep the script lightweight
- preserve quick execution
- avoid complex architecture
- prefer minimal patches

Avoid:

- large refactors
- unnecessary abstractions
- heavy dependencies
- background loops or long-running processes

## Python style guidelines

- keep functions small
- keep code readable
- avoid unnecessary complexity
- follow existing style patterns

## Validation checklist after edits

After modifying the addon:

- addon.xml still loads correctly
- launcher.py still opens settings correctly when run directly
- context menu entries still appear
- default.py executes without syntax errors
- router.py still resolves Radarr/Sonarr/test actions correctly
- Kodi metadata extraction still finds IDs for supported items
- Radarr action still triggers correctly
- Sonarr action still triggers correctly
- script exits cleanly

## Good prompts for agents

- Explain how router.py routes actions to Radarr or Sonarr.
- Check context menu visibility rules in addon.xml.
- Verify Radarr and Sonarr API request logic.
- Review context.py for Kodi metadata extraction edge cases.
- Check launcher.py and settings.xml behavior for direct launches.

## What to avoid

- changing addon id
- altering context menu structure unnecessarily
- introducing persistent background logic
- breaking compatibility with Kodi list item metadata
