# AGENTS.md

## Repository purpose
This repository hosts the Kodi repository **repository.addonniss** and the source code for the add-ons published through it.

Main responsibilities of this repo:
- maintain Kodi add-on source folders
- generate repository metadata
- package add-ons into zip files
- publish repository index through GitHub Pages

The repository includes multiple independent add-ons.

## Repository structure
repository.addonniss/
│
├─ .github/workflows
├─ create_repository.py
├─ zips
├─ addon.xml
├─ icon.png
│
├─ service.translatarr/
│
└─ script.kodiarr.instant/


Each add-on folder should be treated as an **independent project**.

Agents must read the `AGENTS.md` inside the specific addon folder before making changes.

Example:
- `service.translatarr/AGENTS.md`
- `script.kodiarr.instant/AGENTS.md`

Root agents should **not mix logic between add-ons**.

## Root repository responsibilities

The root repository mainly handles:

### 1. Repository generation
Handled by:
create_repository.py


This script typically:
- scans addon folders
- reads `addon.xml`
- extracts versions
- generates zipped packages
- updates `addons.xml`
- generates `addons.xml.md5`
- updates repository index

Agents must preserve this behavior.

### 2. Packaging
Add-ons are packaged into zip archives.

Rules:
- zip filename must match addon id and version
- folder structure inside zip must match Kodi expectations
- zips should contain the addon folder itself

Example:
service.translatarr-1.0.0.zip
└── service.translatarr/
├── addon.xml
├── service.py
└── ...


Agents should **not change packaging structure unless explicitly asked**.

### 3. Version handling
Versions are read from:
addon.xml

Agents must:
- preserve version format `x.x.x`
- avoid automatic version bumps unless requested
- avoid changing version detection logic casually

### 4. addons.xml generation
The repository index must contain metadata for all add-ons.

Agents should not:
- change XML formatting unnecessarily
- remove addon entries accidentally
- break Kodi repository compatibility

### 5. GitHub Pages publishing
This repository is designed to be served via GitHub Pages.

Agents should avoid:
- renaming repository structure
- breaking static hosting paths
- changing index links without explicit instruction

## Editing rules

When modifying repository automation:

- prefer minimal changes
- preserve backward compatibility
- keep zip generation deterministic
- avoid unnecessary dependencies
- keep script readable

Avoid:
- large refactors
- altering repository structure
- changing addon folder names
- modifying build logic unrelated to the task

## Add-on boundaries
Each add-on should be modified independently.

Add-on folders include:

- `service.translatarr`
- `script.kodiarr.instant`

Agents must **not assume shared runtime behavior between add-ons**.

## Python guidelines

For repository scripts:

- keep logic simple
- avoid heavy abstractions
- avoid external dependencies
- preserve compatibility with standard Python

## Validation checklist after edits

After modifying repository automation:

- script still runs without syntax errors
- zip archives still generate correctly
- addon.xml parsing still works
- addons.xml generation remains valid
- repository index still lists addons correctly

## Preferred workflow for agents

1. read `create_repository.py`
2. understand repository packaging logic
3. identify minimal change required
4. modify only relevant section
5. ensure add-on folders remain untouched

## Good prompts for this repo

- Explain how create_repository.py builds the repository.
- Verify zip packaging logic matches Kodi expectations.
- Check that addons.xml generation includes all addons.
- Ensure newest zip version is always linked in index.html.

## What to avoid

- rewriting the repository builder
- altering repository structure
- modifying add-on code when the task concerns packaging
- introducing dependencies
- changing zip naming conventions
