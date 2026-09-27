# M18/M19 implementation and verification follow-up

Date: 2026-09-27. Implemented candidate: **0.1.0a1-b016b423b7099943**. The outstanding owner desktop checks are **passed**; formal M18-G/M19-G closure and promotion are not recorded here. This completes the automated follow-up described below, not the later M20–M22 Paper-inator feature scope.

## Implemented fixes

- Multiple Paper drafts and cross-module Hub close choices are collected before any Save/Discard action. Cancel changes nothing. Workspace transitions also collect multiple draft decisions together. Saves precede discards; a failed save stops continuation, while completed confirmed saves remain saved.
- Paper recovery validates library/schema/profile before touching files. A per-library file-operation lock spans staging through commit/rollback; recovery defers while that operation is active. Abandoned staging cleanup can no longer remove a foreign profile's staging file before rejection.
- Confirmed Paper imports execute in a background executor, one document at a time. Qt widgets are updated only on the GUI thread; preview decisions are disabled during application. Managed copying and fingerprinting check cancellation. Committed documents are retained and unimported documents remain identifiable.
- Confirmed M18 metadata precedence has an explicit conflicting-path regression test. Confirmed M19 logical trash is retained, without physical relocation.

## Verification evidence

| Verification | Result | Evidence |
| --- | --- | --- |
| Full source regression at first fix checkpoint | 387 passed | final_regression.log |
| Workspace tests after follow-up change | 33 passed | workspace_fix.log |
| Targeted audit regressions, including background-worker responsiveness | 7 passed | new_regressions.log |
| Native Wayland M18/M19 plus new regression tests | 42 passed | final_wayland.log |
| Final installed package core/Qt/audit tests | 93 passed | final_package/installed_tests.log |
| Final package installer/reinstall, launcher startup and desktop-file validation | Passed | final_package/report.json |
| Populated library install, upgrade, rollback, re-upgrade, uninstall, reinstall | All preserved data bytes; retained item/note/album readable | upgrade/report.json |
| Real PDF text extraction/search and preserved original; real tagged FLAC/MP3 grouping | Passed during preceding review | real_media/report.json |

Counts overlap and must not be added together as independent tests. The full run preceded the final workspace/UI-control refinement and the seventh new test; subsequent affected-suite, native and installed runs cover those final changes. No Qt stand-in was used for these results.

Final archive SHA-256: `e4d70450526a654274e73c15151cca48355191cd2625a479a16d3402ae1cbceb`.

Installer tests redirect integration paths to the review folder and use isolated XDG directories. Runtime checks and installer logic execute normally. This is not a fresh operating-system certification. Everyday and existing M17 profiles were not changed.

## Desktop acceptance environments

The application menu now contains **Media-inator M18 Acceptance Testing** and **Media-inator M19 Acceptance Testing**. Both pin the verified frozen release above and have separate config/data/cache and catalogs under `desktop_m18` / `desktop_m19` in this review directory. Book-inator uses sample mode. M18 is prepopulated with generated audio; M19 seeds a generated research PDF on first launch. The fixtures contain no personal research or music.

`launch_acceptance.py 18` opens M18; `launch_acceptance.py 19` opens M19. Both isolated launchers were used for the owner desktop checks recorded below.

## Owner desktop acceptance results

- M18: external-player playback and track order confirmed by the owner on 2026-09-27 using M18 Playback Check (eight seconds at 440 Hz, followed by eight seconds at 660 Hz) in Elisa. The original 0.15-second fixtures were unsuitable for audible acceptance; replacement fixtures decoded successfully and their durations were verified with ffprobe (`playback_check/verification.json`). Owner also confirmed that all Music-inator controls, text, album details and track information are legible on 2026-09-27; screenshot supplied. Playback and readability desktop checks are passed.
- M19: owner confirmed successful launch, sample research item visibility, and Home dashboard readability on 2026-09-27 (screenshot supplied). Owner confirmed item editing and persistence: Authors changed to Acceptance Tester, saved, and retained after reopening the editor (screenshot supplied). Owner confirmed Markdown heading, bold text and two bullet points render correctly, and Acceptance note was saved (screenshot supplied). This note is a Summary attached to Preservation research fixture. Owner confirmed that clicking the Preservation research fixture link in Acceptance note navigates to the item in Library. Owner confirmed moving the research item to logical Trash: Library shows zero items and zero notes, and Trash lists Preservation research fixture and 1 more (screenshot supplied). Owner confirmed restoration of both the item and attached note; screenshot shows one item, one note, and the restored Markdown content and item link. Owner confirmed the required managed/reference choice: neither initially selected, explanatory labels understood, and selecting one deselects the other; screenshots supplied. The outstanding desktop checklist is complete. Automated functional evidence remains separately reported above.
- All owner checks requested in this follow-up are now confirmed. Formal gate closure requires reconciliation with the complete milestone criteria; this record does not claim additional manual checks or authorize promotion. Everyday remains unchanged.

The initial audit in `review.md` is historical. Its three implementation findings are addressed by this follow-up; its two product questions have both been answered and documented.
