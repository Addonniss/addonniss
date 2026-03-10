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
    
# ----------------------------------------------------------
# Subtitle Processing with TEMP FILES
# ----------------------------------------------------------
def process_subtitles(original_path, monitor, force_retranslate=False, save_path=None):
    log(f"process_subtitles called with: {original_path}, force_retranslate={force_retranslate}", "debug", monitor)

    try:
        if not xbmc.Player().isPlaying():
            return False

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return False
            
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
            except:
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
            start_time = time.time()
            min_chunk = 5
    
            if getattr(monitor, 'live_translation', False):
                monitor.live_reload_index = 0
    
            # Immediately display new subtitle mid-playback if it's a fresh source
            if not force_retranslate and xbmcvfs.exists(original_path):
                try:
                    monitor.load_subtitle_if_new(original_path)
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
                    progress.close()
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
                monitor.session_translation_created = True
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
        self.known_subtitles = {}
        self.last_temp_folder_mtime = 0   # Track newest temp SRT in special://temp/
        self.last_auto_sub_path = None
        self.last_auto_sub_mtime = 0      # Track last processed auto-detected in-player subtitle
        self.last_processed_source_name = None
        self.last_processed_source_path = None
        self.last_processed_source_mtime = 0  # track last translated source file mtime
        super().__init__()
        self.polling_active = False
        self.last_source_size = {}
        self.is_busy = False
        self.session_translation_created = False
        self.reload_settings()
        log("Monitor initialized.", "debug", self)

    def is_playing_network_stream(self):
        playing_file = xbmc.Player().getPlayingFile()
        return playing_file.startswith(("plugin://", "http", "https", "dav://", "sftp://"))
    
    def onSettingsChanged(self):
        log("Settings changed → reloading monitor.", "debug", self, force=True)
        self.reload_settings()

   
    def load_subtitle_if_new(self, path):
        try:
            stat = xbmcvfs.Stat(path)
            mtime = stat.st_mtime()

            # Skip if same file and same modification time
            if (getattr(self, "last_auto_sub_path", None) == path and
                getattr(self, "last_auto_sub_mtime", 0) == mtime):
                return False

            xbmc.Player().setSubtitles(path)
            self.last_auto_sub_path = path
            self.last_auto_sub_mtime = mtime
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
            f"model={self.model}, "
            f"openai_model={self.openai_model}"
        )

        # Only show subtitle folder in Manual mode
        if not self.auto_mode:
            settings_snapshot += f", subtitle_folder={self.sub_folder}"

        log(settings_snapshot, "debug", self, force=True)

    def onPlaybackStarted(self):
        log("Playback started. Activating polling.", "debug", self)
        self.polling_active = True
        self.last_source_size = {}
        self.session_translation_created = False
        self.last_processed_source_name = None
        self.last_auto_sub_path = None
        self.last_auto_sub_mtime = 0

    def onPlaybackStopped(self):
        log("Playback stopped. Resetting state.", "debug", self)
        self.polling_active = False

    def onPlaybackEnded(self):
        log("Playback ended. Resetting state.", "debug", self)
        self.polling_active = False

    def check_for_subs(self):
        if not xbmc.Player().isPlaying():
            return
    
        if self.auto_mode:
            self.check_auto_mode()
        else:
            self.check_manual_mode()
    # ------------------------------------------------------------
    # check_for_subs_override just a backup/falloff if case I dont use/call check_for_subs_sequential_network()
    # ------------------------------------------------------------    
    #def check_for_subs_override(self):
    #    if not xbmc.Player().isPlaying():
    #        return
    #
    #    if self.is_playing_network_stream():
    #        log("Network stream detected. Running sequential check.", "debug", self)
    #        self.check_for_subs_sequential_network()
    #    else:
    #        # Normal local file logic
    #        if self.auto_mode:
    #            self.check_auto_mode()
    #        else:
    #            self.check_manual_mode()
    #       
    # ------------------------------------------------------------
    # check_for_subs_sequential_network for Real Debrid Torbox
    # ------------------------------------------------------------
    #def check_for_subs_sequential_network(self):
    #   if self.is_busy: return
    #   
    #   # 1. Get safe name
    #   video_name = xbmc.getInfoLabel('Player.Title') or "Streamed_Video"
    #   
    #   # 2. Only scan local temp folders (where A4k/OS save their results)
    #   try:
    #       temp_folder = xbmcvfs.translatePath("special://temp/")
    #       # Unpack listdir properly: returns (dirs, files)
    #       _, files = xbmcvfs.listdir(temp_folder)
    #       srt_files = [vfs_join(temp_folder, f) for f in files if f.lower().endswith(".srt")]
    #       
    #       if not srt_files:
    #           return
    #           
    #       # Get the most recent one
    #       sub_file = max(srt_files, key=lambda x: xbmcvfs.Stat(x).st_mtime())
    #       mtime = xbmcvfs.Stat(sub_file).st_mtime()
    #       size = xbmcvfs.Stat(sub_file).st_size()
    #       if size < 50:
    #           log("Temp subtitle still being written.", "debug", self)
    #           return
    #
    #       if getattr(self, "last_network_sub_mtime", 0) == mtime:
    #           return 
    #
    #       self.last_network_sub_mtime = mtime
    #       log(f"Network stream subtitle detected in temp: {sub_file}", "debug", self)
    #
    #       # 3. Process
    #       final_file_name = f"{video_name}.{self.target_lang_iso}.srt"
    #       save_path = vfs_join(TRANSLATARR_SUB_FOLDER, final_file_name)
    #       
    #       self.is_busy = True
    #       process_subtitles(sub_file, self, save_path=save_path)
    #       self.is_busy = False
    #
    #   except Exception as e:
    #       log(f"Failed sequential network check: {e}", "error", self)
    #       self.is_busy = False
    
    
    # ------------------------------------------------------------
    # check_temp_folder_for_srt
    # ------------------------------------------------------------
    def check_temp_folder_for_srt(self):
        if not xbmc.Player().isPlaying():
            return

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return

        # Use xbmc.getInfoLabel to get a safe name if os.path fails on URIs
        video_name = xbmc.getInfoLabel('Player.Title')
        if not video_name or video_name == "":
             video_name = os.path.splitext(os.path.basename(playing_file))[0] if not self.is_playing_network_stream() else "Streamed_Video"
        video_name_normalized = normalize_name(video_name)

        # -------------------------------------------------
        # Define folders to scan safely
        # -------------------------------------------------
        folders_to_scan = [OPENSUBTITLES_SUB_FOLDER, A4K_SUB_FOLDER]

        # Only add movie folder if it's a real local/network filesystem path
        if not self.is_playing_network_stream():
            # Use os.path ONLY on validated local-style paths
            movie_folder = os.path.dirname(playing_file)
            if movie_folder:
                folders_to_scan.append(movie_folder)

        target_srt_path = None
        newest_source_file = None
        newest_source_mtime = 0

        for folder in folders_to_scan:
            # xbmcvfs.exists is safe for special:// and plugin:// paths
            if not folder or not xbmcvfs.exists(folder):
                continue

            try:
                # listdir returns (directories, files)
                _, files = xbmcvfs.listdir(folder)
                srt_files = [f for f in files if f.lower().endswith(".srt")]
            except Exception as e:
                log(f"Failed to list folder {folder}: {e}", "debug", self)
                continue

            for f in srt_files:
                # Use / for Kodi VFS paths to be cross-platform safe
                full_path = vfs_join(folder, f)
                f_lower = f.lower()
                f_normalized = normalize_name(f)

                if video_name_normalized not in f_normalized:
                    continue

                # Check if this is already our translated file
                if f_lower.endswith(f".{self.target_lang_iso}.srt"):
                    try:
                        f_mtime = xbmcvfs.Stat(full_path).st_mtime()
                        if target_srt_path is None or f_mtime > xbmcvfs.Stat(target_srt_path).st_mtime():
                            target_srt_path = full_path
                    except: continue
                    continue 

                # Otherwise, it's a potential source
                try:
                    stat = xbmcvfs.Stat(full_path)
                    if stat.st_mtime() > newest_source_mtime:
                        newest_source_mtime = stat.st_mtime()
                        newest_source_file = full_path
                except: continue

        # 1️⃣ Load target-language SRT if found
        if target_srt_path:
            self.load_subtitle_if_new(target_srt_path)

        # 2️⃣ Translate newest source if it's newer than what we last processed
        if newest_source_file:
            if newest_source_mtime > getattr(self, "last_processed_source_mtime", 0):
                final_file_name = f"{video_name}.{self.target_lang_iso}.srt"
                save_path = vfs_join(TRANSLATARR_SUB_FOLDER, final_file_name)
                
                log(f"New source detected in temp: {newest_source_file}", "debug", self)
                success = process_subtitles(newest_source_file, self, save_path=save_path)
                
                if success:
                    self.last_processed_source_path = newest_source_file
                    self.last_processed_source_mtime = newest_source_mtime
                    self.load_subtitle_if_new(save_path)

        # -------------------------------------------------
        # 3️⃣ Nothing new found
        # -------------------------------------------------
        if not target_srt_path and not newest_source_file:
            log("No new subtitles found.", "debug", self)
            
    # ------------------------------------------------------------
    # check_auto_mode
    # ------------------------------------------------------------
    def check_auto_mode(self):
        if not xbmc.Player().isPlaying() or self.is_busy:
            return

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return

        # 1. FIX: Safe name extraction (No os.path on URIs)
        is_network = self.is_playing_network_stream()
        raw_name = xbmc.getInfoLabel('Player.Title')
        
        if not raw_name or raw_name == "":
            if not is_network:
                video_name = os.path.splitext(os.path.basename(playing_file))[0]
            else:
                video_name = "Streamed_Video"
        else:
            video_name = raw_name
            
        video_name_normalized = normalize_name(video_name)
        movie_folder = None
        sub_path = None

        # 2. Only check local folders if NOT a network stream
        if not is_network:
            movie_folder = os.path.dirname(playing_file)
            
            if movie_folder and xbmcvfs.exists(movie_folder):
                # Check for existing translation first
                target_in_movie = vfs_join(movie_folder, f"{video_name}.{self.target_lang_iso}.srt")
                if xbmcvfs.exists(target_in_movie):
                    self.load_subtitle_if_new(target_in_movie)
                    # We can return here if we found a perfect match locally
                    return 

                # Otherwise, scan for a source SRT to translate
                try:
                    _, files = xbmcvfs.listdir(movie_folder)
                    for f in files:
                        if f.lower().endswith(".srt") and video_name_normalized in normalize_name(f):
                            sub_path = vfs_join(movie_folder, f)
                            log(f"Found external subtitle in movie folder: {sub_path}", "debug", self)
                            break
                except Exception as e:
                    log(f"Failed to scan movie folder: {e}", "debug", self)

        # 3. Fallback to Temp Folder if no local sub found (Essential for Plugins)
        if not sub_path:
            log("No local/beside-file subtitle found. Checking temp folder...", "debug", self)
            self.check_temp_folder_for_srt()
            return

        # 4. Process the found subtitle
        final_file_name = f"{video_name}.{self.target_lang_iso}.srt"
        save_path = vfs_join(TRANSLATARR_SUB_FOLDER, final_file_name)

        try:
            stat = xbmcvfs.Stat(sub_path)
            current_mtime = stat.st_mtime()
            
            # Optimization check
            if getattr(self, 'last_auto_sub_path', None) == sub_path and current_mtime == self.last_auto_sub_mtime:
                return

            force_retranslate = (getattr(self, 'last_auto_sub_path', None) != sub_path)
            
            self.last_auto_sub_path = sub_path
            self.last_auto_sub_mtime = current_mtime

            self.is_busy = True
            process_subtitles(sub_path, self, force_retranslate=force_retranslate, save_path=save_path)
        finally:
            self.is_busy = False
    
    def check_manual_mode(self):
        log("Polling for subtitles...", "debug", self)

        if not xbmc.Player().isPlaying() or self.is_busy:
            return

        playing_file = xbmc.Player().getPlayingFile()
        if not playing_file:
            return

        # 1. FIX: Sanitized video name (Prevents crash on plugins)
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
            self.last_source_size = {}
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

        candidate_files = []
        for f in files:
            f_lower = f.lower()
            f_normalized = normalize_name(f_lower)
            
            # Match normalized names
            if video_name_normalized not in f_normalized:
                continue
                
            src_ok = any(f_lower.endswith(f".{v}.srt") for v in src_variants)
            trg_ok = not any(f_lower.endswith(ext) for ext in target_exts)
            
            if src_ok and trg_ok:
                candidate_files.append(f)

        # 3. Sorting by mtime (using xbmcvfs)
        def safe_mtime(f):
            try:
                return xbmcvfs.Stat(vfs_join(custom_dir, f)).st_mtime()
            except: return 0
        
        candidate_files.sort(key=safe_mtime, reverse=True)

        for f in candidate_files:
            full_path = vfs_join(custom_dir, f)
            try:
                stat = xbmcvfs.Stat(full_path)
                size = stat.st_size()
                
                if size < 500: continue

                force_retranslate = False
                last_size = self.last_source_size.get(f.lower())

                if last_size is not None and size != last_size:
                    log("Size changed, forcing retranslation.", "debug", self)
                    force_retranslate = True
                elif last_size is not None:
                    continue # Unchanged

                self.is_busy = True
                try:
                    success = process_subtitles(full_path, self, force_retranslate)
                finally:
                    self.is_busy = False

                if success:
                    self.last_source_size[f.lower()] = size
                
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
        _global_monitor = monitor

        while not monitor.abortRequested():
            if xbmc.Player().isPlaying():
                monitor.check_for_subs()
            else:
                log("Playback stopped. Skipping poll.", "debug", monitor)
            
            monitor.waitForAbort(3)  # still responsive to abort

    finally:
        window.clearProperty("TranslatarrRunning")
        xbmc.log("[Translatarr] Instance stopped. Lock released.", xbmc.LOGINFO)
