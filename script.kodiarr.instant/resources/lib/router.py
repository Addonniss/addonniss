# -*- coding: utf-8 -*-
import sys
import xbmc

from . import radarr, sonarr
from .common import log, notify


def _get_action():
    argv_text = " ".join(sys.argv).lower()

    if "action=test_radarr" in argv_text:
        return "test_radarr"
    if "action=test_sonarr" in argv_text:
        return "test_sonarr"

    return "add"


def run():
    action = _get_action()
    log("Router action={}".format(action))

    if action == "test_radarr":
        radarr.test_connection(show_notification=True)
        return

    if action == "test_sonarr":
        sonarr.test_connection(show_notification=True)
        return

    db_type = xbmc.getInfoLabel("ListItem.DBTYPE").lower()
    item_type = xbmc.getInfoLabel("ListItem.Property(item.type)").lower()

    log("DBTYPE={} item.type={}".format(db_type, item_type))

    if db_type == "movie" or item_type == "movie":
        log("Routing to Radarr")
        radarr.run()
        return

    if db_type in ["tvshow", "season", "episode"] or item_type in ["tvshow", "season", "episode"]:
        log("Routing to Sonarr")
        sonarr.run()
        return

    notify("KodiARR Instant", "Unsupported item type")
