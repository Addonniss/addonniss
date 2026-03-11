# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon

ADDON_ID = "script.kodiarr.instant"
ADDON = xbmcaddon.Addon(ADDON_ID)


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("[KodiARR Instant] {}".format(msg), level)


def notify(title, message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(title, message, icon, 5000)


def alert(title, message):
    xbmcgui.Dialog().ok(title, message)


def get_setting(key, default=""):
    try:
        value = ADDON.getSetting(key)
        return value if value != "" else default
    except Exception:
        return default


def get_int(key, default=0):
    try:
        return int(get_setting(key, str(default)))
    except Exception:
        return default


def clean_url(url):
    return (url or "").strip().rstrip("/")


def open_settings():
    try:
        ADDON.openSettings()
    except Exception:
        pass
