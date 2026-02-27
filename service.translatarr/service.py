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

# –––––––––––––––––––––––––––––
# Logging
# –––––––––––––––––––––––––––––

# Global monitor reference used by log() when no monitor is passed explicitly.
# Set to the active TranslatarrMonitor instance once created.
_global_monitor = None

def log(msg, level='info', monitor=None, force=False):
    # Resolve which monitor to use: prefer the explicitly passed one,
    # fall back to the global reference so debug_mode is always honoured.
    resolved_monitor = monitor if monitor is not None else _global_monitor
    debug_enabled = False
    if resolved_monitor and hasattr(resolved_monitor, 'debug_mode'):
        debug_enabled = resolved_monitor.debug_mode

    if force or level != 'debug' or debug_enabled:
        prefix = "[Translatarr]"
        if level == 'debug':
            xbmc.log(f"{prefix}[DEBUG] {msg}", xbmc.LOGINFO)
        elif level == 'error':
            xbmc.log(f"{prefix}[ERROR] {msg}", xbmc.LOGERROR)
        else:
            xbmc.log(f"{prefix} {msg}", xbmc.LOGINFO)

# –––––––––––––––––––––––––––––
# CHANGELOG POPUP
# –––––––––––––––––––––––––––––

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

# –––––––––––––––––––––––––––––
# Subtitle Processing with TEMP FILES
# –––––––––––––––––––––––––––––

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
        temp_path = save_path + ".tmp"  # <-- temp file path
        log(f"Calculated target save_path: {save_path}, temp_path: {temp_path}", "debug", monitor)

        # If final SRT exists and not forced, just load it
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
        log(f"Starting translation for: {original_path}", "debug", monitor)

        with xbmcvfs.File(original_path, 'r') as f:
            content = f.read()
            log(f"Read source SRT, size: {len(content)} bytes", "debug", monitor)

        timestamps, texts = file_manager.parse_srt(content)
        if not timestamps:
            log("Invalid SRT format. Aborting.", "debug", monitor)
            progress.close()
            return False

        total_lines = len(texts)
        total_chunks_est = math.ceil(total_lines / initial_chunk)
        log(f"Total lines to translate: {total_lines}, estimated chunks: {total_chunks_est}", "debug", monitor)

        all_translated = []
        cum_in = 0
        cum_out = 0
        idx = 0
        start_time = time.time()
        min_chunk = 5

        while idx < total_lines:
            if progress.is_canceled() or not xbmc.Player().isPlaying():
                log("Playback stopped or user canceled.", "debug", monitor)
                progress.close()
                return False

            success = False
            chunk_size = initial_chunk
            retries = 0

            while retries < 3 and not success:
                curr_size = min(chunk_size, total_lines - idx)
                log(f"Translating chunk {idx}-{idx+curr_size}, size: {curr_size}", "debug", monitor)

                res, in_t, out_t = translator.translate_batch(texts[idx:idx + curr_size], curr_size)

                if res:
                    all_translated.extend(res)
                    cum_in += in_t
                    cum_out += out_t
                    idx += curr_size
                    success = True
                    percent = int((idx / total_lines) * 100)
                    log(f"Chunk translated. Progress: {percent}%", "debug", monitor)
                    progress.update(
                        percent,
                        src_name=video_name,
                        trg_name=clean_name,
                        chunk_num=idx // initial_chunk,
                        total_chunks=total_chunks_est,
                        lines_done=idx,
                        total_lines=total_lines
                    )
                    
                    # ----------------------------------------------------------
                    # NEW: Live Translation Write
                    # If enabled, write partial translated SRT after each chunk.
                    # We NEVER let AI touch timestamps.
                    # We slice timestamps to match translated lines only.
                    # This guarantees valid SRT structure at all times.
                    # ----------------------------------------------------------
                    if monitor.live_translation:
                        try:
                            log("Live mode: writing partial SRT.", "debug", monitor)

                            file_manager.write_srt(
                                temp_path,
                                timestamps[:len(all_translated)],
                                all_translated
                            )

                            # Load partial subtitles during playback
                            xbmc.Player().setSubtitles(temp_path)

                        except Exception as e:
                            log(f"Live write failed: {e}", "error", monitor)
                            
                else:
                    retries += 1
                    chunk_size = max(chunk_size // 2, min_chunk)
                    log(f"Chunk rejected. Retry {retries}. New size {chunk_size}", "debug", monitor)
                    time.sleep(2)

            if not success:
                progress.close()
                ui.notify("Critical failure: API rejected all chunk sizes.")
                log("Aborting translation: all retries failed.", "error", monitor)
                return False

        # Write final translation to TEMP file first
        log("Writing translated SRT TEMP file.", "debug", monitor)
        file_manager.write_srt(temp_path, timestamps, all_translated)

        # Once done, rename temp to final
        try:
            if xbmcvfs.exists(save_path):
                xbmcvfs.delete(save_path)
            xbmcvfs.rename(temp_path, save_path)
            log(f"Temp file renamed to final SRT: {save_path}", "debug", monitor)
        except Exception as e:
            log(f"Failed to rename temp file: {e}", "error", monitor)
            ui.notify(f"Error renaming temp file: {e}", title="Translatarr Error")
            return False

        xbmc.Player().setSubtitles(save_path)
        progress.close()
        monitor.session_translation_created = True

        total_time = time.time() - start_time
        cost = translator.calculate_cost(cum_in, cum_out)
        trg_name, _ = get_lang_params(monitor.target_lang)
        log(f"Translation finished. Total time: {total_time:.2f}s, cost: ${cost:.4f}", "debug", monitor)

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

# –––––––––––––––––––––––––––––
# Monitor
# –––––––––––––––––––––––––––––

class TranslatarrMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.polling_active = False
        self.last_source_size = {}
        self.is_busy = False
        self.session_translation_created = False
        self.reload_settings()
        log("Monitor initialized.", "debug", self)

    # ----------------------------------------------------------
    # Dynamic Settings Reload (no Kodi restart required)
    # ----------------------------------------------------------
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
        # ----------------------------------------------------------
        # NEW: Live Translation mode (progressive SRT writing)
        # When enabled, subtitles are written after each translated chunk
        # instead of waiting for full translation completion.
        # ----------------------------------------------------------
        self.live_translation = addon.getSettingBool('live_translation')

        # ----------------------------------------------------------
        # NEW CHANGE:
        # Centralize sub_folder inside monitor settings
        # This ensures consistent dynamic reload behavior and
        # removes direct ADDON access from polling logic.
        # ----------------------------------------------------------
        self.sub_folder = addon.getSetting('sub_folder')

        log("Settings reloaded.", "debug", self, force=True)

    def onPlaybackStarted(self):
        log("Playback started. Activating polling.", "debug", self)
        self.polling_active = True
        self.last_source_size = {}
        self.session_translation_created = False

    def onPlaybackStopped(self):
        log("Playback stopped. Resetting state.", "debug", self)
        self.polling_active = False

    def onPlaybackEnded(self):
        log("Playback ended. Resetting state.", "debug", self)
        self.polling_active = False

    def check_for_subs(self):
        log("Polling for subtitles...", "debug", self)

        if not xbmc.Player().isPlaying():
            if self.debug_mode:
                log("Playback not active. Skipping check.", "debug", self)
            return

        if self.is_busy:
            log("Translation in progress. Skipping check.", "debug", self)
            return

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]
        log(f"Current video: {video_name}", "debug", self)

        # ----------------------------------------------------------
        # UPDATED: use centralized self.sub_folder
        # ----------------------------------------------------------
        custom_dir = self.sub_folder
        log(f"Custom subtitles folder: {custom_dir}", "debug", self)

        if not custom_dir or not xbmcvfs.exists(custom_dir):
            log("Sub folder missing or inaccessible. Abort check.", "debug", self)
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

        log(f"Found {len(candidate_files)} candidate source SRT(s) for current video.", "debug", self)

        for f in candidate_files:
            full_path = os.path.join(custom_dir, f)
            stat = xbmcvfs.Stat(full_path)
            log(f"File stats -> size: {stat.st_size()} bytes, mtime: {stat.st_mtime()}", "debug", self)

            if stat.st_size() < 500:
                log(f"File too small (possibly incomplete). Will check next poll: {f}", "debug", self)
                continue

            force_retranslate = False
            last_size = self.last_source_size.get(f.lower())
            if last_size is not None:
                if stat.st_size() != last_size:
                    log(f"File size changed: {last_size} → {stat.st_size()}. Forcing retranslation.", "debug", self)
                    force_retranslate = True
                else:
                    log("File unchanged since last check. Skipping.", "debug", self)
                    continue

            self.last_source_size[f.lower()] = stat.st_size()
            log("Stored source metadata snapshot (pre-process).", "debug", self)

            try:
                self.is_busy = True
                log(f"Processing subtitle: {f}", "debug", self)
                success = process_subtitles(full_path, self, force_retranslate)
            finally:
                self.is_busy = False

            if not success:
                if last_size is None:
                    del self.last_source_size[f.lower()]
                else:
                    self.last_source_size[f.lower()] = last_size
                log("Reverted source metadata snapshot due to failure.", "debug", self)

            return

# –––––––––––––––––––––––––––––
# ENTRY POINT
# –––––––––––––––––––––––––––––

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "show_changelog":
        show_changelog()
    else:
        monitor = TranslatarrMonitor()

        # ----------------------------------------------------------
        # FIX: ensure global debug fallback works properly
        # ----------------------------------------------------------
        global _global_monitor
        _global_monitor = monitor

        poll_count = 0
        while not monitor.abortRequested():
            poll_count += 1
            log(f"Poll iteration #{poll_count}", "debug", monitor)

            if monitor.polling_active:
                monitor.check_for_subs()
                monitor.waitForAbort(3)
            else:
                monitor.waitForAbort(15)


