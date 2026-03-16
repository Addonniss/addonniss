# -*- coding: utf-8 -*-
import xbmcgui

from . import radarr, sonarr
from .common import get_addon_path, get_setting, notify, set_setting

TITLE = "KodiARR Instant"

URL_ID = 3101
API_ID = 3102
ROOT_ID = 3103
PROFILE_ID = 3104

SWITCH_ID = 3201
TEST_ID = 3202
SAVE_CLOSE_ID = 3203
CLOSE_ID = 3204


class QuickSetupDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = ""
        self.field_map = {}
        self.test_callback = None
        self.switch_label = ""
        self.switch_target = None
        self.test_label = ""
        self.help_text = {}
        self._switch_requested = False

    def onInit(self):
        self.getControl(3001).setLabel("{} Quick Setup".format(self.service_name))
        self.getControl(SWITCH_ID).setLabel(self.switch_label)
        self.getControl(TEST_ID).setLabel(self.test_label)
        self.getControl(URL_ID).setText(get_setting(self.field_map["url"]))
        self.getControl(API_ID).setText(get_setting(self.field_map["api"]))
        self.getControl(ROOT_ID).setText(get_setting(self.field_map["root"]))
        self.getControl(PROFILE_ID).setText(get_setting(self.field_map["profile"], "1"))
        self._set_help(URL_ID)

    def onFocus(self, control_id):
        self._set_help(control_id)

    def onClick(self, control_id):
        if control_id == SWITCH_ID:
            self._switch_requested = True
            self.close()
        elif control_id == TEST_ID:
            if self._save(show_notification=False):
                self.test_callback(show_notification=True)
        elif control_id == SAVE_CLOSE_ID:
            if self._save(show_notification=True):
                self.close()
        elif control_id == CLOSE_ID:
            self.close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (
            xbmcgui.ACTION_NAV_BACK,
            xbmcgui.ACTION_PREVIOUS_MENU,
            xbmcgui.ACTION_PARENT_DIR,
        ):
            self.close()

    def _collect_values(self):
        return {
            self.field_map["url"]: self.getControl(URL_ID).getText().strip(),
            self.field_map["api"]: self.getControl(API_ID).getText().strip(),
            self.field_map["root"]: self.getControl(ROOT_ID).getText().strip(),
            self.field_map["profile"]: self.getControl(PROFILE_ID).getText().strip(),
        }

    def _save(self, show_notification):
        values = self._collect_values()
        if not all(values.values()):
            notify(TITLE, "Please fill all fields", xbmcgui.NOTIFICATION_WARNING)
            return False

        saved_ok = True
        for key, value in values.items():
            saved_ok = set_setting(key, value) and saved_ok

        if not saved_ok:
            notify(TITLE, "Failed to save settings", xbmcgui.NOTIFICATION_ERROR)
            return False

        if show_notification:
            notify(TITLE, "{} settings saved".format(self.service_name))
        return True

    def _set_help(self, control_id):
        text = self.help_text.get(control_id, self.help_text.get("default", ""))
        self.getControl(3002).setText(text)


def _run_dialog(service_name, field_map, test_callback, switch_label, switch_target, test_label, help_text):
    dialog = QuickSetupDialog("QuickSetupDialog.xml", get_addon_path(), "default", "1080i")
    dialog.service_name = service_name
    dialog.field_map = field_map
    dialog.test_callback = test_callback
    dialog.switch_label = switch_label
    dialog.switch_target = switch_target
    dialog.test_label = test_label
    dialog.help_text = help_text
    dialog.doModal()
    next_dialog = dialog.switch_target if dialog._switch_requested else None
    del dialog

    if next_dialog:
        next_dialog()


def _run_radarr_flow():
    _run_dialog(
        "Radarr",
        {
            "url": "radarr_url",
            "api": "radarr_api",
            "root": "radarr_root",
            "profile": "radarr_quality_profile",
        },
        radarr.test_connection,
        "Open Sonarr Settings",
        _run_sonarr_flow,
        "Test Radarr Connection",
        {
            "default": "Move through the form and the helper text will follow the selected field or action.",
            URL_ID: "Base address of your Radarr instance, for example http://192.168.1.10:7878",
            API_ID: "API key from Radarr Settings > General.",
            ROOT_ID: "Root folder path Radarr should use when adding new movies.",
            PROFILE_ID: "Numeric quality profile ID used when adding movies.",
            SWITCH_ID: "Open the Sonarr custom settings page without going back to the launcher.",
            TEST_ID: "Save the current Radarr values, then verify the saved Radarr URL and API key.",
            SAVE_CLOSE_ID: "Save the current Radarr values and close this page.",
            CLOSE_ID: "Close this page without saving any new changes.",
        },
    )


def _run_sonarr_flow():
    _run_dialog(
        "Sonarr",
        {
            "url": "sonarr_url",
            "api": "sonarr_api",
            "root": "sonarr_root",
            "profile": "sonarr_quality_profile",
        },
        sonarr.test_connection,
        "Open Radarr Settings",
        _run_radarr_flow,
        "Test Sonarr Connection",
        {
            "default": "Move through the form and the helper text will follow the selected field or action.",
            URL_ID: "Base address of your Sonarr instance, for example http://192.168.1.11:8989",
            API_ID: "API key from Sonarr Settings > General.",
            ROOT_ID: "Root folder path Sonarr should use when adding new series.",
            PROFILE_ID: "Numeric quality profile ID used when adding series.",
            SWITCH_ID: "Open the Radarr custom settings page without going back to the launcher.",
            TEST_ID: "Save the current Sonarr values, then verify the saved Sonarr URL and API key.",
            SAVE_CLOSE_ID: "Save the current Sonarr values and close this page.",
            CLOSE_ID: "Close this page without saving any new changes.",
        },
    )


def open_radarr_settings():
    _run_radarr_flow()


def open_sonarr_settings():
    _run_sonarr_flow()


def show_launcher_menu():
    options = [
        "Radarr Settings",
        "Sonarr Settings",
    ]
    choice = xbmcgui.Dialog().select(TITLE, options)

    if choice == 0:
        _run_radarr_flow()
    elif choice == 1:
        _run_sonarr_flow()
