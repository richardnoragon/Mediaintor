# RC1 pre-trial preparation and freeze

**RC1 built, qualified and frozen locally. 18 checks passed. Personal RC1 acceptance confirmed; seven-day trial started 2026-09-22, Day 1 result pending. M7-G OPEN. Nothing published.**

The owner approved Compose, a self-contained deployment bundle and backup/restore scripts as pre-trial additions. This explicitly extends the earlier manual-only deployment procedure. No web service, authentication/TLS subsystem, public distribution or application version bump was added.

## Frozen deliverables

Independent directory: `../Mediaintor-M7-Testing/releases/mediainator-rc1/`.

Local distributable archive: `../Mediaintor-M7-Testing/releases/mediainator-rc1.tar.gz` (520,767,345 bytes), with adjacent SHA-256 file.

Archive SHA-256: `cb8ba49f26f4301dd5f116ae4ef758547c329d164638cbe04ad298a274a13513`.

Contents include Dockerfile/source records, `docker-compose.yml`, `.env.example`, README, `backup.sh`, `restore.sh`, supporting Python scripts, the accepted application archive, full Docker image archive, `RC1.json` and `FILES.json`. It contains no personal library or user .env. Images are loaded locally, not rebuilt or downloaded at startup. Docker/Compose and a configured compatible KDE Wayland host remain prerequisites.

The image and app remain the M7-03 corrected build. Deployment files are new RC1 scope. `.env` is machine-specific, generated separately and hashed in the [freeze record](rc1_freeze.json). All seven days must use these fixed application/image/deployment/configuration identities. No Git tag was created because the workspace is not a Git repository; manifest/archive checksums identify RC1 without claiming a source-control tag.

## Qualification

[18 checks passed from the extracted archive](rc1_qualification.json):

- Bundle integrity and bundled-image loading without rebuilding.
- Compose configuration, fresh-home installation, native Hub startup and isolated mounts.
- `up -d`, `down`, `up -d` with retained settings on a clean disposable fixture.
- Backup refuses running-container sources, existing destinations and overlapping paths.
- Successful whole-state backup and isolated restore with verified contents.
- Restore refuses existing destinations and corrupted backups.
- Restored application starts after container removal and passes 101-book/runtime/snapshot/Calibre adapter checks.
- Bundle files and original active library remain unchanged throughout qualification.

The Compose lifecycle test used clean automated fixtures with no unsaved user edits. Users must close readers and the Hub normally before `down`; Compose shutdown is not a replacement for Save/Discard review. The tests used the existing host Docker daemon with freshly extracted files/state, not a separate clean host or seven-day stability run.

Runtime constraints: pinned local image, no pulls, no automatic restarts, no network, dropped capabilities, non-root app user, read-only image, persistent bind-mounted state and only native Wayland display sharing. First initialization installs once; a changed/modified installed build fails verification instead of silently upgrading.

The new scripts are explicit local copy/restore utilities, not application backup controls. They do not stop containers, delete source data, overwrite existing destinations or automatically apply recovery. The existing M7-03 manual procedure remains valid.

## Personal handoff

KDE shortcut is now **Media-inator RC1 (Docker Compose)**. It launches the configured frozen bundle against the separate M7 active state. Do not use the previous direct Docker launcher during the formal trial.

From the configured RC1 directory:

```sh
docker compose up -d
# Close Hub/readers normally first:
docker compose down
```

Asked the owner to confirm catalog/reader operation and KDE relaunch, then choose Day 1. No pass result, start date or elapsed use day is inferred. Next is M7-04 on exactly RC1; any adopted fix changing this candidate restarts the consecutive-day count. M7-G still requires the actual week and final evidence review.

References for implementation behavior: [Compose services](https://docs.docker.com/reference/compose-file/services/), [Docker image save/load archive](https://docs.docker.com/reference/cli/docker/image/save/).

Subsequent user confirmation: all six acceptance checks passed and Day 1 authorized for 2026-09-22. [Current trial record](trial_start.json). Freeze-time records retain their historical not-started state; frozen artifacts are unchanged.
