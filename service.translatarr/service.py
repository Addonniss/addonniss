# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import os
import time
import math
import sys

import translator
import file_manager
import ui
from languages import get_lang_params, get_iso_variants

ADDON_ID = 'service.translatarr'
ADDON = xbmcaddon.Addon(ADDON_ID)

xbmc.log("[Translatarr] SERVICE STARTED", xbmc.LOGINFO)

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------
def log(msg, level='info', monitor=None, force=False):
    debug_enabled = False
    if monitor and hasattr(monitor, 'debug_mode'):
        debug_enabled = monitor.debug_mode

    if force or level != 'debug' or debug_enabled:
        prefix = "[Translatarr]"
        if level == 'debug':
            xbmc.log(f"{prefix}[DEBUG] {msg}", xbmc.LOGINFO)
        elif level == 'error':
            xbmc.log(f"{prefix}[ERROR] {msg}", xbmc.LOGERROR)
        else:
            xbmc.log(f"{prefix} {msg}", xbmc.LOGINFO)


# ----------------------------------------------------------
# CHANGELOG POPUP
# ----------------------------------------------------------
def show_changelog():
    addon_path = ADDON.getAddonInfo('path')
    changelog_path = os.path.join(addon_path, 'changelog.txt')
    log(f"Attempting to show changelog from: {changelog_path}", "debug")

    if xbmcvfs.exists(changelog_path):
        with xbmcvfs.File(changelog_path) as f:
            content = f.read()
            log("Changelog loaded successfully.", "debug")
    else:
        content = "No changelog available."
        log("Changelog not found.", "debug")

    xbmcgui.Dialog().textviewer("Translatarr - Change Log", content)


