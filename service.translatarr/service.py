# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import os
import time
import math
import re

from languages import get_lang_params
import ui
import translator
import file_manager


# ----------------------------------------------------------
# Addon & logging
# ----------------------------------------------------------
ADDON_ID = 'service.translatarr'
ADDON = xbmcaddon.Addon(ADDON_ID)


def log(msg):
    xbmc.log(f"[Translatarr] {msg}", xbmc.LOGINFO)


# ----------------------------------------------------------
# Helper to always reload dynamic settings
# ----------------------------------------------------------
def get_setting_bool(key):
    xbmcaddon.Addon(ADDON_ID)._settings = None  # refresh cache
    return xbmcaddon.Addon(ADDON_ID).getSettingBool(key)

def get_setting(key, default=None):
    xbmcaddon.Addon(ADDON_ID)._settings = None
    val = xbmcaddon.Addon(ADDON_ID).getSetting(key)
    return val if val else default


# ----------------------------------------------------------
# Subtitle Processing
# ----------------------------------------------------------
def process_subtitles(original_path):
    try:
        # ✅ Reload Addon to pick up latest settings
        ADDON = xbmcaddon.Addon('service.translatarr')

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]

        save_path, clean_name = file_manager.get_target_path(original_path, video_name)

        # Already translated
        if xbmcvfs.exists(save_path):
            xbmc.Player().setSubtitles(save_path)
            return

        # ----------------------------
        # Read settings once
        # ----------------------------
        use_notifications = ADDON.getSettingBool('notify_mode')
        show_stats = ADDON.getSettingBool('show_stats')
        initial_chunk = max(10, min(int(ADDON.getSetting('chunk_size') or 100), 150))

        # ✅ Model name for progress bar
        model_name = translator.get_model_string()
        progress = ui.TranslationProgress(model_name, use_notifications=use_notifications)

        with xbmcvfs.File(original_path, 'r') as f:
            content = f.read()

        timestamps, texts = file_manager.parse_srt(content)
        if not timestamps:
            progress.close()
            return

        total_lines = len(texts)
        total_chunks_est = math.ceil(total_lines / initial_chunk)

        all_translated = []
        cum_in = 0
        cum_out = 0
        idx = 0
        start_time = time.time()

        while idx < total_lines:

            if progress.is_canceled() or not xbmc.Player().isPlaying():
                progress.close()
                return

            success = False

            # --- Adaptive Chunking ---
            for size in [initial_chunk, 50, 25]:

                curr_size = min(size, total_lines - idx)
                percent = int((idx / total_lines) * 100)
                current_chunk_display = math.ceil(idx / initial_chunk) + 1

                progress.update(
                    percent,
                    os.path.basename(original_path),
                    clean_name,
                    current_chunk_display,
                    total_chunks_est,
                    idx,
                    total_lines
                )

                res, in_t, out_t = translator.translate_batch(
                    texts[idx:idx + curr_size],
                    curr_size
                )

                if res:
                    all_translated.extend(res)
                    cum_in += in_t
                    cum_out += out_t
                    idx += curr_size
                    success = True
                    time.sleep(1)
                    break
                else:
                    log(f"Shrinking chunk at index {idx} to {size}...")
                    time.sleep(2)

            if not success:
                progress.close()
                ui.notify("Critical Failure: API rejected all chunk sizes.")
                return

        # Final 100% milestone
        progress.update(
            100,
            os.path.basename(original_path),
            clean_name,
            total_chunks_est,
            total_chunks_est,
            total_lines,
            total_lines
        )

        # Write and activate
        file_manager.write_srt(save_path, timestamps, all_translated)
        xbmc.Player().setSubtitles(save_path)
        progress.close()

        # ----------------------------
        # Show stats if enabled
        # ----------------------------
        if show_stats:
            cost = translator.calculate_cost(cum_in, cum_out)
            trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
            src_file_name = os.path.basename(original_path)

            ui.show_stats_box(
                src_file_name,
                clean_name,
                trg_name,
                cost,
                (cum_in + cum_out),
                total_chunks_est,
                initial_chunk,
                model_name
            )

        # Notify completion
        if use_notifications:
            cost = translator.calculate_cost(cum_in, cum_out)
            trg_name, _ = get_lang_params(ADDON.getSetting('target_lang'))
            ui.notify(
                f"Complete! Cost: ${cost:.4f}",
                title=f"Translated to {trg_name}"
            )

    except Exception as e:
        log(f"Process Error: {e}")


# ----------------------------------------------------------
# Monitor
# ----------------------------------------------------------
class TranslatarrMonitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()
        self.last_processed = ""

    def check_for_subs(self):

        if not xbmc.Player().isPlaying():
            return

        _, src_iso = get_lang_params(get_setting('source_lang', 'English'))
        _, trg_iso = get_lang_params(get_setting('target_lang', 'English'))

        if trg_iso == "auto":
            trg_iso = "ro"

        target_ext = f".{trg_iso}.srt"

        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except:
            return

        custom_dir = get_setting('sub_folder', '/storage/emulated/0/Download/sub/')
        if not custom_dir or not xbmcvfs.exists(custom_dir):
            return

        _, files = xbmcvfs.listdir(custom_dir)
        valid_files = []

        for f in files:
            f_low = f.lower()

            if video_name.lower() in f_low and f_low.endswith('.srt'):
                if target_ext in f_low:
                    continue

                is_foreign = False
                match = re.search(r'\.([a-z]{2,3})\.srt$', f_low)

                if match:
                    lang = match.group(1)
                    if lang not in ['en', 'eng', src_iso]:
                        is_foreign = True

                if not is_foreign:
                    valid_files.append(f)

        if valid_files:
            prio = (
                [f for f in valid_files if f".{src_iso}." in f.lower()]
                if src_iso != "auto"
                else []
            )

            if not prio:
                prio = [
                    f for f in valid_files
                    if ".en." in f.lower() or ".eng." in f.lower()
                ]

            src_list = prio if prio else valid_files

            src_list.sort(
                key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(),
                reverse=True
            )

            newest_path = os.path.join(custom_dir, src_list[0])

            if newest_path != self.last_processed:
                stat = xbmcvfs.Stat(newest_path)
                if stat.st_size() > 500 and (time.time() - stat.st_mtime() < 300):
                    self.last_processed = newest_path
                    process_subtitles(newest_path)


# ----------------------------------------------------------
# Entry
# ----------------------------------------------------------
if __name__ == '__main__':
    monitor = TranslatarrMonitor()
    while not monitor.abortRequested():
        monitor.check_for_subs()
        if monitor.waitForAbort(10):
            break

