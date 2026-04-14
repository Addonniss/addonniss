# -*- coding: utf-8 -*-
import requests
import xbmc
import xbmcgui

from .common import get_setting, get_int, clean_url, notify, alert, log, open_settings
from .context import get_sonarr_context


def _get_connection_values(url=None, api=None):
    return clean_url(url or get_setting("sonarr_url")), (api or get_setting("sonarr_api")).strip()


def _get_status(sonarr_url, headers):
    return requests.get(
        "{}/api/v3/system/status".format(sonarr_url),
        headers=headers,
        timeout=10
    )


def test_connection(show_notification=True, url=None, api=None):
    sonarr_url, api = _get_connection_values(url, api)

    if not sonarr_url or not api:
        if show_notification:
            alert("Sonarr", "Please fill Sonarr URL and API key.")
        log("Sonarr test: missing URL or API key", xbmc.LOGERROR)
        return False

    headers = {"X-Api-Key": api}

    try:
        resp = _get_status(sonarr_url, headers)

        if resp.status_code == 200:
            data = resp.json()
            version = data.get("version", "unknown")
            if show_notification:
                alert("Sonarr", "Connection OK ({})".format(version))
            return True

        if show_notification:
            alert("Sonarr", "Connection failed: HTTP {}".format(resp.status_code))
        log("Sonarr test failed: {}".format(resp.text), xbmc.LOGERROR)
        return False

    except Exception as e:
        if show_notification:
            alert("Sonarr", "Connection error:\n{}".format(e))
        log("Sonarr test crash: {}".format(e), xbmc.LOGERROR)
        return False


def fetch_setup_options(url=None, api=None):
    sonarr_url, api = _get_connection_values(url, api)
    if not sonarr_url or not api:
        raise ValueError("Please fill Sonarr URL and API key.")

    headers = {"X-Api-Key": api}

    root_resp = requests.get(
        "{}/api/v3/rootfolder".format(sonarr_url),
        headers=headers,
        timeout=10
    )
    root_resp.raise_for_status()

    profile_resp = requests.get(
        "{}/api/v3/qualityprofile".format(sonarr_url),
        headers=headers,
        timeout=10
    )
    profile_resp.raise_for_status()

    roots = [item.get("path", "").strip() for item in root_resp.json() if item.get("path")]
    profiles = [
        {"id": item.get("id"), "name": item.get("name", "").strip()}
        for item in profile_resp.json()
        if item.get("id") is not None and item.get("name")
    ]

    return {"roots": roots, "profiles": profiles}


