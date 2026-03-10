import requests
import xbmcgui

from .common import get_setting, get_int, clean_url, notify
from .context import get_movie_id


def run():

    radarr_url = clean_url(get_setting("radarr_url"))
    api = get_setting("radarr_api")
    root = get_setting("radarr_root")
    profile = get_int("radarr_quality_profile", 1)

    if not radarr_url or not api:
        notify("Radarr", "Please configure settings", xbmcgui.NOTIFICATION_ERROR)
        return

    id_val, id_type = get_movie_id()

    if not id_val:
        notify("Radarr", "No movie ID found", xbmcgui.NOTIFICATION_ERROR)
        return

    headers = {"X-Api-Key": api}

    term = f"{id_type}:{id_val}"

    notify("Radarr", f"Searching {term}")

    lookup = requests.get(
        f"{radarr_url}/api/v3/movie/lookup?term={term}",
        headers=headers
    )

    if lookup.status_code != 200:
        notify("Radarr", "Lookup failed", xbmcgui.NOTIFICATION_ERROR)
        return

    movies = lookup.json()

    if not movies:
        notify("Radarr", "Movie not found", xbmcgui.NOTIFICATION_ERROR)
        return

    movie = movies[0]

    payload = {
        "title": movie["title"],
        "qualityProfileId": profile,
        "rootFolderPath": root,
        "tmdbId": movie["tmdbId"],
        "year": movie.get("year"),
        "monitored": True,
        "addOptions": {"searchForMovie": True}
    }

    r = requests.post(
        f"{radarr_url}/api/v3/movie",
        json=payload,
        headers=headers
    )

    if r.status_code == 201:
        notify("Radarr", f"Added {movie['title']}")
    else:
        notify("Radarr", "Add failed", xbmcgui.NOTIFICATION_ERROR)
