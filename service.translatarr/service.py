# -*- coding: utf-8 -*-
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, os, requests, json, re, time, math
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')
DIALOG = xbmcgui.Dialog()

def log(msg): 
    xbmc.log(f"[Gemini-Translator] {msg}", xbmc.LOGINFO)

def notify(msg, title="Translatarr", duration=3000):
    DIALOG.notification(title, msg, xbmcgui.NOTIFICATION_INFO, duration)

def get_model_string():
    model_index = ADDON.getSetting('model') or "0"
    mapping = {"0": "gemini-2.0-flash", "1": "gemini-1.5-flash", "2": "gemini-2.5-flash"}
    return mapping.get(model_index, "gemini-2.0-flash")

def translate_text_only(text_list, expected_count):
    api_key = ADDON.getSetting('api_key')
    model_name = get_model_string()
    try: temp_val = float(ADDON.getSetting('temp') or 0.15)
    except: temp_val = 0.15

    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    source_instruction = src_name if src_name != "Auto-Detect" else "the detected original language"

    input_text = "\n".join([f"L{i:03}: {text}" for i, text in enumerate(text_list)])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = (f"Translate from {source_instruction} to {trg_name}. Keep lines equal. Prefix 'Lxxx:'.")

    try:
        payload = {"contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}], "generationConfig": {"temperature": temp_val}}
        r = requests.post(url, json=payload, timeout=30)
        res_json = r.json()
        if 'candidates' not in res_json: return None, 0, 0
            
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        usage = res_json.get('usageMetadata', {})
        return [re.sub(r'^.*?:\s*', '', l.strip()) for l in raw_text.strip().split('\n')][:expected_count], usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
    except: return None, 0, 0

def process_subtitles(original_path):
    trg_name, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    if trg_iso == "auto": trg_iso = "ro"
    
    # CRITICAL: If the file we found IS already our target language, STOP.
    if f".{trg_iso}." in original_path.lower():
        log(f"Skipping {original_path} - already in target language.")
        return

    save_dir = ADDON.getSetting('sub_folder')
    base_name = os.path.basename(original_path)
    clean_name = re.sub(r'\.[a-z]{2,3}\.srt$', '', base_name, flags=re.IGNORECASE) + f".{trg_iso}.srt"
    save_path = os.path.join(save_dir, clean_name)

    if xbmcvfs.exists(save_path):
        xbmc.Player().setSubtitles(save_path)
        return

    use_notifications = ADDON.getSettingBool('notify_mode')
    if not use_notifications:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('[B][COLOR gold]Translatarr AI[/COLOR][/B]', 'Starting...')
    else:
        notify(f"Starting translation to {trg_name}...", "Translatarr")

    try:
        with xbmcvfs.File(original_path, 'r') as f: content = f.read()
        blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)', content, re.DOTALL)
        if not blocks: return

        timestamps = [(b[0], b[1]) for b in blocks]
        texts = [b[2].replace('\n', ' | ') for b in blocks]
        all_translated = []
        cum_in = cum_out = idx = 0
        chunk_size = int(ADDON.getSetting('chunk_size') or 50)
        total_chunks = math.ceil(len(texts) / chunk_size)

        while idx < len(texts):
            if (not use_notifications and pDialog.iscanceled()) or not xbmc.Player().isPlaying():
                if not use_notifications: pDialog.close()
                return
            
            curr_size = min(chunk_size, len(texts) - idx)
            percent = int((idx / len(texts)) * 100)
            chunk_num = (idx // chunk_size) + 1
            
            # Progress Logic
            msg = f"Chunk {chunk_num}/{total_chunks} ({idx}/{len(texts)} lines)"
            if not use_notifications:
                pDialog.update(percent, f"[B]File:[/B] {base_name}\n[B]Progress:[/B] [COLOR springgreen]{msg}[/COLOR]")
            elif chunk_num % 2 == 0: # Notify every 2nd chunk to avoid spamming
                notify(msg, f"Translating... {percent}%")

            res, in_t, out_t = translate_text_only(texts[idx:idx + curr_size], curr_size)
            if res:
                all_translated.extend(res)
                cum_in += in_t; cum_out += out_t; idx += curr_size
            else:
                if not use_notifications: pDialog.close()
                notify("Translation failed."); return 

        final_srt = [f"{t[0]}\n{t[1]}\n{txt.replace(' | ', '\n')}\n" for t, txt in zip(timestamps, all_translated)]
        with xbmcvfs.File(save_path, 'w') as f: f.write("\n".join(final_srt))
        
        xbmc.Player().setSubtitles(save_path)
        if not use_notifications: pDialog.close()

        cost = ((cum_in / 1_000_000) * 0.075) + ((cum_out / 1_000_000) * 0.30)
        
        # Show Results
        if ADDON.getSettingBool('show_stats'):
            DIALOG.textviewer("Stats", f"File: {clean_name}\nCost: ${cost:.4f}\nTokens: {cum_in + cum_out}")
        if use_notifications:
            notify(f"Success! Cost: ${cost:.4f}", "Translation Done")

    except Exception as e:
        log(f"Error: {e}")
        if 'pDialog' in locals(): pDialog.close()

class GeminiMonitor(xbmc.Monitor):
    def __init__(self):
        super(GeminiMonitor, self).__init__()
        self.last_processed = ""

    def check_for_subs(self):
        if not xbmc.Player().isPlaying(): return
        
        # Determine current target ISO
        _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
        if trg_iso == "auto": trg_iso = "ro"
        
        custom_dir = ADDON.getSetting('sub_folder')
        if not custom_dir or not xbmcvfs.exists(custom_dir): return

        _, files = xbmcvfs.listdir(custom_dir)
        
        # 1. Filter out already translated files (prevents loops)
        # 2. Filter for files modified in the last 3 minutes (fresh downloads)
        valid_files = []
        for f in files:
            if f.lower().endswith('.srt') and f".{trg_iso}." not in f.lower():
                path = os.path.join(custom_dir, f)
                stat = xbmcvfs.Stat(path)
                if (time.time() - stat.st_mtime() < 180) and stat.st_size() > 500:
                    valid_files.append(path)

        if valid_files:
            # Sort to find English priority
            valid_files.sort(key=lambda x: (".en." in x.lower() or ".eng." in x.lower()), reverse=True)
            newest_path = valid_files[0]
            
            if newest_path != self.last_processed:
                self.last_processed = newest_path
                process_subtitles(newest_path)

if __name__ == '__main__':
    log("Service started.")
    monitor = GeminiMonitor()
    while not monitor.abortRequested():
        monitor.check_for_subs()
        if monitor.waitForAbort(10): break
