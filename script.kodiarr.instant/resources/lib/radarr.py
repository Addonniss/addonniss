import requests
import xbmcgui

from .common import get_setting, get_int, clean_url, notify, log
from .context import get_movie_id


def run():
    radarr_url = clean_url(get_setting("radarr_url"))
    api = get_setting("radarr_api")
    root = get_setting("radarr_root")
    profile = get_int("radarr_quality_profile", 1)

    if not radarr_url or not api or not root:
        notify("Radarr", "Please configure settings", xbmcgui.NOTIFICATION_ERROR)
        return

    id_val, id_type = get_movie_id()

    if not id_val:
        notify("Radarr", "No movie ID found", xbmcgui.NOTIFICATION_ERROR)
        return

    headers = {"X-Api-Key": api}
    term = f"{id_type}:{str(id_val).strip()}"

    try:
        notify("Radarr", f"Searching {term}")

        lookup = requests.get(
            f"{radarr_url}/api/v3/movie/lookup?term={term}",
            headers=headers,
            timeout=10
        )

        if lookup.status_code != 200:
            notify("Radarr", f"Lookup failed: {lookup.status_code}", xbmcgui.NOTIFICATION_ERROR)
            log(f"Radarr lookup failed: {lookup.text}")
            return

        movies = lookup.json()
        if not movies:
            notify("Radarr", "Movie not found", xbmcgui.NOTIFICATION_ERROR)
            return

        movie = movies[0]
        title = movie.get("title", "Unknown")

        if not movie.get("tmdbId"):
            notify("Radarr", "Invalid lookup result", xbmcgui.NOTIFICATION_ERROR)
            log(f"Radarr invalid lookup payload: {movie}")
            return

        # Already exists in Radarr -> just search
        if movie.get("id", 0) > 0:
            movie_id = movie["id"]

            cmd = requests.post(
                f"{radarr_url}/api/v3/command",
                json={"name": "MoviesSearch", "movieIds": [movie_id]},
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Radarr", f"'{title}' already exists. Search triggered.")
            else:
                notify("Radarr", "Movie exists, but search failed", xbmcgui.NOTIFICATION_ERROR)
                log(f"Radarr command failed: {cmd.text}")
            return

        # Missing -> add then search
        payload = {
            "title": movie["title"],
            "qualityProfileId": profile,
            "rootFolderPath": root,
            "tmdbId": movie["tmdbId"],
            "year": movie.get("year"),
            "images": movie.get("images", []),
            "monitored": True,
            "addOptions": {"searchForMovie": True}
        }

        add_resp = requests.post(
            f"{radarr_url}/api/v3/movie",
            json=payload,
            headers=headers,
            timeout=15
        )

        if add_resp.status_code == 201:
            added = add_resp.json()
            new_id = added["id"]

            # extra explicit search
            requests.post(
                f"{radarr_url}/api/v3/command",
                json={"name": "MoviesSearch", "movieIds": [new_id]},
                headers=headers,
                timeout=10
            )

            notify("Radarr", f"Added '{title}'. Search started.")
        else:
            notify("Radarr", f"Add failed: {add_resp.status_code}", xbmcgui.NOTIFICATION_ERROR)
            log(f"Radarr add failed: {add_resp.text}")

    except Exception as e:
        notify("Radarr", f"Error: {e}", xbmcgui.NOTIFICATION_ERROR)
        log(f"Radarr crash: {e}")
