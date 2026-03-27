# Translatarr Remote Extractor

Docker-first companion service for `service.translatarr`.

Purpose:
- provide embedded subtitle extraction for platforms where local tools are unavailable or impractical
- support Android / NVIDIA Shield clients through a remote HTTP API
- keep extraction logic separate from the Kodi addon runtime

Planned v1 API:
- `GET /health`
- `POST /extract`

Planned capabilities:
- bearer-token authentication
- path mapping from `smb://` and UNC paths to server-mounted paths
- `MKV` extraction via `mkvinfo` + `mkvextract`
- `MP4` extraction via `ffprobe` + `ffmpeg`
- extracted subtitle caching

Deployment targets:
- Docker Compose
- Portainer stacks

Current state:
- project scaffold created
- v1 API contract added
- bearer-token authentication added
- path-mapping config added
- `MKV` extraction path added
- extracted subtitle cache added for `MKV`
- `MP4` extraction path added

## Published Image

Normal users should deploy the published container image:

```text
ghcr.io/addonniss/translatarr-remote-extractor:latest
```

The GitHub Actions workflow publishes this image automatically when the project changes.

## Docker Compose

1. Place this project on the server that can access your media files.
2. Review [docker-compose.yml](C:/Users/angel/repository.addonniss/translatarr-remote-extractor/docker-compose.yml).
3. Set a real `EXTRACTOR_API_TOKEN`.
4. Mount your media into the container as read-only.
5. Adjust `EXTRACTOR_PATH_MAPS` so Kodi playback paths resolve to the mounted server paths.
6. Start the service:

```bash
docker compose up -d
```

For normal user deployment, the default compose file uses the published GHCR image.

For local development from source, use:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Example media mount:

```yaml
volumes:
  - ./cache:/cache
  - ./work:/work
  - /data/media:/data/media:ro
```

Example path mapping:

```yaml
environment:
  EXTRACTOR_PATH_MAPS: >
    [
      {"from": "smb://192.168.0.200/SSD-Data/", "to": "/data/media/"},
      {"from": "\\\\192.168.0.200\\SSD-Data\\", "to": "/data/media/"}
    ]
```

Health check example:

```bash
curl http://SERVER_IP:8097/health
```

## Portainer

You can deploy the same service as a Portainer stack.

Recommended flow:

1. Open Portainer.
2. Go to `Stacks`.
3. Create a new stack named `translatarr-remote-extractor`.
4. Paste the contents of [docker-compose.yml](C:/Users/angel/repository.addonniss/translatarr-remote-extractor/docker-compose.yml).
5. Edit:
   - `EXTRACTOR_API_TOKEN`
   - media volume mounts
   - `EXTRACTOR_PATH_MAPS`
6. Deploy the stack.

Portainer notes:
- keep media mounts read-only
- keep `cache` and `work` on writable storage
- if Kodi sends `smb://` or UNC paths, make sure they are translated to paths that exist inside the container

## Image Publishing

This project is set up to publish a container image to GHCR using:

- [translatarr_remote_extractor_image.yml](C:/Users/angel/repository.addonniss/.github/workflows/translatarr_remote_extractor_image.yml)

Published image name:

```text
ghcr.io/addonniss/translatarr-remote-extractor:latest
```

The workflow currently publishes:
- `latest`
- a commit-SHA tag

## Environment Variables

- `EXTRACTOR_API_TOKEN`
  - optional bearer token required by `/extract`
- `EXTRACTOR_CACHE_DIR`
  - writable cache directory inside the container
- `EXTRACTOR_WORK_DIR`
  - writable temporary extraction directory
- `EXTRACTOR_TIMEOUT`
  - timeout in seconds for `mkvinfo` and similar probe steps
- `EXTRACTOR_FFMPEG_TIMEOUT`
  - timeout in seconds for `ffmpeg` extraction
- `EXTRACTOR_PATH_MAPS`
  - JSON array mapping Kodi playback paths to server-mounted paths

## Important Path Rule

The extractor host must be able to open the same video file that Translatarr requests.

That means one of these must be true:
- Kodi already provides a filesystem path the server can access directly
- path mapping converts `smb://` or UNC playback paths into valid mounted container paths
