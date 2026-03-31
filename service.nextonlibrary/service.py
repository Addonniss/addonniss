# -*- coding: utf-8 -*-
import json
import re
from platform import machine

import xbmc
import xbmcaddon
import xbmcgui

ADDON_ID = "service.nextonlibrary"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo("path")
BUTTON_CONTROL_ID = 3012
CLOSE_BUTTON_CONTROL_ID = 3013
ACTION_SELECT_ITEM = 7
ACTION_PLAYER_STOP = 13
ACTION_NAV_BACK = 92
ACTION_MOUSE_MOVE = 107
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_DOUBLE_CLICK = 103
ACTION_MOUSE_DRAG = 106
OS_MACHINE = machine()


def localize(string_id):
    return ADDON.getLocalizedString(string_id)


def log(message, level=xbmc.LOGINFO, force=False):
    debug_enabled = get_setting_bool("debug_logging")
    if not force and level == xbmc.LOGDEBUG and not debug_enabled:
        return
    if level == xbmc.LOGDEBUG and debug_enabled:
        level = xbmc.LOGINFO
    xbmc.log("[NextOnLibrary] %s" % message, level)


def get_setting_bool(setting_id):
    try:
        return ADDON.getSettingBool(setting_id)
    except AttributeError:
        return ADDON.getSetting(setting_id).lower() == "true"


def get_setting_int(setting_id, default=0, minimum=None, maximum=None):
    try:
        value = ADDON.getSettingInt(setting_id)
    except AttributeError:
        raw_value = ADDON.getSetting(setting_id)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def get_setting_string(setting_id, default=""):
    try:
        value = ADDON.getSettingString(setting_id)
    except AttributeError:
        value = ADDON.getSetting(setting_id)
    return value if value not in (None, "") else default


def is_meaningful_gap(current_value, previous_value, minimum_gap):
    return (current_value - previous_value) >= minimum_gap


def jsonrpc(method, params=None, log_errors=True):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        payload["params"] = params

    try:
        raw_result = xbmc.executeJSONRPC(json.dumps(payload))
        result = json.loads(raw_result)
    except Exception as exc:
        log("JSON-RPC failure for %s: %s" % (method, exc), xbmc.LOGERROR, force=True)
        return {}

    if result.get("error") and log_errors:
        log("JSON-RPC error for %s: %s" % (method, result["error"]), xbmc.LOGDEBUG)
    return result


