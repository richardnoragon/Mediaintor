# M13 everyday promotion

Authorized and completed 2026-09-24 after owner confirmed normal shutdown. M13-G remains accepted with unchanged criteria.

Use **Media-inator Everyday (M13)** from KDE. The running installation is labeled **M13 Everyday**, accepted build `0.1.0a1-db6a7fb8885f9bd9`. M12 is stopped and retained as **Media-inator M12 Rollback**. M11 is unchanged.

Verified pre-promotion backups exist for both installations. All 966 M13 and 769 M12 active files matched their backups after relabeling. Only deployment display labels and existing desktop entry names changed; no library migration, package replacement, duplicate launcher, or publication occurred. Historical directory and desktop filenames remain intact to preserve paths.

[Machine-readable evidence](promotion.json). To reverse the labels, close the affected applications normally and restore only docker-compose.yml and the desktop entries from each pre-m13-everyday-promotion backup. Do not restore old library/user data over newer everyday work. M12 retains its own older data; it does not automatically receive M13 changes.
