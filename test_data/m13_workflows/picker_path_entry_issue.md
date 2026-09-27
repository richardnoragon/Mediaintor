# M13-PICKER-01 — Editable and pasteable import paths

Status: FIXED AND INSTALLED; actual KDE path-entry verification pending. Priority: high within M13 workflow clarity. Reported during KDE acceptance on build `0.1.0a1-911ac9451958810d`.

## Observed behavior

Owner reports that Choose ebook files does not allow editing or pasting a path. The fixture was selected using the path dropdown. The import help explicitly promises that a full path can be pasted. Earlier paste-capability assumptions are superseded by this report. The screenshot shows the resulting preview, not the picker itself; the exact picker focus/backend cause is not established.

## Reproduction

1. Open M13 Development → Import ebooks → Choose ebook files.
2. Attempt to type and paste `/data/import-sources/M13 Final Acceptance.epub` using visible path controls.
3. Owner reports those actions unavailable, while dropdown navigation works.

## Required work

- Reproduce the actual KDE picker behavior and inspect focus, editable controls and dialog backend. Source entry points are `mediainator/import_dialog.py` file/folder chooser methods using QFileDialog static methods.
- Provide a clearly labeled, keyboard-accessible editable path route supporting typing and paste; an application-owned path input is a candidate if the native picker cannot reliably provide it.
- Route path input through existing preview and explicit confirmation safeguards; selection alone must not import or alter originals.
- Align help text and packaged instructions with demonstrated behavior. Do not claim paste support until tested.

## Verification before resolution

- On installed M13 under KDE, type and paste a full filename containing spaces; correct fixture reaches preview.
- Verify folder entry, browsing/dropdown fallback, keyboard focus and cancellation; invalid paths produce actionable feedback without writes.
- Confirm preview/explicit import confirmation and original-file retention remain intact.
- Add targeted regression coverage for any new input/validation logic and repeat affected installed acceptance checks.

M13-G remains OPEN. This records a defect against existing import/help and keyboard acceptance requirements; it neither changes nor waives those criteria. Accepted M12/M11 remain untouched.

Implemented an application-owned File or folder path input and Preview path action in build `0.1.0a1-594c20d70805c834`. Native picker remains available for browsing. See [fix verification](acceptance_fixes.md).
