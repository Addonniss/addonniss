import xbmc
from urllib.parse import urlparse, parse_qs


def get_movie_id():
    prop_id = xbmc.getInfoLabel("ListItem.Property(tmdb_id)")
    if prop_id and prop_id.isdigit():
        return prop_id, "tmdb"

    imdb = xbmc.getInfoLabel("ListItem.IMDBNumber")
    if imdb and imdb.startswith("tt"):
        return imdb, "imdb"

    std_id = xbmc.getInfoLabel("ListItem.TmdbId")
    if std_id and std_id.isdigit():
        return std_id, "tmdb"

    return None, None


def find_series_id():
    tmdb_prop = xbmc.getInfoLabel("ListItem.Property(tmdb_id)")
    tvdb_prop = xbmc.getInfoLabel("ListItem.Property(tvdb_id)")

    if tmdb_prop and tmdb_prop.isdigit():
        return tmdb_prop, "tmdb"

    if tvdb_prop and tvdb_prop.isdigit():
        return tvdb_prop, "tvdb"

    path_item = xbmc.getInfoLabel("ListItem.Path")
    if path_item and path_item.startswith("plugin://"):
        try:
            parsed = urlparse(path_item)
            params = parse_qs(parsed.query)
            if "tmdb_id" in params:
                return params["tmdb_id"][0], "tmdb"
            if "tvdb_id" in params:
                return params["tvdb_id"][0], "tvdb"
        except Exception:
            pass

    path_container = xbmc.getInfoLabel("Container.FolderPath")
    if path_container and path_container.startswith("plugin://"):
        try:
            parsed = urlparse(path_container)
            params = parse_qs(parsed.query)
            if "tmdb_id" in params:
                return params["tmdb_id"][0], "tmdb"
            if "tvdb_id" in params:
                return params["tvdb_id"][0], "tvdb"
        except Exception:
            pass

    return None, None
