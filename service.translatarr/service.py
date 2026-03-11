# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import os
import time
import math
import sys
import re

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

A4K_SUB_FOLDER = xbmcvfs.translatePath(
    "special://profile/addon_data/service.subtitles.a4ksubtitles/temp/"
)

OPENSUBTITLES_SUB_FOLDER = xbmcvfs.translatePath(
    "special://temp/"
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
# Helpers
# ----------------------------------------------------------
def normalize_name(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    
def vfs_join(folder, file):
    return (folder.rstrip("/\\") + "/" + file.lstrip("/\\")).replace("\\", "/")
    
def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*]+', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.rstrip('. ')
    
def get_best_playing_path(self):
    candidates = [
        xbmc.getInfoLabel("Player.Filenameandpath"),
        xbmc.getInfoLabel("ListItem.FileNameAndPath"),
        xbmc.Player().getPlayingFile(),
    ]

    for path in candidates:
        if not path:
            continue
        path = path.strip()

        # Prefer real playable paths over plugin paths
        if path.startswith(("smb://", "nfs://", "dav://", "ftp://", "sftp://")):
            return path
        if path.startswith("/") or ":\\" in path:
            return path

    return xbmc.Player().getPlayingFile()
    
# ----------------------------------------------------------
# Subtitle Processing with TEMP FILES
# ----------------------------------------------------------
def process_subtitles(original_path, monitor, force_retranslate=False, save_path=None, show_source_immediately=True):
    log(f"process_subtitles called with: {original_path}, force_retranslate={force_retranslate}", "debug", monitor)

    try:
        if not xbmc.Player().isPlaying():
            return False

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return False
            
        session_playing_file = playing_file
            
        # FIX: Get video name safely. If it's a URL, use the Player Title label.
        raw_name = xbmc.getInfoLabel('Player.Title')
        if not raw_name or raw_name == "":
            # Fallback to file name only if it's not a plugin/http source
            if not monitor.is_playing_network_stream():
                raw_name = os.path.splitext(os.path.basename(playing_file))[0]
            else:
                raw_name = "Streamed_Video"

        video_name = raw_name
        log(f"Processing for video: {video_name}", "debug", monitor)

        # Ensure save_path is VFS compatible (forward slashes)
        if save_path is None:
            save_path, clean_name = file_manager.get_target_path(original_path, video_name)
        else:
            # Fix slash direction for Kodi VFS
            save_path = save_path.replace('\\', '/')
            clean_name = os.path.splitext(os.path.basename(save_path))[0]

        temp_path = save_path + ".tmp"

        # Check existing
        if xbmcvfs.exists(save_path) and not force_retranslate:
            log("Subtitle already exists. Loading.", "debug", monitor)
            monitor.load_subtitle_if_new(save_path)
            return True

        initial_chunk = max(10, min(int(monitor.chunk_size or 100), 150))
        model_name = translator.get_model_string()

        progress = None
        try:
            # Use a slightly cleaner title for the UI
            progress = ui.TranslationProgress(model_name=model_name, title=video_name[:30] + "...")
            
            # Read source - xbmcvfs is essential for special:// and plugin://
            # Wait briefly for subtitle to finish writing
            try:
                stat1 = xbmcvfs.Stat(original_path).st_size()
                time.sleep(0.25)
                stat2 = xbmcvfs.Stat(original_path).st_size()

                if stat1 != stat2:
                    log("Subtitle still being written. Skipping this poll.", "debug", monitor)
                    return False
            except Exception:
                pass

            with xbmcvfs.File(original_path, 'r') as f:
                content = f.read()

            if not content:
                log("Source SRT is empty.", "debug", monitor)
                return False

            timestamps, texts = file_manager.parse_srt(content)
            if not timestamps:
                log("Invalid SRT format.", "error", monitor)
                return False
    
            total_lines = len(texts)
            total_chunks_est = math.ceil(total_lines / initial_chunk)
            log(f"Total lines to translate: {total_lines}, estimated chunks: {total_chunks_est}", "debug", monitor)
    
            all_translated = []
            cum_in = 0
            cum_out = 0
            idx = 0
            completed_chunks = 0
            start_time = time.time()
            min_chunk = 5
    
            if getattr(monitor, 'live_translation', False):
                monitor.live_reload_index = 0
    
            # Immediately display new subtitle mid-playback if it's a fresh source
            if show_source_immediately and xbmcvfs.exists(original_path):
                try:
                    monitor.load_subtitle_if_new(original_path)
                    log("Displayed newly detected source subtitle instantly.", "debug", monitor)
                except Exception as e:
                    log(f"Failed to instantly display source subtitle: {e}", "error", monitor)
    
            while idx < total_lines:
                if xbmc.Player().getPlayingFile() != session_playing_file:
                    log("Playback target changed during translation. Aborting current job.", "debug", monitor)
                    return False

                if progress.is_canceled() or not xbmc.Player().isPlaying():
                    log("Playback stopped or user canceled.", "debug", monitor)
                    return False
    
                success = False
                chunk_size = initial_chunk
                retries = 0
    
                while retries < 3 and not success:
                    if xbmc.Player().getPlayingFile() != session_playing_file:
                        log("Playback target changed during retry. Aborting current job.", "debug", monitor)
                        return False
                        
                    curr_size = min(chunk_size, total_lines - idx)
                    log(f"Translating chunk {idx}-{idx+curr_size}, size: {curr_size}", "debug", monitor)
    
                    res, in_t, out_t = translator.translate_batch(texts[idx:idx + curr_size], curr_size)
    
                    if res:
                        all_translated.extend(res)
                        cum_in += in_t
                        cum_out += out_t
                        idx += curr_size
                        completed_chunks += 1
                        success = True
                        percent = int((idx / total_lines) * 100)
                        log(f"Chunk translated. Progress: {percent}%", "debug", monitor)
                        progress.update(
                            percent,
                            src_name=video_name,
                            trg_name=clean_name,
                            chunk_num=completed_chunks,
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
                                    monitor.load_subtitle_if_new(temp_path)
                                except Exception as e:
                                    log(f"Live write failed: {e}", "error", monitor)
                                monitor.live_reload_index += 1
    
                    else:
                        retries += 1
                        chunk_size = max(chunk_size // 2, min_chunk)
                        log(f"Chunk rejected. Retry {retries}. New size {chunk_size}", "debug", monitor)
                        time.sleep(2)
    
                if not success:
                    ui.notify("Critical failure: API rejected all chunk sizes.")
                    log("Aborting translation: all retries failed.", "error", monitor)
                    return False
    
            log("Writing translated SRT TEMP file.", "debug", monitor)
            file_manager.write_srt(temp_path, timestamps, all_translated)
    
            if xbmcvfs.exists(save_path):
                xbmcvfs.delete(save_path)
            
            # Rename is safer than delete+write for file locks
            if xbmcvfs.rename(temp_path, save_path):
                log(f"Successfully saved: {save_path}", "debug", monitor)
                monitor.load_subtitle_if_new(save_path)
                total_time = time.time() - start_time
                cost = translator.calculate_cost(cum_in, cum_out)
                trg_name = monitor.target_lang_name
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
                
            else:
                log("VFS Rename failed.", "error", monitor)
                return False 
            
        finally:
            if progress:
                progress.close()
            
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
        self.reset_playback_state()
        self.reload_settings()
        log("Monitor initialized.", "debug", self)

    def is_playing_network_stream(self):
        playing_file = xbmc.Player().getPlayingFile()
        return bool(playing_file) and playing_file.startswith(
            ("plugin://", "http://", "https://", "dav://", "sftp://")
        )
            
    def onSettingsChanged(self):
        log("Settings changed → reloading monitor.", "debug", self, force=True)
        self.reload_settings()

   
    def load_subtitle_if_new(self, path):
        try:
            stat = xbmcvfs.Stat(path)
            mtime = stat.st_mtime()

            # Skip if same file and same modification time
            if (getattr(self, "last_loaded_subtitle_path", None) == path and
                getattr(self, "last_loaded_subtitle_mtime", 0) == mtime):
                return False

            xbmc.Player().setSubtitles(path)
            self.last_loaded_subtitle_path = path
            self.last_loaded_subtitle_mtime = mtime
            log(f"Loaded subtitle: {path}", "debug", self)
            return True
        except Exception as e:
            log(f"Failed to load subtitle: {e}", "error", self)
            return False
    
    
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
                log(f"Invalid integer setting for '{key}', using fallback {fallback}", "error", self)
                return fallback
    
        # ------------------------------------------------------------
        # Boolean settings
        # ------------------------------------------------------------
        mode = addon.getSetting('translation_mode')
        self.auto_mode = mode == "Auto"
        log(f"Translation mode: {mode}", "debug", self)
        self.debug_mode = safe_bool('debug_mode', False)
        self.use_notifications = safe_bool('notify_mode', True)
        self.show_stats = safe_bool('show_stats', True)
        self.live_translation = safe_bool('live_translation', True)
    
        # ------------------------------------------------------------
        # Numeric / string settings
        # ------------------------------------------------------------
        self.chunk_size = safe_int('chunk_size', 100)
        self.sub_folder = addon.getSetting('sub_folder') or "/storage/emulated/0/Download/"
        
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
        # Kodi-safe folder creation (Android / SMB / special:// compatible)
        if not xbmcvfs.exists(self.sub_folder):
            try:
                success = xbmcvfs.mkdirs(self.sub_folder)
                if success:
                    log(f"Created missing subtitle folder: {self.sub_folder}", "info", self)
                else:
                    log(f"mkdirs returned False for: {self.sub_folder}", "error", self)
            except Exception as e:
                log(f"Exception creating subtitle folder: {self.sub_folder} | Error: {e}", "error", self)
        else:
            log(f"Subtitle folder already exists: {self.sub_folder}", "debug", self)
    
        # ------------------------------------------------------------
        # Final confirmation log
        # ------------------------------------------------------------
        log("Settings reloaded successfully.", "debug", self, force=True)

        settings_snapshot = (
            "Settings snapshot → "
            f"mode={'Auto' if self.auto_mode else 'Manual'}, "
            f"debug={self.debug_mode}, "
            f"notify={self.use_notifications}, "
            f"stats={self.show_stats}, "
            f"live_translation={self.live_translation}, "
            f"chunk_size={self.chunk_size}, "
            f"source_lang={self.source_lang_name} ({self.source_lang_iso}), "
            f"target_lang={self.target_lang_name} ({self.target_lang_iso}), "
            f"provider={self.provider}, "
        )

        # Show only the active provider model
        if self.provider == "OpenAI":
            settings_snapshot += f"openai_model={self.openai_model}"
        else:
            settings_snapshot += f"model={self.model}"

        # Only show subtitle folder in Manual mode
        if not self.auto_mode:
            settings_snapshot += f", subtitle_folder={self.sub_folder}"

        log(settings_snapshot, "debug", self, force=True)

    def reset_playback_state(self):
        self.last_source_state = {}
        self.last_processed_video = None
        self.last_processed_source_path = None
        self.last_processed_source_mtime = 0
        self.last_loaded_subtitle_path = None
        self.last_loaded_subtitle_mtime = 0
        self.live_reload_index = 0
        self.is_busy = False
        self.playback_started_at = 0
        
    
    def onPlaybackStarted(self):
        log("Playback started. Activating polling.", "debug", self)
        self.reset_playback_state()
        self.playback_started_at = time.time()

    def onPlaybackStopped(self):
        log("Playback stopped. Resetting state.", "debug", self)
        self.reset_playback_state()

    def onPlaybackEnded(self):
        log("Playback ended. Resetting state.", "debug", self)
        self.reset_playback_state()

    def check_for_subs(self):
        if not xbmc.Player().isPlaying():
            return
    
        if self.auto_mode:
            self.check_auto_mode_unified()
        else:
            self.check_manual_mode()
  
    # ------------------------------------------------------------
    # check_auto_mode_unified
    # ------------------------------------------------------------
    def check_auto_mode_unified(self):
        if not xbmc.Player().isPlaying() or self.is_busy:
            return

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return

        raw_name = xbmc.getInfoLabel('Player.Title')
        if not raw_name or raw_name == "":
            if not self.is_playing_network_stream():
                video_name = os.path.splitext(os.path.basename(playing_file))[0]
            else:
                video_name = "Streamed_Video"
        else:
            video_name = raw_name

        video_name_normalized = normalize_name(video_name)
        
        trg_variants = get_iso_variants(self.target_lang_name)
        target_exts = [f".{v}.srt" for v in trg_variants]

        folders_to_scan = [OPENSUBTITLES_SUB_FOLDER, A4K_SUB_FOLDER]
        
        if not self.is_playing_network_stream():
            movie_folder = os.path.dirname(playing_file)
            if movie_folder and xbmcvfs.exists(movie_folder):
                folders_to_scan.insert(0, movie_folder)
                
        log(f"Auto scan folders: {folders_to_scan}", "debug", self)
        log(f"Auto current video: {video_name} | normalized: {video_name_normalized}", "debug", self)

        newest_target_file = None
        newest_target_mtime = 0

        newest_source_file = None
        newest_source_mtime = 0

        for folder in folders_to_scan:
            if not folder or not xbmcvfs.exists(folder):
                continue

            try:
                _, files = xbmcvfs.listdir(folder)
                log(f"Scanning folder: {folder} | files: {len(files)}", "debug", self)
            except Exception as e:
                log(f"Failed to list folder {folder}: {e}", "debug", self)
                continue

            for f in files:
                if not f.lower().endswith(".srt"):
                    continue

                f_lower = f.lower()
                f_normalized = normalize_name(f)

                if video_name_normalized not in f_normalized:
                    continue

                full_path = vfs_join(folder, f)

                try:
                    # Detect files still being written
                    size_check = xbmcvfs.Stat(full_path).st_size()
                    time.sleep(0.2)
                    if xbmcvfs.Stat(full_path).st_size() != size_check:
                        log(f"Subtitle still being written: {full_path}", "debug", self)
                        continue

                    stat = xbmcvfs.Stat(full_path)
                    f_mtime = stat.st_mtime()
                    f_size = stat.st_size()
                except Exception:
                    continue

                is_temp_folder = folder in (OPENSUBTITLES_SUB_FOLDER, A4K_SUB_FOLDER)                
                
                if is_temp_folder and getattr(self, "playback_started_at", 0) and f_mtime < self.playback_started_at - 10:
                    log(f"Skipping stale temp subtitle from older session: {full_path}", "debug", self)
                    continue

                if f_size < 50:
                    continue

                # Prefer already translated subtitle if available                
                if any(f_lower.endswith(ext) for ext in target_exts):
                    if f_mtime > newest_target_mtime:
                        newest_target_mtime = f_mtime
                        newest_target_file = full_path
                    continue

                # Otherwise treat as a source subtitle candidate
                if f_mtime > newest_source_mtime:
                    newest_source_mtime = f_mtime
                    newest_source_file = full_path

        # 1. Load newest translated target if one already exists
        if newest_target_file:
            self.load_subtitle_if_new(newest_target_file)

        # 2. Translate newest source only when needed
        last_processed_source_path = getattr(self, "last_processed_source_path", None)
        last_processed_source_mtime = getattr(self, "last_processed_source_mtime", 0)

        source_changed = (
            newest_source_file and (
                newest_source_file != last_processed_source_path
                or newest_source_mtime != last_processed_source_mtime
            )
        )

        target_covers_source = (
            newest_target_file is not None and
            newest_target_mtime >= newest_source_mtime
        )

        if source_changed and not target_covers_source:
            safe_video_name = safe_filename(video_name)
            final_file_name = f"{safe_video_name}.{self.target_lang_iso}.srt"
            save_path = vfs_join(TRANSLATARR_SUB_FOLDER, final_file_name)

            log(f"Newest source subtitle detected: {newest_source_file}", "debug", self)

            self.is_busy = True
            try:
                success = process_subtitles(
                    newest_source_file,
                    self,
                    force_retranslate=True,
                    save_path=save_path,
                    show_source_immediately=True
                )
            finally:
                self.is_busy = False

            if success:
                self.last_processed_source_path = newest_source_file
                self.last_processed_source_mtime = newest_source_mtime
                self.load_subtitle_if_new(save_path)
        elif newest_source_file and newest_target_file and newest_target_mtime >= newest_source_mtime:
            log("Target subtitle already exists and is same-age or newer than source. Skipping translation.", "debug", self)

        if not newest_target_file and not newest_source_file:
            log("No subtitles found in auto mode.", "debug", self)


    # ------------------------------------------------------------
    # check_manual_mode
    # ------------------------------------------------------------
    def check_manual_mode(self):
        log("Polling for subtitles...", "debug", self)

        if not xbmc.Player().isPlaying() or self.is_busy:
            return

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return

        # 1. FIX: Derives video name (Prevents crash on plugins)
        raw_name = xbmc.getInfoLabel('Player.Title')
        if not raw_name or raw_name == "":
            if not self.is_playing_network_stream():
                video_name = os.path.splitext(os.path.basename(playing_file))[0]
            else:
                video_name = "Streamed_Video"
        else:
            video_name = raw_name

        video_name_normalized = normalize_name(video_name)
        
        # Check if we switched movies to clear size cache if necessary
        if getattr(self, 'last_processed_video', None) != video_name:
            self.last_source_state = {}
            self.last_processed_video = video_name

        custom_dir = self.sub_folder
        if not custom_dir or not xbmcvfs.exists(custom_dir):
            return

        # 2. FIX: Unpack listdir properly (it returns dirs, files)
        try:
            _, files = xbmcvfs.listdir(custom_dir)
        except Exception as e:
            log(f"Listdir error: {e}", "error", self)
            return

        src_variants = get_iso_variants(self.source_lang_name)
        trg_variants = get_iso_variants(self.target_lang_name)
        target_exts = [f".{v}.srt" for v in trg_variants]

        source_candidates = []
        target_candidates = []

        for f in files:
            f_lower = f.lower()
            f_normalized = normalize_name(f_lower)

            # Match normalized names
            if video_name_normalized not in f_normalized:
                continue

            is_target = any(f_lower.endswith(ext) for ext in target_exts)
            is_source = any(f_lower.endswith(f".{v}.srt") for v in src_variants)

            if is_target:
                target_candidates.append(f)
            elif is_source:
                source_candidates.append(f)

        # 3. Sorting by mtime (using xbmcvfs)
        def safe_mtime(f):
            try:
                return xbmcvfs.Stat(vfs_join(custom_dir, f)).st_mtime()
            except Exception:
                return 0

        target_candidates.sort(key=safe_mtime, reverse=True)
        source_candidates.sort(key=safe_mtime, reverse=True)

        # Load newest target if already present
        if target_candidates:
            target_path = vfs_join(custom_dir, target_candidates[0])
            try:
                stat = xbmcvfs.Stat(target_path)
                target_mtime = stat.st_mtime()

                if stat.st_size <= 100:
                    log(f"Skipping tiny/broken target subtitle: {target_path}", "debug", self)
                elif (
                    getattr(self, "last_loaded_subtitle_path", None) != target_path
                    or getattr(self, "last_loaded_subtitle_mtime", 0) != target_mtime
                ):
                    self.load_subtitle_if_new(target_path)

            except Exception as e:
                log(f"Failed to stat target subtitle: {e}", "error", self)

        for f in source_candidates:
            full_path = vfs_join(custom_dir, f)
            try:
                # Detect files still being written
                try:
                    size_check = xbmcvfs.Stat(full_path).st_size()
                    time.sleep(0.2)
                    if xbmcvfs.Stat(full_path).st_size() != size_check:
                        log(f"Source subtitle still being written: {full_path}", "debug", self)
                        continue
                except Exception:
                    pass

                stat = xbmcvfs.Stat(full_path)
                size = stat.st_size()
                mtime = stat.st_mtime()

                if getattr(self, "playback_started_at", 0) and mtime < self.playback_started_at - 10:
                    log(f"Skipping stale manual subtitle from older session: {full_path}", "debug", self)
                    continue
                
                if size < 500: 
                    continue
                    
                # Skip translation if an existing target already covers this source
                if target_candidates:
                    newest_target_path = vfs_join(custom_dir, target_candidates[0])
                    try:
                        target_stat = xbmcvfs.Stat(newest_target_path)
                        target_mtime = target_stat.st_mtime()

                        if target_stat.st_size > 100 and target_mtime >= mtime:
                            log(
                                f"Target subtitle already exists and is same-age or newer than source. Skipping translation for: {full_path}",
                                "debug",
                                self
                            )
                            return
                    except Exception as e:
                        log(f"Failed to stat target subtitle for source comparison: {e}", "error", self)

                force_retranslate = False
                last_state = self.last_source_state.get(f.lower())

                if last_state is not None:
                    last_size, last_mtime = last_state
                    if size != last_size or mtime != last_mtime:
                        log("Subtitle changed (size or mtime), forcing retranslation.", "debug", self)
                        force_retranslate = True
                    else:
                        continue

                self.is_busy = True
                try:
                    success = process_subtitles(
                        full_path,
                        self,
                        force_retranslate=force_retranslate,
                        show_source_immediately=True
                    )
                finally:
                    self.is_busy = False

                if success:
                    try:
                        final_stat = xbmcvfs.Stat(full_path)
                        self.last_source_state[f.lower()] = (final_stat.st_size(), final_stat.st_mtime())
                    except Exception:
                        self.last_source_state[f.lower()] = (size, mtime)
                
                return # always stop after trying the newest valid candidate

            except Exception as e:
                log(f"Manual poll processing error: {e}", "error", self)
                return
 

# ----------------------------------------------------------
# ENTRY POINT (Safe for RD / Torbox)
# ----------------------------------------------------------
if __name__ == '__main__':
    window = xbmcgui.Window(10000)

    if window.getProperty("TranslatarrRunning") == "true":
        xbmc.log("[Translatarr] Another instance already running. Exiting.", xbmc.LOGINFO)
        sys.exit()

    window.setProperty("TranslatarrRunning", "true")

    try:
        monitor = TranslatarrMonitor()
        set_global_monitor(monitor)

        while not monitor.abortRequested():
            if xbmc.Player().isPlaying():
                monitor.check_for_subs()
            else:
                log("Playback stopped. Skipping poll.", "debug", monitor)
            
            monitor.waitForAbort(3)  # still responsive to abort

    finally:
        window.clearProperty("TranslatarrRunning")
        xbmc.log("[Translatarr] Instance stopped. Lock released.", xbmc.LOGINFO)
