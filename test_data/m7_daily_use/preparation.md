# M7-01 preparation — 2026-09-22

**M7-01 COMPLETE for inventory and durable location preparation. M7-G OPEN.** No installation, Docker image build or seven-day trial has started. Docker is the user's revised deployment requirement; M6 qualification does not automatically qualify a container runtime.

[Inventory and copy verification](preparation_report.json) found no normal-account installation, launcher, desktop file or application state at the expected Media-inator locations. Docker CLI was absent from PATH and the default Docker socket was absent. This does not exclude a remote engine or nonstandard installation.

## Durable locations

All paths below now reside in the separate sibling `../Mediaintor-M7-Testing/`, outside the development checkout. See [separation verification](separation_report.json). The previous project-local `m7_workspace/` remains untouched as an unused preparation copy; it is not the active M7 location.

| Path | Purpose / current contents |
| --- | --- |
| `active/library/` | Fresh 101-book copy of the registered M4 disposable seed; contents hash-verified, with an updated disposable marker. |
| `active/home/` | Empty persistent container user home; will hold installation/configuration/history/recovery and viewer configuration. |
| `active/import-sources/` | Empty location for independently prepared import source fixtures. |
| `backups/` | Empty destination for dated manual library and application-data copies. |
| `restores/` | Empty destination for separate restore environments. |
| `artifacts/` | Accepted M6 bundle, checksum verified against gate record. |
| `evidence/library_manifest.json` | SHA-256 inventory of the prepared library. |

No live library was accessed. The seed was unchanged during copying; destination matches all seed file contents except the intentionally updated disposable marker. The copied database contains 101 books and passes SQLite integrity_check under immutable read, with no WAL file present. Ordinary read-only SQLite opening returned a disk I/O error: **writable database/locking behavior on this filesystem remains an explicit M7-02 prerequisite**, not a passed check. Do not start daily use until real adapter operations succeed.

These are same-filesystem manual-test locations, not protection against loss of the entire disk. Backup and restore directories are prepared but no completed backup/restore validation is claimed.

## Docker handoff to M7-02

- Install/build the application inside Docker; do not substitute a native host installation. GUI choice confirmed: native KDE windows, launched through a host KDE menu shortcut; container display integration remains to be qualified.
- Retain host directories as explicit bind mounts so state survives container replacement. Docker documentation: [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/). Mount only the selected active test environment; restore testing must mount only the selected restore environment at identical internal paths.
- Proposed stable internal paths: `/home/mediainator` for persistent home, `/data/library` and `/data/import-sources`. Ensure the disposable-library marker and any stored references reflect actual container paths before use. Never expose backup/restore trees or the original library to the active application unnecessarily.
- Run the application as a non-root user with mapped ownership. Keep Calibre and its viewer in the same application environment; it remains a separately installed prerequisite, not embedded in the application bundle.
- Qualify exact dependency versions inside the image, Qt display/viewer startup, persistence, permissions and database locks. Do not relax compatibility guards merely to make an available image run.
- Container process isolation may prevent existing process checks from seeing host Calibre/readers. Use only the dedicated mounted library and qualify access/locking explicitly. Do not claim host-wide reader detection works without evidence.
- Record image digest and launch/mount configuration alongside the package hash; fixes changing this candidate deployment reset the seven-day count. Container deletion must retain persistent data; never use volume deletion as the uninstall test.
- Implement and verify a host KDE menu shortcut for native container windows. No browser desktop is planned.

Next: M7-02 Docker runtime/design, prerequisites and installation qualification. No Docker installation or daemon configuration was attempted during M7-01.

Independent candidate: `../Mediaintor-M7-Testing/candidate.json` pins the accepted package hash. Its package and data copies are independent of development rebuilds. Docker deployment files belong in its `deployment/` directory; never mount the development checkout into the test application. Branch development alone does not reset the trial, provided the tested candidate is unchanged. Docker installation is still pending.

M7-02 follow-up: normal host SQLite writing and competing-writer locking passed outside the sandbox, and the prepared library opened read-only with 101 books. The earlier disk I/O result did not recur outside sandbox. Container filesystem/runtime checks remain pending. Docker deployment files are prepared but not executed; Docker installation requires local administrator authentication.
