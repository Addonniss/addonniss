# -*- coding: utf-8 -*-
import requests
import xbmcgui

from .common import (
    get_setting,
    get_int_setting,
    clean_url,
    notify,
    log,
    ensure_required
)
from .context import get_movie_id


def run():
    radarr_url = clean_url(get_setting("radarr_url"))
    api_key = get_setting("radarr_api")
    root_folder = get_setting("radarr_root")
    quality_profile_id = get_int_setting("radarr_quality_profile", 8)

    if not ensure_required("Radarr", radarr_url, api_key, root_folder):
        return

    id_val, id_type = get_movie_id()
    if not id_val:
        notify("Radarr", "No movie ID found. Check logs.", xbmcgui.NOTIFICATION_ERROR)
        log("Movie ID not found from current context.", xbmcgui.LOGERROR)
        return

    headers = {"X-Api-Key": api_key}
    clean_id = str(id_val).strip()
    term = "{}:{}".format(id_type, clean_id)

    notify("Radarr", "Searching {}...".format(term))

    try:
        lookup_url = "{}/api/v3/movie/lookup?term={}".format(radarr_url, term)
        r = requests.get(lookup_url, headers=headers, timeout=10)

        if r.status_code != 200:
            notify("Radarr", "API Error: {}".format(r.status_code), xbmcgui.NOTIFICATION_ERROR)
            log("Lookup failed: {}".format(r.text), xbmcgui.LOGERROR)
            return

        movies = r.json()
        if not movies:
            notify("Radarr", "No metadata found for {}".format(term), xbmcgui.NOTIFICATION_ERROR)
            return

        movie = movies[0]
        movie_title = movie.get("title", "Unknown")

        if not movie.get("tmdbId"):
            notify("Radarr", "Lookup returned invalid data.", xbmcgui.NOTIFICATION_ERROR)
            log("Invalid lookup payload: {}".format(movie), xbmcgui.LOGERROR)
            return

        if "id" in movie and movie["id"] > 0:
            notify("Radarr", "'{}' exists. Triggering search...".format(movie_title))
            requests.post(
                "{}/api/v3/command".format(radarr_url),
                json={"name": "MoviesSearch", "movieIds": [movie["id"]]},
                headers=headers,
                timeout=10
            )
            return

        payload = {
            "title": movie["title"],
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder,
            "tmdbId": movie["tmdbId"],
            "year": movie.get("year"),
            "images": movie.get("images", []),
            "monitored": True,
            "addOptions": {"searchForMovie": True}
        }

        add_url = "{}/api/v3/movie".format(radarr_url)
        r_add = requests.post(add_url, json=payload, headers=headers, timeout=15)

        if r_add.status_code == 201:
            new_movie = r_add.json()
            new_db_id = new_movie["id"]

            notify("Radarr", "Added '{}'. Search started.".format(movie_title))

            requests.post(
                "{}/api/v3/command".format(radarr_url),
                json={"name": "MoviesSearch", "movieIds": [new_db_id]},
                headers=headers,
                timeout=10
            )
        else:
            notify("Radarr", "Add failed: {}".format(r_add.status_code), xbmcgui.NOTIFICATION_ERROR)
            log("Add failed body: {}".format(r_add.text), xbmcgui.LOGERROR)

    except Exception as e:
        notify("Radarr", "Error: {}".format(str(e)), xbmcgui.NOTIFICATION_ERROR)
        log("Crash: {}".format(str(e)), xbmcgui.LOGERROR)
