# -*- coding: utf-8 -*-
import sys
import xbmc

from . import radarr, sonarr
from .common import log, notify


def _get_action():
    argv = [str(x).lower() for x in sys.argv]
    argv_text = " ".join(argv)

    if "action=test_radarr" in argv_text:
        return "test_radarr"
    if "action=test_sonarr" in argv_text:
        return "test_sonarr"

    if "radarr" in argv:
        return "radarr"
    if "sonarr" in argv:
        return "sonarr"

    if "action=radarr" in argv_text:
        return "radarr"
    if "action=sonarr" in argv_text:
        return "sonarr"

    return None


def run():
    action = _get_action()
    log("Router action={}".format(action))
    log("sys.argv={}".format(sys.argv))

    if action == "test_radarr":
        radarr.test_connection(show_notification=True)
        return

    if action == "test_sonarr":
        sonarr.test_connection(show_notification=True)
        return

    if action == "radarr":
        log("Calling radarr.run()")
        radarr.run()
        return

    if action == "sonarr":
        log("Calling sonarr.run()")
        sonarr.run()
        return

    db_type = xbmc.getInfoLabel("ListItem.DBTYPE").lower()
    item_type = xbmc.getInfoLabel("ListItem.Property(item.type)").lower()

    if db_type == "movie" or item_type == "movie":
        log("Fallback routing to Radarr")
        radarr.run()
        return

    if db_type in ["tvshow", "season", "episode"] or item_type in ["tvshow", "season", "episode"]:
        log("Fallback routing to Sonarr")
        sonarr.run()
        return

    notify("KodiARR Instant", "Unsupported item type")
