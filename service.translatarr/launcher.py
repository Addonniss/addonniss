# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui

ADDON_ID = "service.translatarr"
addon = xbmcaddon.Addon(ADDON_ID)

def show_changelog():
    try:
        changelog = addon.getAddonInfo("changelog")
        with open(changelog, "r", encoding="utf-8") as f:
            content = f.read()

        xbmcgui.Dialog().textviewer(
            f"{addon.getAddonInfo('name')} - Change Log",
            content
        )

    except Exception as e:
        xbmc.log(f"[Translatarr][Launcher] Failed to load changelog: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Translatarr", f"Failed to open changelog:\n{e}")

if __name__ == "__main__":

    # If called with parameter
    if len(sys.argv) > 1:
        param = sys.argv[1]

        if param == "show_changelog":
            show_changelog()
        else:
            addon.openSettings()
    else:
        # Default action: open settings
        addon.openSettings()
