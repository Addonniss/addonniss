# -*- coding: utf-8 -*-
import os, re, xbmcvfs, xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def sanitize_filename(filename):
    """
    Aggressively cleans filenames for Windows OS.
    """
    # 1. Remove illegal characters: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 2. Check for Windows Reserved Names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    # We just prepend an underscore if it matches
    name_part = os.path.splitext(sanitized)[0].upper()
    reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    
    if name_part in reserved:
        sanitized = "_" + sanitized

    # 3. Windows hates trailing periods or spaces
    return sanitized.strip('. ')

def get_target_path(original_path, video_name):
    _, src_iso = get_lang_params(ADDON.getSetting('source_lang'))
    _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    if trg_iso == "auto": trg_iso = "ro"
    
    save_dir = ADDON.getSetting('sub_folder')
    base_name = os.path.basename(original_path)

    # 1. Logic: Swap the extension
    if src_iso != "auto" and f".{src_iso}.srt" in base_name.lower():
        clean_name = re.sub(rf'\.{src_iso}\.srt$', f'.{trg_iso}.srt', base_name, flags=re.IGNORECASE)
    else:
        clean_name = re.sub(r'\.(en|eng)\.srt$', f'.{trg_iso}.srt', base_name, flags=re.IGNORECASE)
        if not clean_name.endswith(f'.{trg_iso}.srt'):
            clean_name = re.sub(r'\.srt$', f'.{trg_iso}.srt', clean_name, flags=re.IGNORECASE)
    
    # 2. Windows-Proofing
    clean_name = sanitize_filename(clean_name)
    
    # 3. Use validatePath to fix slashes for the specific OS (Windows vs Linux)
    full_path = xbmcvfs.validatePath(os.path.join(save_dir, clean_name))
            
    return full_path, clean_name

def parse_srt(content):
    # Ensure line endings are normalized to avoid regex failure on Windows CRLF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)', content, re.DOTALL)
    if not blocks: return None, None
    
    timestamps = [(b[0], b[1]) for b in blocks]
    texts = [b[2].replace('\n', ' [BR] ') for b in blocks]
    return timestamps, texts

def write_srt(path, timestamps, translated_texts):
    nl = "\n"
    final_srt = [f"{t[0]}{nl}{t[1]}{nl}{txt.replace(' [BR] ', nl)}{nl}" for t, txt in zip(timestamps, translated_texts)]
    
    with xbmcvfs.File(path, 'w') as f:
        # Final join with native newlines
        f.write(nl.join(final_srt))
