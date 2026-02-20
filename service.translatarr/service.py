# -*- coding: utf-8 -*-
import xbmc, xbmcaddon, xbmcvfs, xbmcgui, os, time, math, re
from languages import get_lang_params

import ui
import translator
import file_manager

ADDON = xbmcaddon.Addon('service.translatarr')

def log(msg): 
    xbmc.log(f"[Gemini-Translator] {msg}", xbmc.LOGINFO)

def process_subtitles(original_path):
    try:
        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]
        
        save_path, clean_name = file_manager.get_target_path(original_path, video_name)

        if xbmcvfs.exists(save_path):
            xbmc.Player().setSubtitles(save_path)
            return

        use_notifications = ADDON.getSettingBool('notify_mode')
        progress = ui.TranslationProgress(use_notifications)
        
        if use_notifications:
            ui.notify(f"Translating: {clean_name}")

        with xbmcvfs.File(original_path, 'r') as f:
            content = f.read()
        
        timestamps, texts = file_manager.parse_srt(content)
        if not timestamps: return

        all_translated = []
        cum_in = cum_out = idx = 0
        chunk_size = max(10, min(int(ADDON.getSetting('chunk_size') or 50), 150))
        total_lines = len(texts)
        total_chunks = math.ceil(total_lines / chunk_size)
        chunk_num = 0

        while idx < len(texts):
            if progress.is_canceled() or not xbmc.Player().isPlaying():
                progress.close()
                return

            chunk_num += 1
            curr_size = min(chunk_size, total_lines - idx)
            percent = int((idx / total_lines) * 100)
            
            progress.update(percent, os.path.basename(original_path), clean_name, chunk_num, total_chunks, idx, total_lines)

            # --- SMART RETRY LOGIC FOR 429 ERRORS ---
            res = None
            for attempt in range(3): # Try 3 times
                res, in_t, out_t = translator.translate_batch(texts[idx:idx + curr_size], curr_size)
                if res:
                    break
                else:
                    log(f"Attempt {attempt+1} failed (Likely 429). Retrying in 5s...")
                    time.sleep(5) # Wait for rate limit to reset

            if res:
                all_translated.extend(res)
                cum_in += in_t
                cum_out += out_t
                idx += curr_size
            else:
                progress.close()
                ui.notify("API Limit Reached (429). Try larger chunks.")
                return 

        file_manager.write_srt(save_path, timestamps, all_translated)
        xbmc.Player().setSubtitles(save_path)
        progress.close()

        cost = translator.calculate_cost(cum_in, cum_out)
        trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
        
        if ADDON.getSettingBool('show_stats'):
            src_file_name = os.path.basename(original_path)
            model_name = translator.get_model_string()
            ui.show_stats_box(src_file_name, clean_name, trg_name, cost, (cum_in + cum_out), chunk_num, chunk_size, model_name)
        
        if use_notifications:
            ui.notify(f"Complete! Cost: ${cost:.4f}", title=f"Translated to {trg_name}")

    except Exception as e:
        log(f"Process Error: {e}")

class GeminiMonitor(xbmc.Monitor):
    def __init__(self):
        super(GeminiMonitor, self).__init__()
        self.last_processed = ""

    def check_for_subs(self):
        if not xbmc.Player().isPlaying(): return
        _, src_iso = get_lang_params(ADDON.getSetting('source_lang'))
        _, trg_iso = get_lang_params(ADDON.getSetting('target_lang'))
        if trg_iso == "auto": trg_iso = "ro"
        target_ext = f".{trg_iso}.srt"

        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except: return

        custom_dir = ADDON.getSetting('sub_folder')
        if not custom_dir or not xbmcvfs.exists(custom_dir): return

        _, files = xbmcvfs.listdir(custom_dir)
        valid_files = []
        for f in files:
            f_low = f.lower()
            if video_name.lower() in f_low and f_low.endswith('.srt'):
                if target_ext in f_low: continue
                is_foreign = False
                match = re.search(r'\.([a-z]{2,3})\.srt$', f_low)
                if match:
                    lang = match.group(1)
                    if lang not in ['en', 'eng', src_iso]: is_foreign = True
                if not is_foreign: valid_files.append(f)
        
        if valid_files:
            prio = [f for f in valid_files if f".{src_iso}." in f.lower()] if src_iso != "auto" else []
            if not prio: prio = [f for f in valid_files if ".en." in f.lower() or ".eng." in f.lower()]
            src_list = prio if prio else valid_files
            src_list.sort(key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(), reverse=True)
            newest_path = os.path.join(custom_dir, src_list[0])
            
            if newest_path != self.last_processed:
                stat = xbmcvfs.Stat(newest_path)
                if stat.st_size() > 500 and (time.time() - stat.st_mtime() < 300):
                    self.last_processed = newest_path
                    process_subtitles(newest_path)

if __name__ == '__main__':
    monitor = GeminiMonitor()
    while not monitor.abortRequested():
        monitor.check_for_subs()
        if monitor.waitForAbort(10): break
