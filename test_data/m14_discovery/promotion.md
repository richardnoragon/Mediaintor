# M14 Everyday promotion

Owner-authorized promotion completed 2026-09-24 after normal shutdown. Use **Media-inator Everyday (M14)** from KDE. Build **0.1.0a1-9cf2b6503ae20a40**, running label **M14 Everyday**. M13 is stopped and retained as **Media-inator M13 Rollback**. M12 and M11 are unchanged.

Both pre-promotion backups were verified. All 1,133 M14 and 966 M13 active files matched their backups after relabeling. Only deployment labels and existing desktop display names changed; no library migration or publication occurred. M14 keeps its accepted 104-book library. Historical directory and desktop filenames remain unchanged to preserve paths.

Runtime inspection confirms M14 running with the Everyday label and M13 stopped. See [machine-readable evidence](promotion.json).

To reverse labels, close affected applications normally and restore only docker-compose.yml and desktop entries from their pre-m14-everyday-promotion backups. Do not overwrite newer library/user data with old backups. M13 retains its own data and does not automatically receive M14 changes.

M14-G remains passed. Deferred M14-UI-01 remains open. Historical M7 observation remains unchanged.
