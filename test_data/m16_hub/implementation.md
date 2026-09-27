# M16 first implementation

Implemented module registry and guarded tiles, Settings, profile/device appearance, atomic rollback and Retry, confirmed appearance-only reset, responsive module scrolling and existing Activity/recovery integration. M15 Everyday is untouched.

Validation: 266 source tests passed. Final package verification passes clean install, reinstall/uninstall retention, desktop entry and installed targeted tests (see polish_package_verification.json). Tests run offscreen with Qt 6.10.2. Local virtualenv lacks PyQt6; supported system Python was used.

Desktop acceptance remains OPEN. Check real KDE System/Light/Dark, accents, sizes/density, open/new dialogs, reset/cancel, restart and unchanged reader presentation. System accent follows the startup Qt palette; restart to pick up desktop accent changes. No M16 promotion.

## Placeholder contrast correction

Candidate 0.1.0a1-c663cfd06375b1f1 explicitly sets opaque PlaceholderText for active, inactive and disabled palette groups using the effective field background. Seven focused tests pass, including 4.5:1 contrast checks across theme transitions on existing/new fields. Updated isolated package validation passed (see polish_package_verification.json). Prepared but not installed: the M16 Hub was still running. Close normally before backup/update. Owner desktop checks through reopening 104 books are recorded in desktop_acceptance.json. M15 untouched.

Contrast correction installed after owner confirmed M16 closed. Verified backup created; all 490 retained files unchanged. Package smoke passes for build c663cfd06375b1f1. Desktop placeholder verification pending. M15 Everyday untouched.

Owner desktop confirmation: dark search placeholder is clearly readable in Find / review on build c663cfd06375b1f1, with 104 of 104 books shown. Placeholder contrast issue resolved. This supersedes the pending placeholder verification above; it does not promote M16 or establish untested milestone criteria.

M16-G PASSED and M16 promoted to Everyday by owner request. M15 retained as stopped rollback. This supersedes earlier pending acceptance/promotion notes. See acceptance.json and promotion.json.
