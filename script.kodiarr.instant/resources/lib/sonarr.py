import requests
import xbmc
import xbmcgui

from .common import get_setting, get_int, clean_url, notify, log
from .context import find_series_id


def get_context_info():
    info = {}
    info["series_id"], info["id_type"] = find_series_id()

    raw_season = xbmc.getInfoLabel("ListItem.Season")
    raw_episode = xbmc.getInfoLabel("ListItem.Episode")
    db_type = xbmc.getInfoLabel("ListItem.DBTYPE").lower()

    if db_type == "tvshow":
        info["type"] = "tvshow"
        info["season"] = None
        info["episode"] = None

    elif db_type == "season":
        info["type"] = "season"
        info["season"] = raw_season
        info["episode"] = None

    elif db_type == "episode":
        info["type"] = "episode"
        info["season"] = raw_season
        info["episode"] = raw_episode

    else:
        if raw_season.isdigit() and raw_episode.isdigit():
            info["type"] = "episode"
            info["season"] = raw_season
            info["episode"] = raw_episode
        elif raw_season.isdigit():
            info["type"] = "season"
            info["season"] = raw_season
            info["episode"] = None
        else:
            info["type"] = "tvshow"
            info["season"] = None
            info["episode"] = None

    return info


def run():
    sonarr_url = clean_url(get_setting("sonarr_url"))
    api = get_setting("sonarr_api")
    root = get_setting("sonarr_root")
    profile = get_int("sonarr_quality_profile", 1)

    if not sonarr_url or not api or not root:
        notify("Sonarr", "Please configure settings", xbmcgui.NOTIFICATION_ERROR)
        return

    info = get_context_info()
    series_id = info.get("series_id")

    if not series_id:
        notify("Sonarr", "No series ID found", xbmcgui.NOTIFICATION_ERROR)
        return

    headers = {"X-Api-Key": api}
    term = f"{info['id_type']}:{series_id}"

    try:
        lookup = requests.get(
            f"{sonarr_url}/api/v3/series/lookup?term={term}",
            headers=headers,
            timeout=10
        )

        if lookup.status_code != 200:
            notify("Sonarr", f"Lookup failed: {lookup.status_code}", xbmcgui.NOTIFICATION_ERROR)
            log(f"Sonarr lookup failed: {lookup.text}")
            return

        results = lookup.json()
        if not results:
            notify("Sonarr", "Show not found", xbmcgui.NOTIFICATION_ERROR)
            return

        series = results[0]
        title = series.get("title", "Unknown")
        series_db_id = series.get("id")

        # Missing -> add first
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
                f"{sonarr_url}/api/v3/series",
                json=payload,
                headers=headers,
                timeout=15
            )

            if add_resp.status_code != 201:
                notify("Sonarr", f"Add failed: {add_resp.status_code}", xbmcgui.NOTIFICATION_ERROR)
                log(f"Sonarr add failed: {add_resp.text}")
                return

            series_db_id = add_resp.json()["id"]

            # if user clicked the show itself, adding with searchForMissingEpisodes=True is enough
            if info["type"] == "tvshow":
                notify("Sonarr", f"Added '{title}'. Search started.")
                return

        # Already exists, or was added for season/episode
        if info["type"] == "tvshow":
            cmd = requests.post(
                f"{sonarr_url}/api/v3/command",
                json={"name": "SeriesSearch", "seriesId": series_db_id},
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Sonarr", f"Series search started: {title}")
            else:
                notify("Sonarr", "Series search failed", xbmcgui.NOTIFICATION_ERROR)
                log(f"Sonarr series search failed: {cmd.text}")
            return

        if info["type"] == "season":
            if not str(info["season"]).isdigit():
                notify("Sonarr", "Invalid season number", xbmcgui.NOTIFICATION_ERROR)
                return

            cmd = requests.post(
                f"{sonarr_url}/api/v3/command",
                json={
                    "name": "SeasonSearch",
                    "seriesId": series_db_id,
                    "seasonNumber": int(info["season"])
                },
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Sonarr", f"Season {info['season']} search started")
            else:
                notify("Sonarr", "Season search failed", xbmcgui.NOTIFICATION_ERROR)
                log(f"Sonarr season search failed: {cmd.text}")
            return

        if info["type"] == "episode":
            if not str(info["season"]).isdigit() or not str(info["episode"]).isdigit():
                notify("Sonarr", "Invalid episode info", xbmcgui.NOTIFICATION_ERROR)
                return

            ep_resp = requests.get(
                f"{sonarr_url}/api/v3/episode?seriesId={series_db_id}",
                headers=headers,
                timeout=15
            )

            if ep_resp.status_code != 200:
                notify("Sonarr", f"Episode lookup failed: {ep_resp.status_code}", xbmcgui.NOTIFICATION_ERROR)
                log(f"Sonarr episode lookup failed: {ep_resp.text}")
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
                f"{sonarr_url}/api/v3/command",
                json={"name": "EpisodeSearch", "episodeIds": [target["id"]]},
                headers=headers,
                timeout=10
            )

            if cmd.status_code in (200, 201):
                notify("Sonarr", f"S{int(info['season']):02d}E{int(info['episode']):02d} search started")
            else:
                notify("Sonarr", "Episode search failed", xbmcgui.NOTIFICATION_ERROR)
                log(f"Sonarr episode search failed: {cmd.text}")
            return

        notify("Sonarr", "Unsupported TV item", xbmcgui.NOTIFICATION_ERROR)

    except Exception as e:
        notify("Sonarr", f"Error: {e}", xbmcgui.NOTIFICATION_ERROR)
        log(f"Sonarr crash: {e}")
