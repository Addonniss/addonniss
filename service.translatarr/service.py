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
    
    try:
        temp_val = float(ADDON.getSetting('temp') or 0.15)
    except:
        temp_val = 0.15

    src_name, _ = get_lang_params(ADDON.getSetting('source_lang'))
    trg_name, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    source_instruction = src_name if src_name != "Auto-Detect" else "the detected original language"

    input_text = "\n".join([f"L{i:03}: {text}" for i, text in enumerate(text_list)])
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    prompt = (
        f"Translate the following subtitles from {source_instruction} to {trg_name}. "
        "Keep the same number of lines. Preserve the 'Lxxx:' prefix at the start of each line. "
        "The output must contain exactly the same number of lines as the input."
    )

    try:
        payload = {
            "contents": [{"parts": [{"text": f"{prompt}\n\n{input_text}"}]}],
            "generationConfig": {"temperature": temp_val, "topP": 0.95}
        }
        r = requests.post(url, json=payload, timeout=30)
        res_json = r.json()
        
        if 'candidates' not in res_json: return None, 0, 0
            
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        usage = res_json.get('usageMetadata', {})
        in_tokens = usage.get('promptTokenCount', 0)
        out_tokens = usage.get('candidatesTokenCount', 0)

        translated = []
        lines = raw_text.strip().split('\n')
        for line in lines:
            clean_line = re.sub(r'^.*?:\s*', '', line.strip())
            translated.append(clean_line)
            
        return translated[:expected_count], in_tokens, out_tokens
    except Exception as e:
        log(f"API Request failed: {e}")
        return None, 0, 0

def process_subtitles(original_path):
    trg_name, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
    if trg_iso == "auto": trg_name, trg_iso = "Romanian", "ro"

    trg_ext = f".{trg_iso}.srt"
    if trg_ext in original_path.lower(): return
    
    save_dir = ADDON.getSetting('sub_folder')
    base_name = os.path.basename(original_path)
    clean_name = re.sub(r'\.[a-z]{2}\.srt$', '', base_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'\.srt$', '', clean_name, flags=re.IGNORECASE) + trg_ext
    save_path = os.path.join(save_dir, clean_name)

    if xbmcvfs.exists(save_path):
        xbmc.Player().setSubtitles(save_path)
        return

    use_notifications = ADDON.getSettingBool('notify_mode')
    
    if not use_notifications:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('[B][COLOR gold]Translatarr AI[/COLOR][/B]', 'Initializing...')
    else:
        notify(f"Translating: {clean_name}")

    try:
        with xbmcvfs.File(original_path, 'r') as f: content = f.read()
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n$|$)', content, re.DOTALL)
        
        if not blocks: return

        timestamps = [(b[0], b[1]) for b in blocks]
        texts = [b[2].replace('\n', ' | ') for b in blocks]
        all_translated = []
        cum_in = cum_out = idx = 0

        try:
            chunk_size = int(ADDON.getSetting('chunk_size') or 50)
            chunk_size = max(10, min(chunk_size, 150))
        except: chunk_size = 50

        total_lines = len(texts)
        total_chunks = math.ceil(total_lines / chunk_size)
        chunk_num = 0

        while idx < len(texts):
            if (not use_notifications and pDialog.iscanceled()) or not xbmc.Player().isPlaying():
                if not use_notifications: pDialog.close()
                return
            
            chunk_num += 1
            curr_size = min(chunk_size, total_lines - idx)
            percent = int((idx / total_lines) * 100)
            
            if not use_notifications:
                line1 = f"[B]File:[/B] [COLOR gray]{base_name}[/COLOR]"
                line2 = f"[B]Action:[/B] [COLOR springgreen]Chunk {chunk_num} of {total_chunks}[/COLOR] ({curr_size} lines)"
                line3 = f"[B]Status:[/B] [COLOR lightblue]{idx:,} / {total_lines:,} lines completed[/COLOR]"
                pDialog.update(percent, line1, line2, line3)

            res, in_t, out_t = translate_text_only(texts[idx:idx + curr_size], curr_size)
            if res:
                all_translated.extend(res)
                cum_in += in_t
                cum_out += out_t
                idx += curr_size
            else:
                if not use_notifications: pDialog.close()
                notify("Translation segment failed.")
                return 

        final_srt = [f"{t[0]}\n{t[1]}\n{txt.replace(' | ', '\n').replace('[BR]', '\n')}\n" for t, txt in zip(timestamps, all_translated)]
        with xbmcvfs.File(save_path, 'w') as f: f.write("\n".join(final_srt))
        
        xbmc.Player().setSubtitles(save_path)
        if not use_notifications: pDialog.close()

        # Calculation from gemini_v2.py
        cost = ((cum_in / 1_000_000) * 0.075) + ((cum_out / 1_000_000) * 0.30)

        if ADDON.getSettingBool('show_stats'):
            stats_msg = (
                "[B][COLOR gold]TRANSLATARR SUCCESS[/COLOR][/B]\n"
                "------------------------------------------------------------\n"
                f"[B]File:[/B]  [COLOR lightgray]{clean_name}[/COLOR]\n"
                f"[B]Target:[/B] [COLOR lightblue]{trg_name}[/COLOR]\n"
                f"[B]Model:[/B]  [COLOR lightblue]{get_model_string()}[/COLOR]\n\n"
                "[B][COLOR orange]BILLING & USAGE[/COLOR][/B]\n"
                "------------------------------------------------------------\n"
                f"[B]• Input Tokens:[/B]    [COLOR springgreen]{cum_in:,}[/COLOR]\n"
                f"[B]• Output Tokens:[/B]   [COLOR springgreen]{cum_out:,}[/COLOR]\n"
                f"[B][COLOR gold]• Estimated Cost:[/COLOR][/B]  [B][COLOR gold]${cost:.4f}[/COLOR][/B]\n\n"
                "[I][COLOR gray]Subtitle applied automatically.[/COLOR][/I]"
            )
            DIALOG.textviewer("Translatarr Statistics", stats_msg)
        else:
            notify(f"Success! Cost: ${cost:.4f}")

    except Exception as e:
        log(f"Process Error: {e}")
        if 'pDialog' in locals(): pDialog.close()

