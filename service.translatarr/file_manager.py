# -*- coding: utf-8 -*-
import os
import re
import xbmcvfs
import xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')


# -----------------------------------
# Filename Sanitization
# -----------------------------------
def sanitize_filename(filename):
    """
    Aggressively clean filenames for Windows/Linux.
    Removes illegal characters and fixes reserved names.
    """
    # Remove illegal characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Check for Windows reserved names
    name_part = os.path.splitext(sanitized)[0].upper()
    reserved = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    if name_part in reserved:
        sanitized = "_" + sanitized

    # Remove trailing periods or spaces
    return sanitized.strip('. ')


# -----------------------------------
# Get Target Path
# -----------------------------------
def get_target_path(original_path, video_name):
    """
    Determine where the translated SRT should be saved.
    Handles source/target language, Windows-safe names.
    """
    _, src_iso = get_lang_params(ADDON.getSetting('source_lang'))
    _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    if trg_iso == "auto":
        trg_iso = "ro"

    save_dir = ADDON.getSetting('sub_folder')
    base_name = os.path.basename(original_path)

    # Logic: Swap the extension for target language
    if src_iso != "auto" and f".{src_iso}.srt" in base_name.lower():
        clean_name = re.sub(rf'\.{src_iso}\.srt$', f'.{trg_iso}.srt', base_name, flags=re.IGNORECASE)
    else:
        clean_name = re.sub(r'\.(en|eng)\.srt$', f'.{trg_iso}.srt', base_name, flags=re.IGNORECASE)
        if not clean_name.endswith(f'.{trg_iso}.srt'):
            clean_name = re.sub(r'\.srt$', f'.{trg_iso}.srt', clean_name, flags=re.IGNORECASE)

    # Windows-proof filename
    clean_name = sanitize_filename(clean_name)

    # Full validated path
    full_path = xbmcvfs.validatePath(os.path.join(save_dir, clean_name))

    return full_path, clean_name


# -----------------------------------
# Parse SRT
# -----------------------------------
def parse_srt(content):
    """
    Parse an SRT file and return timestamps + text lines.
    Newlines inside a block are replaced with [BR].
    """
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.findall(
        r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)',
        content,
        re.DOTALL
    )
    if not blocks:
        return None, None

    timestamps = [(b[0], b[1]) for b in blocks]
    texts = [b[2].replace('\n', ' [BR] ') for b in blocks]

    return timestamps, texts


# -----------------------------------
# Write SRT
# -----------------------------------
def write_srt(path, timestamps, translated_texts):
    """
    Write translated texts to SRT file with proper formatting.
    Ensures Lxxx prefixes are removed and [BR] is converted back to line breaks.
    """
    nl = "\n"
    final_srt = []

    for t, txt in zip(timestamps, translated_texts):
        # Remove any surviving Lxxx prefixes
        scrubbed_txt = re.sub(r'^[ \t]*L\d{1,4}[:\-\s\.]*', '', txt, flags=re.IGNORECASE).strip()
        # Convert [BR] back to newline
        final_txt = scrubbed_txt.replace(' [BR] ', nl).strip()
        # Build SRT block
        final_srt.append(f"{t[0]}{nl}{t[1]}{nl}{final_txt}{nl}")

    # Write to file using xbmcvfs
    with xbmcvfs.File(path, 'w') as f:
        f.write(nl.join(final_srt))
