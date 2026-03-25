# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
import tempfile


SDH_MARKERS_RE = re.compile(
    r"(sdh|cc|hi|hearing.?impaired|closed.?caption|forced)",
    re.IGNORECASE
)


def _log(log_fn, message, level="debug"):
    if log_fn:
        log_fn(message, level)


def _find_tool(name, custom_path=None):
    if custom_path:
        if os.path.isfile(custom_path):
            return custom_path
        return None
    return shutil.which(name)


def _is_local_path(path):
    if not path:
        return False

    lowered = path.lower()
    if lowered.startswith((
        "plugin://",
        "http://",
        "https://",
        "smb://",
        "nfs://",
        "dav://",
        "ftp://",
        "sftp://",
        "special://",
    )):
        return False

    return bool(re.match(r"^[a-zA-Z]:[\\/]", path)) or path.startswith("/")


def _build_output_path(output_dir, media_path, source_lang_iso):
    base_name = os.path.splitext(os.path.basename(media_path))[0]
    safe_base = re.sub(r'[<>:"/\\|?*]+', "_", base_name).rstrip(". ")
    return os.path.join(output_dir, "{0}.{1}.srt".format(safe_base, source_lang_iso))


def _run_command(command, log_fn=None):
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as exc:
        _log(log_fn, "Command failed to start: {0} | Error: {1}".format(command[0], exc), "error")
        return False, "", str(exc)

    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip()
        return False, completed.stdout or "", stderr

    return True, completed.stdout or "", ""


def _parse_mkvinfo_tracks(output, source_variants, source_lang_name):
    source_tokens = set(v.lower() for v in source_variants)
    source_name = (source_lang_name or "").strip().lower()
    tracks = []

    current = None

    def finalize_track():
        if not current:
            return
        if current.get("is_subtitle") and current.get("is_source_language") and current.get("track_id"):
            tracks.append(
                {
                    "track_id": current["track_id"],
                    "is_sdh": current.get("is_sdh", False),
                    "name": current.get("name", ""),
                }
            )

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if re.match(r"^\|\s+\+\sTrack$", line):
            finalize_track()
            current = {
                "track_id": None,
                "is_subtitle": False,
                "is_source_language": False,
                "is_sdh": False,
                "name": "",
            }
            continue

        if current is None:
            continue

        track_id_match = re.search(
            r"track ID for mkvmerge & mkvextract:\s*([0-9]+)",
            line,
            re.IGNORECASE
        )
        if track_id_match:
            current["track_id"] = track_id_match.group(1)

        if "Track type: subtitles" in line:
            current["is_subtitle"] = True

        for pattern in (
            r"Language:\s*([a-zA-Z0-9_-]+)",
            r"Language \(IETF BCP 47\):\s*([a-zA-Z0-9_-]+)",
        ):
            lang_match = re.search(pattern, line, re.IGNORECASE)
            if lang_match:
                lang_token = lang_match.group(1).lower()
                primary_token = lang_token.split("-")[0]
                if lang_token in source_tokens or primary_token in source_tokens:
                    current["is_source_language"] = True

        name_match = re.search(r"\+\sName:\s*(.+)$", line)
        if name_match:
            track_name = name_match.group(1).strip()
            current["name"] = track_name
            lowered_name = track_name.lower()
            if source_name and source_name in lowered_name:
                current["is_source_language"] = True
            if SDH_MARKERS_RE.search(track_name):
                current["is_sdh"] = True

    finalize_track()
    return tracks


def _pick_best_track(tracks):
    if not tracks:
        return None

    for track in tracks:
        if not track.get("is_sdh"):
            return track
    return tracks[0]


def _looks_like_ass_or_ssa(path):
    try:
        with open(path, "rb") as handle:
            header = handle.read(512)
    except Exception:
        return False

    try:
        text_header = header.decode("utf-8", errors="ignore")
    except Exception:
        return False

    return "[Script Info]" in text_header or "[V4+ Styles]" in text_header


def try_extract_embedded_subtitle(
    media_path,
    output_dir,
    source_lang_iso,
    source_lang_name,
    source_variants,
    mkvinfo_path=None,
    mkvextract_path=None,
    ffmpeg_path=None,
    log_fn=None
):
    if not _is_local_path(media_path):
        return {"success": False, "reason": "media_path_not_local"}

    if not _is_local_path(output_dir):
        return {"success": False, "reason": "output_dir_not_local"}

    if not media_path.lower().endswith(".mkv"):
        return {"success": False, "reason": "unsupported_container"}

    if not os.path.isfile(media_path):
        return {"success": False, "reason": "media_file_missing"}

    if not os.path.isdir(output_dir):
        return {"success": False, "reason": "output_dir_missing"}

    output_path = _build_output_path(output_dir, media_path, source_lang_iso)
    if os.path.isfile(output_path) and os.path.getsize(output_path) > 100:
        _log(log_fn, "Embedded subtitle output already exists: {0}".format(output_path))
        return {"success": True, "output_path": output_path, "reason": "already_exists"}

    mkvinfo = _find_tool("mkvinfo", mkvinfo_path)
    mkvextract = _find_tool("mkvextract", mkvextract_path)
    if not mkvinfo or not mkvextract:
        return {"success": False, "reason": "required_tools_missing"}

    ok, mkvinfo_output, mkvinfo_error = _run_command([mkvinfo, media_path], log_fn=log_fn)
    if not ok:
        _log(log_fn, "mkvinfo failed for {0}: {1}".format(media_path, mkvinfo_error), "error")
        return {"success": False, "reason": "mkvinfo_failed"}

    tracks = _parse_mkvinfo_tracks(mkvinfo_output, source_variants, source_lang_name)
    best_track = _pick_best_track(tracks)
    if not best_track:
        return {"success": False, "reason": "no_matching_subtitle_track"}

    fd, temp_path = tempfile.mkstemp(prefix="translatarr_extract_", suffix=".sub", dir=output_dir)
    os.close(fd)
    try:
        extract_spec = "{0}:{1}".format(best_track["track_id"], temp_path)
        ok, _, extract_error = _run_command([mkvextract, "tracks", media_path, extract_spec], log_fn=log_fn)
        if not ok:
            _log(log_fn, "mkvextract failed for {0}: {1}".format(media_path, extract_error), "error")
            return {"success": False, "reason": "mkvextract_failed"}

        if _looks_like_ass_or_ssa(temp_path):
            ffmpeg = _find_tool("ffmpeg", ffmpeg_path)
            if not ffmpeg:
                return {"success": False, "reason": "ffmpeg_required_for_conversion"}

            ok, _, ffmpeg_error = _run_command(
                [ffmpeg, "-y", "-loglevel", "error", "-i", temp_path, output_path],
                log_fn=log_fn
            )
            if not ok:
                _log(log_fn, "ffmpeg conversion failed for {0}: {1}".format(temp_path, ffmpeg_error), "error")
                return {"success": False, "reason": "ffmpeg_conversion_failed"}
        else:
            shutil.move(temp_path, output_path)
            temp_path = None

        if not os.path.isfile(output_path) or os.path.getsize(output_path) <= 100:
            return {"success": False, "reason": "output_invalid"}

        return {
            "success": True,
            "output_path": output_path,
            "track_id": best_track["track_id"],
            "was_sdh": best_track.get("is_sdh", False),
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
