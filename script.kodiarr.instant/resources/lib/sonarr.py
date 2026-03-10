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
from .context import get_sonarr_context


def run():
    sonarr_url = clean_url(get_setting("sonarr_url"))
    api_key = get_setting("sonarr_api")
    root_folder = get_setting("sonarr_root")
    quality_profile_id = get_int_setting("sonarr_quality_profile", 8)

    if not ensure_required("Sonarr", sonarr_url, api_key, root_folder):
        return

    info = get_sonarr_context()
    series_id = info.get("series_id")

    if not series_id:
        debug_path = ""
        try:
            import xbmc
            debug_path = xbmc.getInfoLabel("ListItem.Path")
        except Exception:
            pass

        notify("Sonarr", "ID not found. Check logs.", xbmcgui.NOTIFICATION_ERROR)
        log("Series ID not found. Path: {}".format(debug_path), xbmcgui.LOGERROR)
        return

    headers = {"X-Api-Key": api_key}

    try:
        lookup_term = "{}:{}".format(info["id_type"], series_id)
        lookup_url = "{}/api/v3/series/lookup?term={}".format(sonarr_url, lookup_term)
        r = requests.get(lookup_url, headers=headers, timeout=10)

        if r.status_code != 200:
            notify("Sonarr", "API Error: {}".format(r.status_code), xbmcgui.NOTIFICATION_ERROR)
            log("Lookup failed: {}".format(r.text), xbmcgui.LOGERROR)
            return

        results = r.json()
        if not results:
            notify("Sonarr", "Show not found in Sonarr lookup.", xbmcgui.NOTIFICATION_ERROR)
            return

        series = results[0]
        series_db_id = series.get("id")
        series_title = series.get("title", "Unknown")

        if not series_db_id:
            notify("Sonarr", "Adding '{}'...".format(series_title))
            should_search_missing = (info["type"] == "tvshow")

            payload = dict(series)
            payload.update({
                "qualityProfileId": quality_profile_id,
                "rootFolderPath": root_folder,
                "monitored": True,
                "addOptions": {"searchForMissingEpisodes": should_search_missing}
            })

            r_add = requests.post(
                "{}/api/v3/series".format(sonarr_url),
                json=payload,
                headers=headers,
                timeout=15
            )

            if r_add.status_code == 201:
                series_db_id = r_add.json()["id"]
            else:
                notify("Sonarr", "Add failed: {}".format(r_add.status_code), xbmcgui.NOTIFICATION_ERROR)
                log("Add failed body: {}".format(r_add.text), xbmcgui.LOGERROR)
                return

        if info["type"] == "tvshow":
            notify("Sonarr", "Searching series: {}".format(series_title))
            cmd = {"name": "SeriesSearch", "seriesId": series_db_id}
            requests.post("{}/api/v3/command".format(sonarr_url), json=cmd, headers=headers, timeout=10)

        elif info["type"] == "season":
            notify("Sonarr", "Searching season {}".format(info["season"]))
            cmd = {
                "name": "SeasonSearch",
                "seriesId": series_db_id,
                "seasonNumber": int(info["season"])
            }
            requests.post("{}/api/v3/command".format(sonarr_url), json=cmd, headers=headers, timeout=10)

        elif info["type"] == "episode":
            notify("Sonarr", "Searching S{}E{}".format(info["season"], info["episode"]))

            ep_url = "{}/api/v3/episode?seriesId={}".format(sonarr_url, series_db_id)
            all_eps_resp = requests.get(ep_url, headers=headers, timeout=15)

            if all_eps_resp.status_code != 200:
                notify("Sonarr", "Episode lookup failed: {}".format(all_eps_resp.status_code), xbmcgui.NOTIFICATION_ERROR)
                log("Episode lookup body: {}".format(all_eps_resp.text), xbmcgui.LOGERROR)
                return

            all_eps = all_eps_resp.json()

            target_ep = next(
                (
                    e for e in all_eps
                    if e["seasonNumber"] == int(info["season"])
                    and e["episodeNumber"] == int(info["episode"])
                ),
                None
            )

            if target_ep:
                cmd = {"name": "EpisodeSearch", "episodeIds": [target_ep["id"]]}
                requests.post("{}/api/v3/command".format(sonarr_url), json=cmd, headers=headers, timeout=10)
            else:
                notify("Sonarr", "Episode not found in Sonarr DB.", xbmcgui.NOTIFICATION_ERROR)

    except Exception as e:
        notify("Sonarr", "Crash: {}".format(str(e)), xbmcgui.NOTIFICATION_ERROR)
        log("Crash: {}".format(str(e)), xbmcgui.LOGERROR)
