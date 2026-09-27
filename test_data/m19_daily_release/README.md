# M19 daily-use release — 2026-09-27

Owner authorized master integration, daily-use promotion and native desktop Docker
packaging. Candidate `0.1.0a1-b016b423b7099943` is unchanged from desktop acceptance.

- Complete final source suite: **388 passed**.
- Installed M18/M19 core, Qt and audit suites inside the new Docker image: **93 passed**.
- Installer and package smoke test passed in the container.
- The initial container test run had one harness error because a fake executable
  was on noexec /tmp. Rerunning with exec-enabled test /tmp passed all 93 tests.
- Owner confirmed M18 playback/order/readability and M19 launch/readability,
  edit persistence, Markdown preview/save, internal links, logical trash/restore,
  and explicit mutually exclusive file handling. Earlier reports retain details.
- M16 active data copied with symlink preservation; 1,351 files matched by SHA-256
  before upgrade. Original M16 data verified unchanged after M19 launch.
- M19 uses the copied M16 profile, history, workspace and library. Acceptance data
  is excluded. Container-local mpv and ebook-viewer are configured for new modules.
- Menu: **Media-inator Everyday (M19)**. Fallback: **Media-inator M16 Last Known Good**.
- Daily installation: sibling `Mediaintor-M19-Everyday`; image and archive checksum
  are in `release.json`. The image archive is generated under `dist/` and excluded
  from Git. Source packaging and installation instructions are in `packaging/docker`.

This is a personal daily-use release of the scoped M19 foundation, not delivery
of deferred M20–M22 features. Native window/audio behavior of the new container
still benefits from owner observation; previous desktop acceptance used the same
application build on the host. No remote repository is configured, so publication
or pushing is outside this local integration.
