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
    _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))

    input_text = "\n".join([f"L{i:03}: {text}" for i, text in enumerate(text_list)])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    prompt = f"Translate to {trg_name}. Keep lines equal. Prefix 'Lxxx:'."

    try:
        payload = {"contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}], "generationConfig": {"temperature": temp_val}}
        r = requests.post(url, json=payload, timeout=30)
        res_json = r.json()
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        usage = res_json.get('usageMetadata', {})
        return [re.sub(r'^.*?:\s*', '', l.strip()) for l in raw_text.strip().split('\n')][:expected_count], usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)
    except: return None, 0, 0

def process_subtitles(original_path):
    _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
    if trg_iso == "auto": trg_iso = "ro"
    
    save_dir = ADDON.getSetting('sub_folder')
    base_name = os.path.basename(original_path)
    # Simplified naming logic to avoid regex crashes
    name_root = base_name.lower().replace('.en.srt', '').replace('.eng.srt', '').replace('.srt', '')
    clean_name = f"{name_root}.{trg_iso}.srt"
    save_path = os.path.join(save_dir, clean_name)

    if xbmcvfs.exists(save_path):
        log(f"Target {save_path} exists. Loading.")
        xbmc.Player().setSubtitles(save_path)
        return

    use_notifications = ADDON.getSettingBool('notify_mode')
    pDialog = None
    if not use_notifications:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('[B][COLOR gold]Translatarr[/COLOR][/B]', 'Starting...')
    else:
        notify(f"Translating to {trg_name}...")

    try:
        with xbmcvfs.File(original_path, 'r') as f: content = f.read()
        blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)', content, re.DOTALL)
        if not blocks: return

        timestamps = [(b[0], b[1]) for b in blocks]
        texts = [b[2].replace('\n', ' | ') for b in blocks]
        all_translated = []
        cum_in = cum_out = idx = 0
        chunk_size = int(ADDON.getSetting('chunk_size') or 50)

        while idx < len(texts):
            if (pDialog and pDialog.iscanceled()) or not xbmc.Player().isPlaying():
                if pDialog: pDialog.close()
                return
            curr_size = min(chunk_size, len(texts) - idx)
            percent = int((idx / len(texts)) * 100)
            
            if pDialog:
                pDialog.update(percent, f"Processing {idx}/{len(texts)} lines...")
            elif use_notifications and (idx // chunk_size) % 4 == 0:
                notify(f"Progress: {percent}%")

            res, in_t, out_t = translate_text_only(texts[idx:idx + curr_size], curr_size)
            if res:
                all_translated.extend(res); cum_in += in_t; cum_out += out_t; idx += curr_size
            else:
                if pDialog: pDialog.close()
                return 

        final_srt = [f"{t[0]}\n{t[1]}\n{txt.replace(' | ', '\n')}\n" for t, txt in zip(timestamps, all_translated)]
        with xbmcvfs.File(save_path, 'w') as f: f.write("\n".join(final_srt))
        xbmc.Player().setSubtitles(save_path)
        if pDialog: pDialog.close()
        
        cost = ((cum_in / 1_000_000) * 0.075) + ((cum_out / 1_000_000) * 0.30)
        if ADDON.getSettingBool('show_stats'):
            DIALOG.textviewer("Success", f"Cost: ${cost:.4f}\nTokens: {cum_in+cum_out}")
        if use_notifications:
            notify(f"Done! ${cost:.4f}")
    except Exception as e:
        log(f"Error: {e}")
        if pDialog: pDialog.close()

class GeminiMonitor(xbmc.Monitor):
    def __init__(self):
        super(GeminiMonitor, self).__init__()
        self.last_file = ""

    def check_for_subs(self):
        if not xbmc.Player().isPlaying(): return
        _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
        if trg_iso == "auto": trg_iso = "ro"
        
        path = ADDON.getSetting('sub_folder')
        if not path: return
        
        _, files = xbmcvfs.listdir(path)
        # Find English files that AREN'T translated yet
        for f in files:
            if f.lower().endswith('.srt') and ('.en.' in f.lower() or '.eng.' in f.lower()):
                full_path = os.path.join(path, f)
                # If we haven't handled this specific file in this session
                if full_path != self.last_file:
                    self.last_file = full_path
                    process_subtitles(full_path)

if __name__ == '__main__':
    log("Service Started")
    monitor = GeminiMonitor()
    while not monitor.abortRequested():
        monitor.check_for_subs()
        if monitor.waitForAbort(5): break
