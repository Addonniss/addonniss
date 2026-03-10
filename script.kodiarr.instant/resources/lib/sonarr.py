import requests
import xbmcgui

from .common import get_setting, get_int, clean_url, notify
from .context import find_series_id


def run():

    sonarr_url = clean_url(get_setting("sonarr_url"))
    api = get_setting("sonarr_api")
    root = get_setting("sonarr_root")
    profile = get_int("sonarr_quality_profile", 1)

    if not sonarr_url or not api:
        notify("Sonarr", "Please configure settings", xbmcgui.NOTIFICATION_ERROR)
        return

    series_id, id_type = find_series_id()

    if not series_id:
        notify("Sonarr", "No series ID found", xbmcgui.NOTIFICATION_ERROR)
        return

    headers = {"X-Api-Key": api}

    term = f"{id_type}:{series_id}"

    lookup = requests.get(
        f"{sonarr_url}/api/v3/series/lookup?term={term}",
        headers=headers
    )

    if lookup.status_code != 200:
        notify("Sonarr", "Lookup failed", xbmcgui.NOTIFICATION_ERROR)
        return

    results = lookup.json()

    if not results:
        notify("Sonarr", "Show not found", xbmcgui.NOTIFICATION_ERROR)
        return

    series = results[0]

    payload = {
        **series,
        "qualityProfileId": profile,
        "rootFolderPath": root,
        "monitored": True,
        "addOptions": {"searchForMissingEpisodes": True}
    }

    r = requests.post(
        f"{sonarr_url}/api/v3/series",
        json=payload,
        headers=headers
    )

    if r.status_code == 201:
        notify("Sonarr", f"Added {series['title']}")
    else:
        notify("Sonarr", "Add failed", xbmcgui.NOTIFICATION_ERROR)
