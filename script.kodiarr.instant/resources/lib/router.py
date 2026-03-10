# -*- coding: utf-8 -*-
import xbmc

from .common import notify, log
from . import radarr
from . import sonarr


def run():
    db_type = xbmc.getInfoLabel("ListItem.DBTYPE").lower()
    item_type = xbmc.getInfoLabel("ListItem.Property(item.type)").lower()

    log("DBTYPE='{}' item.type='{}'".format(db_type, item_type))

    movie_types = ("movie",)
    tv_types = ("tvshow", "season", "episode")

    if db_type in movie_types or item_type in movie_types:
        log("Routing to Radarr")
        radarr.run()
        return

    if db_type in tv_types or item_type in tv_types:
        log("Routing to Sonarr")
        sonarr.run()
        return

    notify("KodiARR Instant", "Unsupported item type.")
    log("Unsupported item type. DBTYPE='{}' item.type='{}'".format(db_type, item_type), xbmc.LOGERROR)
