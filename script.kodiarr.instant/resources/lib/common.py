# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("[{}] {}".format(ADDON_NAME, msg), level)


def notify(title, message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(title, message, icon, 5000)


def get_setting(key, default=""):
    try:
        value = ADDON.getSetting(key)
        return value if value != "" else default
    except Exception:
        return default


def get_int_setting(key, default=0):
    try:
        return int(get_setting(key, str(default)))
    except Exception:
        return default


def clean_url(url):
    return (url or "").strip().rstrip("/")


def ensure_required(service_name, url, api_key, root_folder):
    if url and api_key and root_folder:
        return True

    notify(service_name, "Please configure the addon settings first.", xbmcgui.NOTIFICATION_ERROR)
    try:
        ADDON.openSettings()
    except Exception:
        pass
    return False
