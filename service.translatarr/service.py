# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import os
import time
import math
import re

import translator
import file_manager
import ui
from languages import get_lang_params

ADDON = xbmcaddon.Addon('service.translatarr')


# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------
def log(msg):
    xbmc.log(f"[Translatarr] {msg}", xbmc.LOGINFO)


# ----------------------------------------------------------
# Subtitle Processing
# ----------------------------------------------------------
def process_subtitles(original_path, monitor):
    try:
        if not xbmc.Player().isPlaying():
            return

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]

        save_path, clean_name = file_manager.get_target_path(original_path, video_name)

        # Skip if already translated
        if xbmcvfs.exists(save_path):
            xbmc.Player().setSubtitles(save_path)
            return

        # -----------------------------------
        # SETTINGS (LIVE — from monitor)
        # -----------------------------------
        use_notifications = monitor.use_notifications
        show_stats = monitor.show_stats
        initial_chunk = max(10, min(int(monitor.chunk_size or 100), 150))
        target_lang = monitor.target_lang

        model_name = translator.get_model_string()

        progress = ui.TranslationProgress(
            model_name=model_name,
            title=video_name
        )

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

        # -----------------------------------
        # TRANSLATION LOOP
        # -----------------------------------
        while idx < total_lines:

            if progress.is_canceled() or not xbmc.Player().isPlaying():
                progress.close()
                return

            success = False

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
                    log(f"Chunk failed at index {idx}, retrying smaller...")
                    time.sleep(2)

            if not success:
                progress.close()
                ui.notify("Critical failure: API rejected all chunk sizes.")
                return

        # -----------------------------------
        # COMPLETE
        # -----------------------------------
        progress.update(
            100,
            os.path.basename(original_path),
            clean_name,
            total_chunks_est,
            total_chunks_est,
            total_lines,
            total_lines
        )

        file_manager.write_srt(save_path, timestamps, all_translated)
        xbmc.Player().setSubtitles(save_path)
        progress.close()

        total_time = time.time() - start_time
        cost = translator.calculate_cost(cum_in, cum_out)
        trg_name, _ = get_lang_params(target_lang)

        # -----------------------------------
        # STATS BOX
        # -----------------------------------
        if show_stats:
            ui.show_stats_box(
                os.path.basename(original_path),
                clean_name,
                trg_name,
                cost,
                cum_in + cum_out,
                total_chunks_est,
                initial_chunk,
                model_name,
                total_time
            )

        # -----------------------------------
        # SIMPLE NOTIFICATION (WITH COST)
        # -----------------------------------
        if use_notifications:
            ui.notify(
                f"✔ Done in {ui.format_time(total_time)} | Cost: ${cost:.4f}",
                title=f"{model_name} → {trg_name}"
            )

    except Exception as e:
        log(f"Processing error: {e}")


# ----------------------------------------------------------
# Monitor
# ----------------------------------------------------------
class TranslatarrMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.last_processed = ""
        self.reload_settings()

    # -----------------------------------
    # Load settings dynamically
    # -----------------------------------
    def reload_settings(self):
        self.use_notifications = ADDON.getSettingBool('notify_mode')
        self.show_stats = ADDON.getSettingBool('show_stats')
        self.chunk_size = int(ADDON.getSetting('chunk_size') or 100)
        self.source_lang = ADDON.getSetting('source_lang')
        self.target_lang = ADDON.getSetting('target_lang')

    # -----------------------------------
    # Auto-called when user changes settings
    # -----------------------------------
    def onSettingsChanged(self):
        log("Settings changed — reloading live.")
        self.reload_settings()

    # -----------------------------------
    # Detect new subtitle
    # -----------------------------------
    def check_for_subs(self):

        if not xbmc.Player().isPlaying():
            return

        _, src_iso = get_lang_params(self.source_lang)
        _, trg_iso = get_lang_params(self.target_lang)

        if trg_iso == "auto":
            trg_iso = "ro"

        target_ext = f".{trg_iso}.srt"

        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except:
            return

        custom_dir = ADDON.getSetting('sub_folder')

        if not custom_dir or not xbmcvfs.exists(custom_dir):
            return

        _, files = xbmcvfs.listdir(custom_dir)

        valid_files = []

        for f in files:
            f_low = f.lower()

            if video_name.lower() in f_low and f_low.endswith('.srt'):

                if target_ext in f_low:
                    continue

                match = re.search(r'\.([a-z]{2,3})\.srt$', f_low)
                if match:
                    lang = match.group(1)
                    if lang not in ['en', 'eng', src_iso]:
                        continue

                valid_files.append(f)

        if not valid_files:
            return

        # Sort by newest modified
        valid_files.sort(
            key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(),
            reverse=True
        )

        newest_path = os.path.join(custom_dir, valid_files[0])
        stat = xbmcvfs.Stat(newest_path)

        # Avoid tiny/incomplete downloads
        if stat.st_size() < 500:
            return

        save_path, _ = file_manager.get_target_path(newest_path, video_name)

        if xbmcvfs.exists(save_path):
            return

        if newest_path == self.last_processed:
            return

        self.last_processed = newest_path

        process_subtitles(newest_path, self)


# ----------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------
if __name__ == '__main__':

    monitor = TranslatarrMonitor()

    while not monitor.abortRequested():

        monitor.check_for_subs()

        if monitor.waitForAbort(5):
            break
