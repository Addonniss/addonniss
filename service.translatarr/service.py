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

# Special folder for Translatarr translations (profile-safe)
TRANSLATARR_SUB_FOLDER = xbmcvfs.translatePath(
    "special://profile/addon_data/service.translatarr/subtitles/"
)

if not xbmcvfs.exists(TRANSLATARR_SUB_FOLDER):
    xbmcvfs.mkdir(TRANSLATARR_SUB_FOLDER)

xbmc.log("[Translatarr] SERVICE STARTED", xbmc.LOGINFO)

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------
_global_monitor = None  # module-level reference for logging

def set_global_monitor(monitor_instance):
    """Safely set the module-wide global monitor."""
    global _global_monitor
    _global_monitor = monitor_instance

def log(msg, level='info', monitor=None, force=False):
    resolved_monitor = monitor if monitor else _global_monitor
    debug_enabled = getattr(resolved_monitor, 'debug_mode', False)
    if force or level != 'debug' or debug_enabled:
        prefix = "[Translatarr]"
        if level == 'debug':
            xbmc.log(f"{prefix}[DEBUG] {msg}", xbmc.LOGINFO)
        elif level == 'error':
            xbmc.log(f"{prefix}[ERROR] {msg}", xbmc.LOGERROR)
        else:
            xbmc.log(f"{prefix} {msg}", xbmc.LOGINFO)

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

        # If final SRT exists and not forced, just load it
        if xbmcvfs.exists(save_path) and not force_retranslate:
            log("Subtitle already loaded this session. Skipping reload.", "debug", monitor)
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

        if getattr(monitor, 'live_translation', False):
            monitor.live_reload_index = 0

        # Immediately display new subtitle mid-playback if it's a fresh source
        if not force_retranslate and xbmcvfs.exists(original_path):
            try:
                xbmc.Player().setSubtitles(original_path)
                log("Displayed newly detected source subtitle instantly.", "debug", monitor)
            except Exception as e:
                log(f"Failed to instantly display source subtitle: {e}", "error", monitor)

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

                    # Live translation progressive reload
                    if getattr(monitor, 'live_translation', False):
                        percent_done = int((idx / total_lines) * 100)
                        if (monitor.live_reload_index < len(monitor.live_reload_points) and
                            percent_done >= monitor.live_reload_points[monitor.live_reload_index]):
                            try:
                                log(f"Live mode: writing partial SRT at {percent_done}%", "debug", monitor)
                                file_manager.write_srt(temp_path, timestamps[:len(all_translated)], all_translated)
                                xbmc.Player().setSubtitles(temp_path)
                            except Exception as e:
                                log(f"Live write failed: {e}", "error", monitor)
                            monitor.live_reload_index += 1

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

        log("Writing translated SRT TEMP file.", "debug", monitor)
        file_manager.write_srt(temp_path, timestamps, all_translated)

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

    def onSettingsChanged(self):
        log("Settings changed → reloading monitor.", "debug", self, force=True)
        self.reload_settings()

    def reload_settings(self):
        """
        Reload addon settings safely.
        Designed to work with both settings version="1" and version="2".
        Prevents TypeError from getSettingBool() and avoids stale runtime state.
        """
    
        addon = xbmcaddon.Addon(ADDON_ID)
    
        # ------------------------------------------------------------
        # Helper: Safe boolean reader (version-agnostic)
        # ------------------------------------------------------------
        def safe_bool(key, fallback=False):
            """
            Safely read boolean setting.
            Works even if Kodi returns string instead of real bool.
            """
            try:
                return addon.getSettingBool(key)
            except (TypeError, ValueError):
                raw = str(addon.getSetting(key) or '').strip().lower()
                if raw in ('true', '1', 'yes', 'on'):
                    return True
                elif raw in ('false', '0', 'no', 'off', ''):
                    return False
                return fallback
    
        # ------------------------------------------------------------
        # Helper: Safe integer reader
        # ------------------------------------------------------------
        def safe_int(key, fallback):
            """
            Safely read integer setting.
            Prevents crashes if setting is empty or corrupted.
            """
            try:
                return int(addon.getSetting(key))
            except (TypeError, ValueError):
                log(f"Invalid integer setting for '{key}', using fallback {fallback}", "warning", self)
                return fallback
    
        # ------------------------------------------------------------
        # Boolean settings
        # ------------------------------------------------------------
        self.auto_mode = safe_bool('auto_mode', True)
        self.debug_mode = safe_bool('debug_mode', False)
        self.use_notifications = safe_bool('notify_mode', True)
        self.show_stats = safe_bool('show_stats', True)
        self.live_translation = safe_bool('live_translation', False)
    
        # ------------------------------------------------------------
        # Numeric / string settings
        # ------------------------------------------------------------
        self.chunk_size = safe_int('chunk_size', 100)
        self.sub_folder = addon.getSetting('sub_folder') or "/storage/emulated/0/Download/sub/"
        # ------------------------------------------------------------
        # Language settings (new select-aware, ISO-respecting)
        # ------------------------------------------------------------
        raw_source = addon.getSetting('source_lang') or "Romanian"
        raw_target = addon.getSetting('target_lang') or "Romanian"
        
        # Convert to full name and ISO
        self.source_lang_name, self.source_lang_iso = get_lang_params(raw_source)
        self.target_lang_name, self.target_lang_iso = get_lang_params(raw_target)
        
        log(
            f"Languages loaded → "
            f"source: {self.source_lang_name} ({self.source_lang_iso}), "
            f"target: {self.target_lang_name} ({self.target_lang_iso})",
            "debug",
            self,
            force=True
        )
        
        self.provider = addon.getSetting('provider')
        self.model = addon.getSetting('model')
        self.openai_model = addon.getSetting('openai_model')
        
        log(
            f"AI snapshot → provider={self.provider}, model={self.model}, openai_model={self.openai_model}",
            "debug",
            self,
            force=True
        )
    
        # ------------------------------------------------------------
        # Live translation runtime state handling
        # Prevent stale values when feature is disabled
        # ------------------------------------------------------------
        if self.live_translation:
            self.live_reload_points = [5, 15, 35, 60, 85]
            self.live_reload_index = 0
            log("Live translation enabled.", "debug", self)
        else:
            self.live_reload_points = []
            self.live_reload_index = 0
            log("Live translation disabled. Runtime state cleared.", "debug", self)
    
        # ------------------------------------------------------------
        # Validate subtitle folder path
        # Auto-create if missing (Android-safe)
        # ------------------------------------------------------------
        if not os.path.exists(self.sub_folder):
            try:
                os.makedirs(self.sub_folder, exist_ok=True)
                log(f"Created missing subtitle folder: {self.sub_folder}", "info", self)
            except Exception as e:
                log(f"Failed to create subtitle folder: {self.sub_folder} | Error: {e}", "error", self)
    
        # ------------------------------------------------------------
        # Final confirmation log
        # ------------------------------------------------------------
        log("Settings reloaded successfully.", "debug", self, force=True)
        log(
            f"Settings snapshot → "
            f"debug={self.debug_mode}, "
            f"notify={self.use_notifications}, "
            f"stats={self.show_stats}, "
            f"live={self.live_translation}, "
            f"chunk={self.chunk_size}, "
            f"src={self.source_lang_name} ({self.source_lang_iso}), "
            f"trg={self.target_lang_name} ({self.target_lang_iso}), "
            f"folder={self.sub_folder}",
            "debug",
            self,
            force=True
        )

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
    
        if self.auto_mode:
            self.check_auto_mode()
        else:
            self.check_manual_mode()
            
    def check_auto_mode(self):
        """
        AUTO MODE: Intercept currently loaded subtitle from any addon
        and process translation, saving in Translatarr profile folder.
        """
        if not xbmc.Player().isPlaying() or self.is_busy:
            return
    
        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]
    
        # Get currently loaded subtitles in player
        sub_path = xbmc.Player().getSubtitles()
        if not sub_path:
            log("No subtitle currently loaded in player.", "debug", self)
            return
    
        sub_file_name = os.path.basename(sub_path)
        sub_ext = os.path.splitext(sub_file_name)[1].lower()
        if sub_ext != ".srt":
            log(f"Subtitle is not .srt ({sub_ext}), skipping.", "debug", self)
            return
    
        # Determine target filename using ISO convention
        source_iso = self.source_lang_iso or "eng"
        target_iso = self.target_lang_iso or "ro"
    
        final_file_name = f"{video_name}.{target_iso}.srt"
        save_path = os.path.join(TRANSLATARR_SUB_FOLDER, final_file_name)
        temp_path = save_path + ".tmp"
    
        # Check if translation already exists
        force_retranslate = False
        if xbmcvfs.exists(save_path):
            stat = xbmcvfs.Stat(save_path)
            last_size = self.last_source_size.get(sub_file_name.lower())
            if last_size == stat.st_size():
                log("Translated SRT already exists and unchanged. Skipping.", "debug", self)
                return
            else:
                force_retranslate = True
    
        try:
            self.is_busy = True
            log(f"Translating subtitle from auto-detected source: {sub_file_name}", "debug", self)
    
            success = process_subtitles(sub_path, self, force_retranslate)
    
            if success:
                stat = xbmcvfs.Stat(save_path)
                self.last_source_size[sub_file_name.lower()] = stat.st_size()
                log(f"Translation saved: {save_path}", "debug", self)
    
        finally:
            self.is_busy = False
    
    def check_manual_mode(self):
        log("Polling for subtitles...", "debug", self)

        if not xbmc.Player().isPlaying():
            log("Playback not active. Skipping check.", "debug", self)
            return

        if self.is_busy:
            log("Translation in progress. Skipping check.", "debug", self)
            return

        playing_file = xbmc.Player().getPlayingFile()
        video_name = os.path.splitext(os.path.basename(playing_file))[0]
        log(f"Current video: {video_name}", "debug", self)

        custom_dir = self.sub_folder
        log(f"Custom subtitles folder: {custom_dir}", "debug", self)

        if not custom_dir or not xbmcvfs.exists(custom_dir):
            log("Sub folder missing or inaccessible. Abort check.", "debug", self)
            return

        _, files = xbmcvfs.listdir(custom_dir)
        src_variants = get_iso_variants(self.source_lang_name)
        trg_variants = get_iso_variants(self.target_lang_name)
        target_exts = [f".{v}.srt" for v in trg_variants]

        # Candidate detection with ISO + name + target ext filters
        candidate_files = []
        for f in files:
            f_lower = f.lower()
            base_ok = video_name.lower() in f_lower
            src_ok = any(f_lower.endswith(f".{v}.srt") for v in src_variants)
            trg_ok = not any(f_lower.endswith(ext) for ext in target_exts)
            if base_ok and src_ok and trg_ok:
                candidate_files.append(f)
                log(f"Candidate subtitle detected: {f}", "debug", self)

        candidate_files.sort(
            key=lambda f: xbmcvfs.Stat(os.path.join(custom_dir, f)).st_mtime(),
            reverse=True
        )

        for f in candidate_files:
            full_path = os.path.join(custom_dir, f)
            stat = xbmcvfs.Stat(full_path)
            log(f"File stats -> size: {stat.st_size()} bytes, mtime: {stat.st_mtime()}", "debug", self)

            if stat.st_size() < 500:
                log(f"File too small (possibly incomplete). Will check next poll: {f}", "debug", self)
                continue

            # Check if source changed in size → force retranslation
            force_retranslate = False
            last_size = self.last_source_size.get(f.lower())
            if last_size is not None:
                if stat.st_size() != last_size:
                    log(f"File size changed: {last_size} → {stat.st_size()}. Forcing retranslation.", "debug", self)
                    force_retranslate = True
                else:
                    log("File unchanged since last check. Skipping.", "debug", self)
                    continue

            try:
                self.is_busy = True
                log(f"Processing subtitle: {f}", "debug", self)
                success = process_subtitles(full_path, self, force_retranslate)
            finally:
                self.is_busy = False

            if success:
                self.last_source_size[f.lower()] = stat.st_size()
                log("Stored source metadata snapshot.", "debug", self)

            return  # only process one new file per poll

# ----------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------
if __name__ == '__main__':
    window = xbmcgui.Window(10000)

    if window.getProperty("TranslatarrRunning") == "true":
        xbmc.log("[Translatarr] Another instance already running. Exiting.", xbmc.LOGINFO)
        sys.exit()

    window.setProperty("TranslatarrRunning", "true")

    try:
        monitor = TranslatarrMonitor()
        _global_monitor = monitor

        poll_count = 0
        while not monitor.abortRequested():
            poll_count += 1
            log(f"Poll iteration #{poll_count}", "debug", monitor)
            monitor.check_for_subs()
            monitor.waitForAbort(3)

    finally:
        window.clearProperty("TranslatarrRunning")
        xbmc.log("[Translatarr] Instance stopped. Lock released.", xbmc.LOGINFO)