class NextOnLibraryOverlay(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        if OS_MACHINE[0:5] == 'armv7':
            xbmcgui.WindowXMLDialog.__init__(self)
        else:
            xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.service = None

    def onInit(self):  # pylint: disable=invalid-name
        try:
            self.getControl(BUTTON_CONTROL_ID).setLabel(self.service.get_overlay_label())
            self.setFocusId(BUTTON_CONTROL_ID)
            self.service.configure_overlay_controls(self)
        except RuntimeError:
            pass

    def onClick(self, control_id):  # pylint: disable=invalid-name
        if control_id == BUTTON_CONTROL_ID and self.service:
            self.service.handle_overlay_action()
        elif control_id == CLOSE_BUTTON_CONTROL_ID and self.service:
            self.service.dismiss_overlay()

    def onAction(self, action):  # pylint: disable=invalid-name
        action_id = action.getId()
        if action_id == ACTION_SELECT_ITEM and self.service:
            focused_id = self.getFocusId()
            if focused_id == BUTTON_CONTROL_ID:
                self.service.handle_overlay_action()
            elif focused_id == CLOSE_BUTTON_CONTROL_ID:
                self.service.dismiss_overlay()
        elif action_id in (ACTION_MOUSE_MOVE, ACTION_MOUSE_LEFT_CLICK, ACTION_MOUSE_DOUBLE_CLICK, ACTION_MOUSE_DRAG):
            return
        elif self.service:
            user_initiated = action_id != ACTION_PLAYER_STOP
            self.service.dismiss_overlay(user_initiated=user_initiated)
        else:
            self.close()


class NextOnLibraryPlayer(xbmc.Player):
    def __init__(self, service):
        self.service = service
        xbmc.Player.__init__(self)

    if callable(getattr(xbmc.Player, "onAVStarted", None)):
        def onAVStarted(self):  # pylint: disable=invalid-name
            self.service.handle_playback_started()

        def onPlayBackStarted(self):  # pylint: disable=invalid-name
            pass
    else:
        def onPlayBackStarted(self):  # pylint: disable=invalid-name
            self.service.handle_playback_started()

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        self.service.reset_session()

    def onPlayBackEnded(self):  # pylint: disable=invalid-name
        self.service.reset_session()

    def onPlayBackError(self):  # pylint: disable=invalid-name
        self.service.reset_session()


class NextOnLibraryService(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.player = NextOnLibraryPlayer(self)
        self.overlay = None
        self.reset_session()

    def reset_session(self):
        self.close_overlay()
        self.current_file = ""
        self.current_episode = None
        self.next_episode = None
        self.chapter_starts = []
        self.chapter_percents = []
        self.skip_intro_target = None
        self.skip_intro_start = None
        self.skip_intro_prompted = False
        self.skip_intro_overlay_shown_at = None
        self.last_logged_skip_intro_target = None
        self.trigger_time = None
        self.next_trigger_source = None
        self.next_overlay_dismissed = False
        self.prompted = False
        self.overlay_action = None

    def close_overlay(self):
        if not self.overlay:
            self.overlay_action = None
            self.skip_intro_overlay_shown_at = None
            return
        try:
            self.overlay.close()
        except RuntimeError:
            pass
        self.overlay = None
        self.overlay_action = None
        self.skip_intro_overlay_shown_at = None

    def handle_playback_started(self):
        self.close_overlay()
        self.bootstrap_session()

    def run(self):
        log("Service started", force=True)

        while not self.abortRequested():
            if self.waitForAbort(1):
                break

            if not get_setting_bool("service_enabled"):
                if self.current_file:
                    log("Service disabled, clearing current session", xbmc.LOGDEBUG)
                    self.reset_session()
                continue

            if not self.player.isPlayingVideo():
                if self.current_file:
                    log("Playback stopped outside callbacks, clearing session", xbmc.LOGDEBUG)
                    self.reset_session()
                continue

            if not self.current_episode:
                self.bootstrap_session()
                continue

            if self.prompted:
                continue

            if not self.session_matches_current_playback():
                self.bootstrap_session()
                continue

            try:
                current_time = self.player.getTime()
                total_time = self.player.getTotalTime()
            except RuntimeError:
                continue

            if total_time <= 0:
                continue

            self.refresh_chapter_markers(total_time)

            if self.handle_skip_intro(current_time, total_time):
                continue

            if self.trigger_time is None:
                self.trigger_time = self.calculate_trigger_time(total_time)
                log("Using trigger time %.2f seconds" % self.trigger_time, xbmc.LOGDEBUG)

            if current_time < self.trigger_time:
                continue

            self.prompt_for_next_episode()

        log("Service stopped", force=True)

    def bootstrap_session(self):
        if not get_setting_bool("service_enabled"):
            return

        if not self.player.isPlayingVideo():
            return

        try:
            current_file = self.player.getPlayingFile()
        except RuntimeError:
            return

        item = self.get_current_episode()
        if not item:
            if self.current_file:
                log("Current playback is not a library episode, clearing session", xbmc.LOGDEBUG)
            self.reset_session()
            return

        if self.current_file == current_file and self.current_episode:
            return

        self.close_overlay()

        self.current_file = current_file
        self.current_episode = item
        self.next_episode = None
        self.chapter_starts, self.chapter_percents = self.get_chapter_markers()
        self.skip_intro_target = None
        self.skip_intro_start = None
        self.skip_intro_prompted = False
        self.trigger_time = None
        self.next_trigger_source = None
        self.next_overlay_dismissed = False
        self.prompted = False
        self.overlay_action = None

        if self.chapter_starts:
            chapter_info = ", ".join(["%.2f" % value for value in self.chapter_starts])
        elif self.chapter_percents:
            chapter_info = "percents=%s" % ", ".join(["%.2f" % value for value in self.chapter_percents])
        else:
            chapter_info = "none"
        log(
            "Tracking %s S%02dE%02d, chapters=%s" % (
                item.get("showtitle", ""),
                int(item.get("season", 0)),
                int(item.get("episode", 0)),
                chapter_info,
            ),
            xbmc.LOGDEBUG,
        )

    def session_matches_current_playback(self):
        try:
            current_file = self.player.getPlayingFile()
        except RuntimeError:
            return False
        return bool(self.current_file and current_file == self.current_file)

    def get_active_player_id(self):
        result = jsonrpc("Player.GetActivePlayers")
        players = result.get("result", [])
        for player in players:
            if player.get("type") == "video":
                return player.get("playerid")
        return None

    def get_current_episode(self):
        player_id = self.get_active_player_id()
        if player_id is None:
            return None

        result = jsonrpc(
            "Player.GetItem",
            {
                "playerid": player_id,
                "properties": [
                    "episode",
                    "season",
                    "showtitle",
                    "title",
                    "tvshowid",
                    "file",
                    "playcount",
                ],
            },
        )
        item = result.get("result", {}).get("item", {})
        if item.get("type") != "episode":
            return None

        tvshow_id = item.get("tvshowid", -1)
        if tvshow_id in (-1, None):
            return None

        return item

    def get_chapter_markers(self):
        starts = self.get_chapter_starts_from_jsonrpc()
        if starts:
            return starts, []
        return self.get_chapter_markers_from_labels()

    def get_chapter_starts_from_jsonrpc(self):
        player_id = self.get_active_player_id()
        if player_id is None:
            return []

        result = jsonrpc(
            "Player.GetProperties",
            {
                "playerid": player_id,
                "properties": ["chapters"],
            },
            log_errors=False,
        )
        chapters = result.get("result", {}).get("chapters", [])
        starts = []
        for chapter in chapters:
            start_time = self.chapter_time_to_seconds(chapter.get("time"))
            if start_time is not None:
                starts.append(start_time)

        unique_starts = sorted(set(starts))
        if unique_starts:
            log("Detected chapter starts from JSON-RPC: %s" % unique_starts, xbmc.LOGDEBUG)
        return unique_starts

    def get_chapter_markers_from_labels(self):
        try:
            chapter_count_raw = xbmc.getInfoLabel("Player.ChapterCount")
            chapter_count = int(chapter_count_raw or "0")
        except ValueError:
            chapter_count_raw = xbmc.getInfoLabel("Player.ChapterCount")
            chapter_count = 0

        chapter_percentages = self.get_chapter_percentages_from_player_label(chapter_count)
        if chapter_percentages:
            log("Detected chapter percentages from Player.Chapters: %s" % chapter_percentages, xbmc.LOGDEBUG)

        if get_setting_bool("debug_logging"):
            current_chapter = xbmc.getInfoLabel("Player.Chapter")
            current_chapter_name = xbmc.getInfoLabel("Player.ChapterName")
            legacy_count_raw = xbmc.getInfoLabel("VideoPlayer.ChapterCount")
            log(
                "Chapter label diagnostics -> count_raw=%s, current=%s, current_name=%s, legacy_count_raw=%s" % (
                    chapter_count_raw or "",
                    current_chapter or "",
                    current_chapter_name or "",
                    legacy_count_raw or "",
                ),
                xbmc.LOGDEBUG,
            )

        starts = []
        for index in range(1, chapter_count + 1):
            label = xbmc.getInfoLabel("Player.Chapter(%d)" % index)
            if not label:
                label = xbmc.getInfoLabel("VideoPlayer.Chapter(%d)" % index)
            if get_setting_bool("debug_logging") and index <= 8:
                log("Chapter label %d -> %s" % (index, label or ""), xbmc.LOGDEBUG)
            start_time = self.parse_time_string(label)
            if start_time is not None:
                starts.append(start_time)

        unique_starts = sorted(set(starts))
        if unique_starts:
            log("Detected chapter starts from labels: %s" % unique_starts, xbmc.LOGDEBUG)
        return unique_starts, chapter_percentages

    def get_chapter_percentages_from_player_label(self, chapter_count=0):
        raw_value = xbmc.getInfoLabel("Player.Chapters")
        if get_setting_bool("debug_logging"):
            log("Player.Chapters raw -> %s" % (raw_value or ""), xbmc.LOGDEBUG)

        if not raw_value:
            return []

        tokens = []
        for token in raw_value.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                tokens.append(float(token))
            except ValueError:
                return []

        if not tokens:
            return []

        # Kodi builds appear to expose Player.Chapters in different layouts:
        # - one start percentage per chapter, e.g. "0.00000,89.75975"
        # - repeated chapter boundaries, e.g. start1,end1,start2,end2,...
        # Normalize both by preserving ordered unique boundary values.
        boundaries = []
        seen = set()
        for value in tokens:
            rounded_value = round(value, 5)
            if rounded_value in seen:
                continue
            seen.add(rounded_value)
            boundaries.append(value)

        if chapter_count > 0 and len(boundaries) > chapter_count:
            boundaries = boundaries[:chapter_count]

        cleaned_starts = []
        for start_percent in boundaries:
            if 0.0 <= start_percent < 100.0:
                cleaned_starts.append(start_percent)

        return sorted(set(cleaned_starts))

    def chapter_time_to_seconds(self, value):
        if isinstance(value, dict):
            hours = int(value.get("hours", 0))
            minutes = int(value.get("minutes", 0))
            seconds = int(value.get("seconds", 0))
            milliseconds = int(value.get("milliseconds", 0))
            return hours * 3600 + minutes * 60 + seconds + (milliseconds / 1000.0)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return self.parse_time_string(value)
        return None

    def parse_time_string(self, value):
        if not value:
            return None

        text = value.strip()
        if not text:
            return None

        match = re.search(r'(\d{1,2}:\d{2}:\d{2}(?:[.,]\d+)?)', text)
        if match:
            text = match.group(1)

        milliseconds = 0.0
        if "." in text or "," in text:
            separator = "." if "." in text else ","
            text, fraction = text.split(separator, 1)
            try:
                milliseconds = float("0.%s" % fraction)
            except ValueError:
                milliseconds = 0.0

        parts = text.split(":")
        if len(parts) == 2:
            parts = ["0"] + parts
        if len(parts) != 3:
            return None

        try:
            hours, minutes, seconds = [int(part) for part in parts]
        except ValueError:
            return None

        return hours * 3600 + minutes * 60 + seconds + milliseconds

    def parse_setting_time(self, value):
        return self.parse_time_string(value)

    def calculate_trigger_time(self, total_time):
        if get_setting_bool("prefer_chapter_trigger"):
            chapter_trigger = self.get_last_chapter_trigger(total_time)
            if chapter_trigger is not None:
                self.next_trigger_source = "chapter"
                return chapter_trigger
            log("No usable chapter trigger found, falling back to percentage trigger", xbmc.LOGDEBUG)

        fallback_percent = get_setting_int("fallback_trigger_percent", default=90, minimum=50, maximum=99)
        self.next_trigger_source = "fallback"
        return max(1.0, total_time * (fallback_percent / 100.0))

    def get_last_chapter_trigger(self, total_time):
        candidates = []
        cutoff = max(1.0, total_time - 5.0)
        for start_time in self.chapter_starts:
            if 0 < start_time < cutoff:
                candidates.append(start_time)

        if not candidates:
            return None

        return candidates[-1]

    def refresh_chapter_markers(self, total_time):
        starts, percentages = self.get_chapter_markers()
        converted_starts = list(starts)
        for start_percent in percentages:
            start_time = total_time * (start_percent / 100.0)
            if 0 < start_time < total_time:
                converted_starts.append(start_time)

        unique_starts = sorted(set(converted_starts))
        if unique_starts != self.chapter_starts or percentages != self.chapter_percents:
            self.chapter_starts = unique_starts
            self.chapter_percents = percentages
            log(
                "Refreshed chapter markers -> starts=%s percents=%s" % (
                    self.chapter_starts,
                    self.chapter_percents,
                ),
                xbmc.LOGDEBUG,
            )
        if get_setting_bool("enable_skip_intro"):
            self.skip_intro_start, self.skip_intro_target = self.calculate_skip_intro_window(total_time)

    def calculate_skip_intro_window(self, total_time):
        max_percent = get_setting_int("skip_intro_max_percent", default=25, minimum=1, maximum=50)
        early_cutoff = total_time * (max_percent / 100.0)
        minimum_intro_target = 20.0
        minimum_gap = 20.0
        candidates = []
        previous_start = 0.0
        for start_time in self.chapter_starts:
            if start_time <= 0:
                previous_start = max(previous_start, start_time)
                continue
            if start_time < minimum_intro_target:
                previous_start = start_time
                continue
            if start_time <= early_cutoff and is_meaningful_gap(start_time, previous_start, minimum_gap):
                candidates.append(start_time)
            previous_start = start_time

        if not candidates:
            if not get_setting_bool("enable_skip_intro_fallback"):
                return None, None
            fallback_start = self.parse_setting_time(get_setting_string("skip_intro_fallback_start", "00:15"))
            fallback_end = self.parse_setting_time(get_setting_string("skip_intro_fallback_end", "01:30"))
            if fallback_start is None:
                fallback_start = 15.0
            if fallback_end is None:
                fallback_end = 90.0
            fallback_start = max(1.0, min(fallback_start, max(1.0, total_time - 1.0)))
            fallback_end = max(fallback_start + 1.0, min(fallback_end, total_time))
            rounded_target = round(fallback_end, 2)
            if self.last_logged_skip_intro_target != rounded_target:
                log(
                    "No usable intro chapter target found, falling back to start=%.2f end=%.2f" % (
                        fallback_start,
                        fallback_end,
                    ),
                    xbmc.LOGDEBUG,
                )
                self.last_logged_skip_intro_target = rounded_target
            return fallback_start, fallback_end

        if len(candidates) >= 2:
            window_start = candidates[0]
            target = candidates[1]
            rounded_target = round(target, 2)
            if self.last_logged_skip_intro_target != rounded_target:
                log(
                    "Using skip intro window %.2f -> %.2f seconds" % (
                        window_start,
                        target,
                    ),
                    xbmc.LOGDEBUG,
                )
                self.last_logged_skip_intro_target = rounded_target
            return window_start, target

        target = candidates[0]
        rounded_target = round(target, 2)
        if self.last_logged_skip_intro_target != rounded_target:
            log("Using skip intro target %.2f seconds" % target, xbmc.LOGDEBUG)
            self.last_logged_skip_intro_target = rounded_target
        return 1.0, target

    def handle_skip_intro(self, current_time, total_time):
        if not get_setting_bool("enable_skip_intro"):
            if self.overlay_action == "skip_intro":
                self.close_overlay()
            return False

        if self.skip_intro_target is None:
            self.skip_intro_start, self.skip_intro_target = self.calculate_skip_intro_window(total_time)

        if self.skip_intro_target is None:
            return False

        if self.skip_intro_start is None:
            self.skip_intro_start = 1.0

        # Skip Intro should only be offered while playback is still before the intro-end marker.
        if current_time >= self.skip_intro_target:
            if self.overlay_action == "skip_intro":
                self.close_overlay()
            self.skip_intro_prompted = True
            return False

        if current_time < self.skip_intro_start:
            return False

        hide_threshold = self.skip_intro_start + ((self.skip_intro_target - self.skip_intro_start) * 0.2)
        if current_time >= hide_threshold:
            if self.overlay_action == "skip_intro":
                log(
                    "Closing Skip Intro overlay early in intro window (current=%.2f, start=%.2f, target=%.2f)" % (
                        current_time,
                        self.skip_intro_start,
                        self.skip_intro_target,
                    ),
                    xbmc.LOGDEBUG,
                )
                self.close_overlay()
            self.skip_intro_prompted = True
            return False

        if self.skip_intro_prompted:
            return False

        if self.skip_intro_overlay_shown_at is not None and (current_time - self.skip_intro_overlay_shown_at) >= 10.0:
            if self.overlay_action == "skip_intro":
                log(
                    "Closing Skip Intro overlay after timeout (current=%.2f, shown_at=%.2f)" % (
                        current_time,
                        self.skip_intro_overlay_shown_at,
                    ),
                    xbmc.LOGDEBUG,
                )
                self.close_overlay()
            self.skip_intro_prompted = True
            return False

        if self.overlay_action == "skip_intro":
            return True

        if self.overlay:
            return False

        self.show_overlay("skip_intro")
        self.skip_intro_overlay_shown_at = current_time
        self.skip_intro_prompted = True
        log("Displayed Skip Intro overlay at %.2f -> target %.2f" % (current_time, self.skip_intro_target), xbmc.LOGDEBUG)
        return True

    def get_next_episode(self):
        if self.next_episode is not None:
            return self.next_episode

        current = self.current_episode
        if not current:
            return None

        tvshow_id = current.get("tvshowid")
        current_episode_id = current.get("id") or current.get("episodeid")
        result = jsonrpc(
            "VideoLibrary.GetEpisodes",
            {
                "tvshowid": int(tvshow_id),
                "properties": [
                    "title",
                    "season",
                    "episode",
                    "showtitle",
                    "playcount",
                    "file",
                ],
                "sort": {"method": "episode"},
            },
        )

        episodes = result.get("result", {}).get("episodes", [])
        found_current = False
        for episode in episodes:
            if episode.get("episodeid") == current_episode_id:
                found_current = True
                continue
            if not found_current:
                continue
            if episode.get("file") == self.current_file:
                continue
            self.next_episode = episode
            return episode

        self.next_episode = False
        return None

    def prompt_for_next_episode(self):
        if self.next_overlay_dismissed:
            return

        self.prompted = True

        episode = self.get_next_episode()
        if not episode:
            log("No next library episode found", xbmc.LOGDEBUG)
            return

        self.show_overlay("next_episode")
        log("Displayed Next overlay for episode %s" % episode.get("episodeid"), xbmc.LOGDEBUG)

    def show_overlay(self, action_name):
        if self.overlay:
            if self.overlay_action == action_name:
                return
            self.close_overlay()

        self.overlay_action = action_name
        xml_filename = self.get_overlay_xml()
        self.overlay = NextOnLibraryOverlay(
            xml_filename,
            ADDON_PATH,
            "default",
            "1080i",
        )
        self.overlay.service = self
        self.overlay.show()
        log(
            "Opened overlay xml=%s for action=%s trigger_source=%s" % (
                xml_filename,
                self.overlay_action,
                self.next_trigger_source,
            ),
            xbmc.LOGDEBUG,
        )

    def configure_overlay_controls(self, overlay):
        show_close_button = self.should_show_close_button()
        try:
            close_button = overlay.getControl(CLOSE_BUTTON_CONTROL_ID)
        except RuntimeError:
            log(
                "Overlay control configuration -> action=%s, trigger_source=%s, show_close=%s, close_control=missing" % (
                    self.overlay_action,
                    self.next_trigger_source,
                    show_close_button,
                ),
                xbmc.LOGDEBUG,
            )
            return

        if show_close_button:
            close_button.setVisible(True)
            close_button.setEnabled(True)
            log(
                "Overlay control configuration -> action=%s, trigger_source=%s, show_close=true" % (
                    self.overlay_action,
                    self.next_trigger_source,
                ),
                xbmc.LOGDEBUG,
            )
        else:
            close_button.setVisible(False)
            close_button.setEnabled(False)
            log(
                "Overlay control configuration -> action=%s, trigger_source=%s, show_close=false" % (
                    self.overlay_action,
                    self.next_trigger_source,
                ),
                xbmc.LOGDEBUG,
            )

    def get_overlay_label(self):
        if self.overlay_action == "skip_intro":
            return localize(30017)
        return localize(30011)

    def get_overlay_xml(self):
        return "script-nextonlibrary-overlay.xml"

    def should_show_close_button(self):
        return False

    def handle_overlay_action(self):
        if self.overlay_action == "skip_intro":
            self.seek_skip_intro()
            return
        self.play_next_episode()

    def dismiss_overlay(self, user_initiated=True):
        if self.overlay_action == "next_episode" and user_initiated:
            self.next_overlay_dismissed = True
            self.prompted = True
            log("Next overlay dismissed by user action", xbmc.LOGDEBUG)
        self.close_overlay()

    def seek_skip_intro(self):
        target_time = self.skip_intro_target
        try:
            current_time = self.player.getTime()
        except RuntimeError:
            current_time = 0.0
        self.close_overlay()
        if target_time is None:
            log("Skip Intro target vanished before click handling", xbmc.LOGDEBUG)
            return
        if current_time >= target_time:
            log(
                "Skip Intro click ignored because playback already passed the target (current=%.2f, target=%.2f)" % (
                    current_time,
                    target_time,
                ),
                xbmc.LOGDEBUG,
            )
            return
        try:
            self.player.seekTime(target_time)
            self.skip_intro_overlay_shown_at = None
            log("Seeking to skip intro target %.2f seconds" % target_time, xbmc.LOGDEBUG)
        except RuntimeError:
            log("Failed to seek to skip intro target %.2f seconds" % target_time, xbmc.LOGDEBUG)

    def play_next_episode(self):
        episode = self.get_next_episode()
        self.close_overlay()
        if not episode:
            log("Next episode vanished before click handling", xbmc.LOGDEBUG)
            return

        jsonrpc("Player.Open", {"item": {"episodeid": episode.get("episodeid")}})
        log("Opening next episode %s" % episode.get("episodeid"), xbmc.LOGDEBUG)


if __name__ == "__main__":
    NextOnLibraryService().run()
