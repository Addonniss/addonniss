# -*- coding: utf-8 -*-
import os, re, xbmcvfs, xbmcaddon
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')

def sanitize_filename(filename):
    """
    Removes characters that are illegal in Windows filenames.
    Forbidden: < > : " / \ | ? *
    """
    # Replace illegal characters with an underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Windows doesn't like files ending in a space or a period
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
    
    # 2. Windows-Proofing: Sanitize the final filename
    clean_name = sanitize_filename(clean_name)
            
    return os.path.join(save_dir, clean_name), clean_name

def parse_srt(content):
    # Ensure line endings are consistent
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)', content, re.DOTALL)
    if not blocks: return None, None
    
    timestamps = [(b[0], b[1]) for b in blocks]
    texts = [b[2].replace('\n', ' | ') for b in blocks]
    return timestamps, texts

def write_srt(path, timestamps, translated_texts):
    # Windows-Proofing: Define newline outside f-strings to avoid SyntaxErrors on older Python
    nl = "\n"
    
    # Construct the SRT structure using 'nl' variable instead of literal '\n'
    final_srt = [
        f"{t[0]}{nl}{t[1]}{nl}{txt.replace(' | ', nl).replace('[BR]', nl)}{nl}" 
        for t, txt in zip(timestamps, translated_texts)
    ]
    
    with xbmcvfs.File(path, 'w') as f:
        f.write(nl.join(final_srt))