class GeminiMonitor(xbmc.Monitor):
    def __init__(self):
        super(GeminiMonitor, self).__init__()
        self.last_processed = ""

    def check_for_subs(self):
        if not xbmc.Player().isPlaying(): return
        
        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except: return

        custom_dir = ADDON.getSetting('sub_folder')
        if not custom_dir or not xbmcvfs.exists(custom_dir): return

        _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
        if trg_iso == "auto": trg_iso = "ro"
        target_ext = f".{trg_iso}.srt"

        _, files = xbmcvfs.listdir(custom_dir)
        
        # Filter for files matching the movie name
        valid_files = [f for f in files if video_name.lower() in f.lower() 
                       and f.lower().endswith('.srt') 
                       and target_ext not in f.lower()]
        
        if valid_files:
            # English Priority
            en_files = [f for f in valid_files if ".en." in f.lower() or ".eng." in f.lower()]
            
            if en_files:
                en_files.sort(key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(), reverse=True)
                newest_path = os.path.join(custom_dir, en_files[0])
            else:
                full_paths = [os.path.join(custom_dir, f) for f in valid_files]
                full_paths.sort(key=lambda x: xbmcvfs.Stat(x).st_mtime(), reverse=True)
                newest_path = full_paths[0]
            
            if newest_path != self.last_processed:
                stat = xbmcvfs.Stat(newest_path)
                if stat.st_size() > 500 and (time.time() - stat.st_mtime() < 180):
                    self.last_processed = newest_path
                    process_subtitles(newest_path)

if __name__ == '__main__':
    log("Translatarr service started.")
    monitor = GeminiMonitor()
    while not monitor.abortRequested():
        monitor.check_for_subs()
        if monitor.waitForAbort(10): break
    log("Translatarr service stopped.")
