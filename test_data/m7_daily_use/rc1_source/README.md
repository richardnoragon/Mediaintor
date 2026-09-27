# Media-inator RC1 — personal KDE Docker deployment

RC1 is a local deployment-candidate label. Application version remains **0.1.0a1**, build **c08faf149723f3c0**. This bundle is not a public release and does not claim seven-day acceptance.

## Requirements

Verified target: Ubuntu 26.04.1 x86_64, KDE Wayland, Docker Engine 29.1.3 and Compose 2.40.3, normal-user Docker access, Python 3 on the host, and sufficient space for the image plus independent library/backup copies. The tested account has UID/GID 1000. Other host platforms/account mappings require qualification. Docker access grants root-equivalent host control.

The image includes the verified runtime and separately installed Calibre 9.2.1. No runtime download, application build, host Calibre installation or source checkout is needed. This is a native desktop application: there is no browser endpoint, authentication service, TLS proxy or published port. The Wayland socket grants display access; other host home directories, the Docker socket and development checkout are not mounted.

## First setup

Extract this archive into a stable directory outside the development checkout. From that directory, in your KDE terminal:

```sh
python3 manage.py verify-bundle
python3 manage.py load-image
python3 manage.py configure --state-root /absolute/path/to/rc1-test-state
```

Configure creates `.env` with your current UID/GID, Wayland socket and persistent-state location. It does not replace an existing `.env`. `.env.example` documents the fields. Keep secrets out of it. Store all application data outside the bundle.

With Calibre/readers closed, copy a complete dedicated Calibre test library into `rc1-test-state/library/` (metadata.db must be directly in that directory). Existing M7 users may instead configure the independent testing directory's `active` root, with its existing `home`, `library` and `import-sources`. Do not use the live library for this trial. No personal library is distributed in this bundle.

Then:

```sh
docker compose up -d
```

The init service installs the pinned package only if no installation exists, otherwise verifies the installed build and file inventory. It never silently upgrades a different build. The Hub opens as a native KDE window. On a fresh home, select `/data/library` in first-run guidance. Local import files belong under the host `import-sources` directory and appear inside `/data/import-sources`.

The Compose file pins the image ID and disallows pulling. Do not edit it or rebuild during the trial. `Dockerfile`, `entrypoint.py` and `verify.py` are included as source records; rebuilding may select newer distribution packages and does not reproduce the frozen candidate. The shipped image archive is authoritative.

## Normal startup, shutdown and diagnostics

```sh
docker compose up -d
docker compose ps -a
docker compose logs --tail 100 hub
```

Save/discard edits and close readers and the Hub normally **before** running:

```sh
docker compose down
docker compose up -d
```

`down` removes containers, not bind-mounted user data. It is not the application's Save/Discard dialog and must not be used to close unsaved work. No automatic container restart or pending-job resumption is configured. Never run another container or host Calibre against the same library concurrently. Start only one deployment against each persistent home; separate restorations use different host directories and Compose project names.

Closing the last Hub window exits its container; `up -d` starts it again. If initialization fails, inspect `docker compose logs init`. Do not delete application data, remove locks, relax version guards or replace the image to bypass an error. Use Help → Preview redacted diagnostics for export; Compose logs are raw local logs and may contain private information.

## Explicit backup and isolated restore

Close the Hub/readers and run `docker compose down` first. Then:

```sh
./backup.sh /absolute/path/to/rc1-test-state /absolute/path/to/backups/backup-001
./restore.sh /absolute/path/to/backups/backup-001 /absolute/path/to/restores/restore-001
```

The scripts copy the complete state root, including library, home, settings, viewer data, history and recovery, and verify hashes, symlinks and permissions. Destinations must not exist; source/destination may not overlap. Backup refuses when a running container mounts the source. No script stops containers, deletes originals or overwrites an existing environment. A failed copy is retained for inspection; a backup is complete only when its manifest exists and verifies.

For restored use, extract another copy of the frozen bundle or use a separate Compose env file. Configure `STATE_ROOT` to the restored directory and a distinct `COMPOSE_PROJECT_NAME` (for example mediainator-rc1-restore). Internal paths stay `/home/mediainator`, `/data/library` and `/data/import-sources`, preserving saved associations and recovery indexes without remapping to active data. Never mount the original environment alongside it. Confirm metadata, formats, settings and recovery before saving anything. Restoring does not automatically execute recovery tasks.

Keep backups on a separate disk if protection against disk failure is needed. The local test directories alone do not provide that protection. Recovery payloads saved outside the state root must be copied separately and their references reviewed; the qualified fixture uses only the state root.

## Freeze and seven-day trial

`FILES.json` freezes bundle contents, including the application package and Docker image archive. `RC1.json` records the image/application identities. Keep the supplied outer archive SHA-256 separately. These hashes provide integrity, not a publisher signature. `.env` is machine-specific and not distributed; record its hash together with the bundle hash before Day 1. No Git tag is claimed because the originating workspace had no Git repository.

Run this candidate for seven consecutive days of normal use, with daily launch/restart, activities, observations, recovery actions and pass/fail. Do not add features or change deployment during the week. Any fix changing the candidate restarts Day 1. Development elsewhere does not alter this bundle. Day 7 reviews existing artifacts and evidence; it does not automatically authorize publication or a version bump.

Known limits: exact dependency baseline; private-copy browsing; protected operations require Calibre/readers closed; a reader may need a keypress before displaying; no synchronization, additional modules, network service or automatic resumption. Tests on disposable copies do not replace the seven personal-use days.
