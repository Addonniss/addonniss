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
DEBUG = ADDON.getSettingBool('debug_mode')  # <-- New debug mode setting

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------
def log(msg, level='info', force=False):
    """
    Custom logging:
    - force=True always logs
    - force=False logs only if DEBUG or level != 'debug'
    """
    if force or DEBUG or level != 'debug':
        xbmc.log(f"[Translatarr] {msg}", getattr(xbmc, f"LOG{level.upper()}"))

# ----------------------------------------------------------
# Subtitle Processing
# ----------------------------------------------------------
def process_subtitles(original_path, monitor):
    try:
        log(f"process_subtitles() called for: {original_path}", level='debug')

        if not xbmc.Player().isPlaying():
            log("No video playing, exiting.", level='debug')
            return

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]

        save_path, clean_name = file_manager.get_target_path(original_path, video_name)
        log(f"Target SRT: {save_path}")

        # Skip if already translated
        if xbmcvfs.exists(save_path):
            log("Translated file already exists. Setting subtitles...")
            xbmc.Player().setSubtitles(save_path)
            return

        # -----------------------------------
        # SETTINGS
        # -----------------------------------
        use_notifications = monitor.use_notifications
        show_stats = monitor.show_stats
        initial_chunk = max(10, min(int(monitor.chunk_size or 100), 150))
        target_lang = monitor.target_lang

        model_name = translator.get_model_string(monitor)
        log(f"Using model: {model_name}, target_lang: {target_lang}")

        progress = ui.TranslationProgress(
            model_name=model_name,
            title=video_name
        )

        with xbmcvfs.File(original_path, 'r') as f:
            content = f.read()

        timestamps, texts = file_manager.parse_srt(content)

        if not timestamps:
            log("SRT parsing failed. Exiting.", level='debug')
            progress.close()
            return

        total_lines = len(texts)
        total_chunks_est = math.ceil(total_lines / initial_chunk)
        log(f"Total lines: {total_lines}, estimated chunks: {total_chunks_est}", level='debug')

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
                log("Translation canceled or video stopped.")
                progress.close()
                return

            success = False

            for size in [initial_chunk, 50, 25]:

                curr_size = min(size, total_lines - idx)
                percent = int((idx / total_lines) * 100)
                current_chunk_display = math.ceil(idx / initial_chunk) + 1

                log(f"Translating chunk {current_chunk_display}/{total_chunks_est} ({curr_size} lines)", level='debug')

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
                    log(f"Chunk translated successfully ({curr_size} lines)", level='debug')
                    all_translated.extend(res)
                    cum_in += in_t
                    cum_out += out_t
                    idx += curr_size
                    success = True
                    time.sleep(1)
                    break
                else:
                    log(f"Chunk failed at index {idx}, retrying smaller...", level='debug')
                    time.sleep(2)

            if not success:
                progress.close()
                log("Critical failure: API rejected all chunk sizes.")
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

        log(f"Translation complete: {clean_name}, cost: ${cost:.4f}")

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
        ui.notify(f"Error: {e}", title="Translatarr Error")


# ----------------------------------------------------------
# Monitor
# ----------------------------------------------------------
class TranslatarrMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.last_processed = ""
        self.reload_settings()  # load initial settings

    # -----------------------------------
    # Load settings dynamically
    # -----------------------------------
    def reload_settings(self):
        # Use a fresh Addon instance to avoid cached values
        addon = xbmcaddon.Addon('service.translatarr')

        # Read boolean / string / integer settings
        self.use_notifications = addon.getSettingBool('notify_mode')
        self.show_stats = addon.getSettingBool('show_stats')
        self.chunk_size = int(addon.getSetting('chunk_size') or 100)
        self.source_lang = addon.getSetting('source_lang')
        self.target_lang = addon.getSetting('target_lang')
        self.debug_mode = addon.getSettingBool('debug_mode')  # <-- Added

        # Log for debugging
        log(f"Reloading settings...", level='debug')
        log(f"Settings: notify={self.use_notifications}, show_stats={self.show_stats}, chunk_size={self.chunk_size}, debug={self.debug_mode}", level='debug')

    # -----------------------------------
    # Auto-called when user changes settings in GUI
    # -----------------------------------
    def onSettingsChanged(self):
        log("Settings changed — reloading live.", level='debug')
        self.reload_settings()

    # -----------------------------------
    # Detect new subtitle
    # -----------------------------------
    def check_for_subs(self):
        log("Running check_for_subs()", level='debug')
        if not xbmc.Player().isPlaying():
            log("No video playing. Skipping subtitle check.", level='debug')
            return

        # Get language codes
        _, src_iso = get_lang_params(self.source_lang)
        _, trg_iso = get_lang_params(self.target_lang)
        if trg_iso == "auto":
            trg_iso = "ro"

        target_ext = f".{trg_iso}.srt"

        # Check custom subtitle folder
        custom_dir = xbmcaddon.Addon('service.translatarr').getSetting('sub_folder')
        if not custom_dir or not xbmcvfs.exists(custom_dir):
            log(f"Custom folder invalid or not exists: {custom_dir}", level='debug')
            return

        _, files = xbmcvfs.listdir(custom_dir)
        log(f"Found {len(files)} files in {custom_dir}", level='debug')

        # Get currently playing video filename
        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except:
            log("Failed to get currently playing file.", level='debug')
            return

        valid_files = []
        for f in files:
            f_low = f.lower()
            if video_name.lower() in f_low and f_low.endswith('.srt'):
                if target_ext in f_low:
                    continue  # skip already translated
                match = re.search(r'\.([a-z]{2,3})\.srt$', f_low)
                if match:
                    lang = match.group(1)
                    if lang not in ['en', 'eng', src_iso]:
                        continue
                valid_files.append(f)

        if not valid_files:
            log("No new valid subtitle files found.", level='debug')
            return

        # Sort by newest modified
        valid_files.sort(
            key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(),
            reverse=True
        )

        newest_path = os.path.join(custom_dir, valid_files[0])
        stat = xbmcvfs.Stat(newest_path)
        if stat.st_size() < 500:
            log(f"File too small or incomplete: {newest_path}", level='debug')
            return

        # Compute target path
        save_path, _ = file_manager.get_target_path(newest_path, video_name)
        if xbmcvfs.exists(save_path):
            log(f"Target file already exists: {save_path}", level='debug')
            return

        if newest_path == self.last_processed:
            log(f"File already processed: {newest_path}", level='debug')
            return

        log(f"Processing : {newest_path}")
        self.last_processed = newest_path
        process_subtitles(newest_path, self)
        
# ----------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------
if __name__ == '__main__':

    monitor = TranslatarrMonitor()

    while not monitor.abortRequested():
        monitor.check_for_subs()
        monitor.waitForAbort(5)
