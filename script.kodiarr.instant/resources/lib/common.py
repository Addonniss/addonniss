import xbmc
import xbmcgui
import xbmcaddon

ADDON = xbmcaddon.Addon()


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("[KodiARR] " + str(msg), level)


def notify(title, message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(title, message, icon, 5000)


def get_setting(key):
    return ADDON.getSetting(key)


def get_int(key, default=0):
    try:
        return int(ADDON.getSetting(key))
    except:
        return default


def clean_url(url):
    return url.rstrip("/")
