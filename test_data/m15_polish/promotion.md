# M15 Everyday promotion

Owner-authorized promotion completed after normal shutdown. Launch **Media-inator Everyday (M15)**. Running label: **M15 Everyday**, build **0.1.0a1-47d071de892ca535**. M14 remains stopped as **Media-inator M14 Rollback**; M13 and older installations unchanged.

Verified backups: each installation's backups/pre-m15-everyday-promotion. After relabeling, all 1,186 M15 and 1,133 M14 active files matched backups. Only deployment labels and existing launcher display names changed; no library migration or publication. Runtime verification confirms M15 running with Everyday label, M14 stopped.

To reverse labels, close affected applications normally and restore only docker-compose.yml and desktop entries from their pre-promotion backups. Do not overwrite newer library/user data with older backups. Rollback installations retain their own independent data.

The seven-day observation condition is retired as obsolete by explicit owner instruction; this does not claim the trial was performed. M15-G remains passed. See promotion.json for machine-readable evidence.
