import xbmc
from . import radarr, sonarr
from .common import log, notify


def run():

    db_type = xbmc.getInfoLabel("ListItem.DBTYPE").lower()
    item_type = xbmc.getInfoLabel("ListItem.Property(item.type)").lower()

    log(f"DBTYPE={db_type} item.type={item_type}")

    if db_type == "movie" or item_type == "movie":
        log("Routing to Radarr")
        radarr.run()
        return

    if db_type in ["tvshow", "season", "episode"] or item_type in ["tvshow", "season", "episode"]:
        log("Routing to Sonarr")
        sonarr.run()
        return

    notify("KodiARR Instant", "Unsupported item type")