def run():
    sonarr_url = clean_url(get_setting("sonarr_url"))
    api = get_setting("sonarr_api")
    root = get_setting("sonarr_root")
    profile = get_int("sonarr_quality_profile", 1)

    if not sonarr_url or not api or not root:
        notify("Sonarr", "Please configure settings", xbmcgui.NOTIFICATION_ERROR)
        open_settings()
        return

    info = get_sonarr_context()
    series_id = info.get("series_id")

    if not series_id:
        notify("Sonarr", "No series ID found", xbmcgui.NOTIFICATION_ERROR)
        return

    headers = {"X-Api-Key": api}
    term = "{}:{}".format(info["id_type"], series_id)

    try:
        lookup = requests.get(
            "{}/api/v3/series/lookup?term={}".format(sonarr_url, term),
            headers=headers,
            timeout=10
        )

        if lookup.status_code != 200:
            notify("Sonarr", "Lookup failed: {}".format(lookup.status_code), xbmcgui.NOTIFICATION_ERROR)
            log("Sonarr lookup failed: {}".format(lookup.text), xbmcgui.LOGERROR)
            return

        results = lookup.json()
        if not results:
            notify("Sonarr", "Show not found", xbmcgui.NOTIFICATION_ERROR)
            return

        series = results[0]
        title = series.get("title", "Unknown")
        series_db_id = series.get("id")

        if not series_db_id:
            should_search_missing = (info["type"] == "tvshow")

            payload = dict(series)
            payload.update({
                "qualityProfileId": profile,
                "rootFolderPath": root,
                "monitored": True,
                "addOptions": {
                    "searchForMissingEpisodes": should_search_missing
                }
            })

            add_resp = requests.post(
                "{}/api/v3/series".format(sonarr_url),
                json=payload,
                headers=headers,
                timeout=15
            )

            if add_resp.status_code != 201:
                notify("Sonarr", "Add failed: {}".format(add_resp.status_code), xbmcgui.NOTIFICATION_ERROR)
                log("Sonarr add failed: {}".format(add_resp.text), xbmcgui.LOGERROR)
                return

            series_db_id = add_resp.json()["id"]

            if info["type"] == "tvshow":
                notify("Sonarr", "Added '{}'. Search started.".format(title))
                return

        if info["type"] == "tvshow":
            cmd = requests.post(
                "{}/api/v3/command".format(sonarr_url),
                json={"name": "SeriesSearch", "seriesId": series_db_id},
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Sonarr", "Series search started: {}".format(title))
            else:
                notify("Sonarr", "Series search failed", xbmcgui.NOTIFICATION_ERROR)
                log("Sonarr series search failed: {}".format(cmd.text), xbmcgui.LOGERROR)
            return

        if info["type"] == "season":
            if not str(info["season"]).isdigit():
                notify("Sonarr", "Invalid season number", xbmcgui.NOTIFICATION_ERROR)
                return

            cmd = requests.post(
                "{}/api/v3/command".format(sonarr_url),
                json={
                    "name": "SeasonSearch",
                    "seriesId": series_db_id,
                    "seasonNumber": int(info["season"])
                },
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Sonarr", "Season {} search started".format(info["season"]))
            else:
                notify("Sonarr", "Season search failed", xbmcgui.NOTIFICATION_ERROR)
                log("Sonarr season search failed: {}".format(cmd.text), xbmcgui.LOGERROR)
            return

        if info["type"] == "episode":
            if not str(info["season"]).isdigit() or not str(info["episode"]).isdigit():
                notify("Sonarr", "Invalid episode info", xbmcgui.NOTIFICATION_ERROR)
                return

            ep_resp = requests.get(
                "{}/api/v3/episode?seriesId={}".format(sonarr_url, series_db_id),
                headers=headers,
                timeout=15
            )

            if ep_resp.status_code != 200:
                notify("Sonarr", "Episode lookup failed: {}".format(ep_resp.status_code), xbmcgui.NOTIFICATION_ERROR)
                log("Sonarr episode lookup failed: {}".format(ep_resp.text), xbmcgui.LOGERROR)
                return

            episodes = ep_resp.json()
            target = next(
                (
                    e for e in episodes
                    if e.get("seasonNumber") == int(info["season"])
                    and e.get("episodeNumber") == int(info["episode"])
                ),
                None
            )

            if not target:
                notify("Sonarr", "Episode not found in Sonarr DB", xbmcgui.NOTIFICATION_ERROR)
                return

            cmd = requests.post(
                "{}/api/v3/command".format(sonarr_url),
                json={"name": "EpisodeSearch", "episodeIds": [target["id"]]},
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify(
                    "Sonarr",
                    "S{:02d}E{:02d} search started".format(int(info["season"]), int(info["episode"]))
                )
            else:
                notify("Sonarr", "Episode search failed", xbmcgui.NOTIFICATION_ERROR)
                log("Sonarr episode search failed: {}".format(cmd.text), xbmcgui.LOGERROR)
            return

        notify("Sonarr", "Unsupported TV item", xbmcgui.NOTIFICATION_ERROR)

    except Exception as e:
        notify("Sonarr", "Error: {}".format(e), xbmcgui.NOTIFICATION_ERROR)
        log("Sonarr crash: {}".format(e), xbmcgui.LOGERROR)