# ----------------------------------------------------------
# Subtitle Processing with TEMP FILES
# ----------------------------------------------------------
def process_subtitles(original_path, monitor, force_retranslate=False):
    log(f"process_subtitles called with: {original_path}, force_retranslate={force_retranslate}", "debug", monitor)

    try:
        if not xbmc.Player().isPlaying():
            log("Not playing. Abort translation.", "debug", monitor)
            return False

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]
        log(f"Video currently playing: {video_name}", "debug", monitor)

        save_path, clean_name = file_manager.get_target_path(original_path, video_name)
        temp_path = save_path + ".tmp"
        log(f"Calculated target save_path: {save_path}, temp_path: {temp_path}", "debug", monitor)

        if xbmcvfs.exists(save_path) and not force_retranslate:
            log("Target exists and no force flag. Loading existing subtitle.", "debug", monitor)
            xbmc.Player().setSubtitles(save_path)
            return True

        if xbmcvfs.exists(save_path) and force_retranslate:
            log("Source changed → Overwriting existing target translation.", "debug", monitor)

        initial_chunk = max(10, min(int(monitor.chunk_size or 100), 150))
        model_name = translator.get_model_string()
        log(f"Using translation model: {model_name}, chunk size: {initial_chunk}", "debug", monitor)

        progress = ui.TranslationProgress(model_name=model_name, title=video_name)

        with xbmcvfs.File(original_path, 'r') as f:
            content = f.read()

        timestamps, texts = file_manager.parse_srt(content)
        if not timestamps:
            log("Invalid SRT format. Aborting.", "debug", monitor)
            progress.close()
            return False

        total_lines = len(texts)
        total_chunks_est = math.ceil(total_lines / initial_chunk)

        all_translated = []
        cum_in = 0
        cum_out = 0
        idx = 0
        start_time = time.time()
        min_chunk = 5

        while idx < total_lines:

            if progress.is_canceled() or not xbmc.Player().isPlaying():
                progress.close()
                return False

            success = False
            chunk_size = initial_chunk
            retries = 0

            while retries < 3 and not success:
                curr_size = min(chunk_size, total_lines - idx)

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

                    percent = int((idx / total_lines) * 100)

                    progress.update(
                        percent,
                        src_name=video_name,
                        trg_name=clean_name,
                        chunk_num=idx // initial_chunk,
                        total_chunks=total_chunks_est,
                        lines_done=idx,
                        total_lines=total_lines
                    )
                else:
                    retries += 1
                    chunk_size = max(chunk_size // 2, min_chunk)
                    time.sleep(2)

            if not success:
                progress.close()
                ui.notify("Critical failure: API rejected all chunk sizes.")
                return False

        file_manager.write_srt(temp_path, timestamps, all_translated)

        try:
            if xbmcvfs.exists(save_path):
                xbmcvfs.delete(save_path)
            xbmcvfs.rename(temp_path, save_path)
        except Exception as e:
            ui.notify(f"Error renaming temp file: {e}", title="Translatarr Error")
            return False

        xbmc.Player().setSubtitles(save_path)
        progress.close()
        monitor.session_translation_created = True

        total_time = time.time() - start_time
        cost = translator.calculate_cost(cum_in, cum_out)

        trg_name, _ = get_lang_params(monitor.target_lang)

        if monitor.show_stats:
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

        if monitor.use_notifications:
            ui.notify(
                f"✔ Done in {ui.format_time(total_time)} | Cost: ${cost:.4f}",
                title=f"{model_name} → {trg_name}"
            )

        return True

    except Exception as e:
        xbmc.log(f"[Translatarr][ERROR] {e}", xbmc.LOGERROR)
        ui.notify(f"Error: {e}", title="Translatarr Error")
        return False


# ----------------------------------------------------------
# Monitor
# ----------------------------------------------------------
class TranslatarrMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.polling_active = False
        self.last_source_size = {}
        self.is_busy = False
        self.session_translation_created = False
        self.reload_settings()
        log("Monitor initialized.", "debug", self)

    # ✅ PROPER FIX: Kodi calls this automatically when settings change
    def onSettingsChanged(self):
        log("Settings changed → reloading monitor.", "debug", self, force=True)
        self.reload_settings()

    def reload_settings(self):
        addon = xbmcaddon.Addon(ADDON_ID)
        self.debug_mode = addon.getSettingBool('debug_mode')
        self.use_notifications = addon.getSettingBool('notify_mode')
        self.show_stats = addon.getSettingBool('show_stats')
        self.chunk_size = int(addon.getSetting('chunk_size') or 100)
        self.source_lang = addon.getSetting('source_lang')
        self.target_lang = addon.getSetting('target_lang')
        log("Settings reloaded.", "debug", self, force=True)

    def onPlaybackStarted(self):
        self.polling_active = True
        self.last_source_size = {}
        self.session_translation_created = False

    def onPlaybackStopped(self):
        self.polling_active = False

    def onPlaybackEnded(self):
        self.polling_active = False

    def check_for_subs(self):

        if not xbmc.Player().isPlaying():
            return

        if self.is_busy:
            return

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]

        custom_dir = ADDON.getSetting('sub_folder')

        if not custom_dir or not xbmcvfs.exists(custom_dir):
            return

        _, files = xbmcvfs.listdir(custom_dir)
        src_variants = get_iso_variants(self.source_lang)
        trg_variants = get_iso_variants(self.target_lang)
        target_exts = [f".{v}.srt" for v in trg_variants]

        candidate_files = [
            f for f in files
            if f.lower().startswith(video_name.lower())
            and f.lower().endswith('.srt')
            and any(f.lower().endswith(f".{v}.srt") for v in src_variants)
            and not any(f.lower().endswith(ext) for ext in target_exts)
        ]

        candidate_files.sort(
            key=lambda f: xbmcvfs.Stat(os.path.join(custom_dir, f)).st_mtime(),
            reverse=True
        )

        for f in candidate_files:

            full_path = os.path.join(custom_dir, f)
            stat = xbmcvfs.Stat(full_path)

            if stat.st_size() < 500:
                continue

            force_retranslate = False
            last_size = self.last_source_size.get(f.lower())

            if last_size is not None:
                if stat.st_size() != last_size:
                    force_retranslate = True
                else:
                    continue

            try:
                self.is_busy = True
                success = process_subtitles(full_path, self, force_retranslate)
            finally:
                self.is_busy = False

            if success:
                self.last_source_size[f.lower()] = stat.st_size()

            return


# ----------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "show_changelog":
        show_changelog()
    else:
        monitor = TranslatarrMonitor()
        poll_count = 0
        while not monitor.abortRequested():
            poll_count += 1
            log(f"Poll iteration #{poll_count}", "debug", monitor)
            monitor.check_for_subs()
            monitor.waitForAbort(3)
