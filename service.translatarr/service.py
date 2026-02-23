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


def log(msg):
    xbmc.log(f"[Translatarr] {msg}", xbmc.LOGINFO)


# ----------------------------------------------------------
# Subtitle Processing
# ----------------------------------------------------------
def process_subtitles(original_path):
    try:
        addon = xbmcaddon.Addon(ADDON_ID)

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]

        save_path, clean_name = file_manager.get_target_path(original_path, video_name)

        # Skip if already translated
        if xbmcvfs.exists(save_path):
            xbmc.Player().setSubtitles(save_path)
            return

        # ----------------------------
        # Read settings ONCE per translation
        # ----------------------------
        use_notifications = addon.getSettingBool('notify_mode')
        show_stats = addon.getSettingBool('show_stats')
        initial_chunk = max(10, min(int(addon.getSetting('chunk_size') or 100), 150))

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

            # Adaptive chunking
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

        # Final 100%
        progress.update(
            100,
            os.path.basename(original_path),
            clean_name,
            total_chunks_est,
            total_chunks_est,
            total_lines,
            total_lines
        )

        # Write translated file
        file_manager.write_srt(save_path, timestamps, all_translated)
        xbmc.Player().setSubtitles(save_path)
        progress.close()

        total_time = time.time() - start_time
        cost = translator.calculate_cost(cum_in, cum_out)
        trg_name, _ = get_lang_params(addon.getSetting('target_lang'))

        # ----------------------------
        # Stats popup
        # ----------------------------
        if show_stats:
            ui.show_stats_box(
                os.path.basename(original_path),
                clean_name,
                trg_name,
                cost,
                (cum_in + cum_out),
                total_chunks_est,
                initial_chunk,
                model_name,
                total_time
            )

        # ----------------------------
        # Simple notification
        # ----------------------------
        if use_notifications:
            ui.notify(
                f"✔ Done in {int(total_time)}s | ${cost:.4f}",
                title=f"{model_name} → {trg_name}"
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

        addon = xbmcaddon.Addon(ADDON_ID)

        _, src_iso = get_lang_params(addon.getSetting('source_lang'))
        _, trg_iso = get_lang_params(addon.getSetting('target_lang'))

        if trg_iso == "auto":
            trg_iso = "ro"

        target_ext = f".{trg_iso}.srt"

        try:
            playing_file = xbmc.Player().getPlayingFile()
            video_name = os.path.splitext(os.path.basename(playing_file))[0]
        except:
            return

        custom_dir = addon.getSetting('sub_folder')
        if not custom_dir or not xbmcvfs.exists(custom_dir):
            return

        _, files = xbmcvfs.listdir(custom_dir)
        valid_files = []

        for f in files:
            f_low = f.lower()

            if video_name.lower() in f_low and f_low.endswith('.srt'):

                # Skip already translated target language
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

        # Sort newest first
        valid_files.sort(
            key=lambda x: xbmcvfs.Stat(os.path.join(custom_dir, x)).st_mtime(),
            reverse=True
        )

        newest_path = os.path.join(custom_dir, valid_files[0])
        stat = xbmcvfs.Stat(newest_path)

        # Skip tiny/incomplete files
        if stat.st_size() < 500:
            return

        # Skip if translation already exists
        save_path, _ = file_manager.get_target_path(newest_path, video_name)
        if xbmcvfs.exists(save_path):
            return

        # Prevent immediate re-trigger
        if newest_path == self.last_processed:
            return

        self.last_processed = newest_path
        process_subtitles(newest_path)


# ----------------------------------------------------------
# Entry
# ----------------------------------------------------------
if __name__ == '__main__':

    monitor = TranslatarrMonitor()

    while not monitor.abortRequested():
        monitor.check_for_subs()

        if monitor.waitForAbort(5):
            break
