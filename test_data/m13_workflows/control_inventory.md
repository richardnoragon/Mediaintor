# M13-01 control inventory

Inspected production source and M12 owner screenshots, 2026-09-23. Design only; accepted M12 untouched.

| Context / source | Existing control or behavior | Problem | Proposed label / behavior |
| --- | --- | --- | --- |
| Startup recovery summary, activity_panel.py | Review Recovery | Opens filtered history, not a draft | View recovery list |
| Startup summary | Dismiss | Confused with dismissing an individual record | Hide startup summary |
| Hub Activity | View selected details | Repeated behind another window | Open activity details |
| Full Activity History | View selected details | Group headers resemble actionable records | Open selected record; disabled on group headers; add Close history |
| Activity details | Review / Retry | Could mean reading, rebuilding a preview, or writing | Kind-specific: Open recovery draft / Review pending imports / Review pending batch / Open book editor / Review next steps |
| Activity details | Dismiss | Hides actionable entry but retains work | Hide from action list; explain retained history and pending work |
| Activity details | Discard Pending | Destructive intent differs from editor discard | Discard preserved draft for recovery; Discard pending imports/changes for respective kind; retain existing review/confirmation safeguards |
| Activity details | Delete History / Close | Scope unclear | Delete this history record / Close details |
| Metadata editor, editor.py | Two sets of Add/Remove; Up/Down | Unclear field affected | Add author / Remove author / Move author up/down; Add tag / Remove tag |
| Metadata editor | Save / Retry / Discard | Unclear whether durable recovery is discarded | Save metadata / Retry unsaved changes / Discard local edits; explicit helper: preserved recovery remains until Save or separate recovery discard |
| Metadata editor | Keep Editing | Generic action | Keep editing; no additional write semantics |
| Metadata editor | Choose image | Context absent | Choose cover image; keep Remove cover and Close editor |
| Bulk window, bulk_dialog.py | Bulk metadata — preview required | Stays incorrect after completion | Operation-specific title plus real UI state |
| Bulk window | Change operation settings | Used to cancel a revert preview | Edit bulk settings for new edit; Cancel revert preview for revert; result uses Start new bulk edit |
| Bulk history | Review / Retry Pending | Review mistaken for execution | Review pending changes; confirmation is a separate action |
| Bulk history | Revert Batch | Actually builds a preview | Preview revert of selected batch |
| Bulk history | Delete history / Discard Pending | Target can be mistaken | Delete selected batch history / Discard selected batch pending work; target ID in confirmation |
| Bulk history | refresh_history preserves old selection | Newly completed batch not selected | Explicit preferred batch ID after local execution; preserve selection only on background refresh |
| Bulk history | Date, operation, pending count, short ID only | Cannot tell target books or revert relationship | Visible summary with operation, local date/time+zone, short ID, counts, affected titles, original/revert relationship |
| Import, import_dialog.py | Choose files / Choose folder | Scope not explicit | Choose ebook files / Choose folder and subfolders |
| Import | Retry / rebuild preview | Sounds like immediate writes | Rebuild import preview |
| Import | Stop after current item / Discard Pending / Close | Context needed | Stop after current file / Discard pending imports / Close imports |
| Workspaces, workspace_ui.py | Save new / Overwrite / Rename / Delete / Restore | Object implicit | Save new workspace / Overwrite selected workspace / Rename workspace / Delete workspace / Restore selected workspace |
| Workspaces | Use at startup / Startup: Last Session | Looks like state instead of action | Use selected workspace at startup / Use Last Session at startup; separate current startup choice label |
| Workspaces | Reload / Close | Confused with library reload | Reload workspace list / Close workspaces |
| File picker | Direct path entry instructions | Latest M13 owner report: neither editing nor pasting paths works; dropdown navigation works | OPEN [M13-PICKER-01](picker_path_entry_issue.md): provide and verify editable/pasteable path entry; correct instructions |

Keep labels short enough for normal KDE window sizes. Wrap rows or use clear groups rather than clipping labels or requiring a wider screen. Tooltips supplement visible labels, never substitute for them. Maintain keyboard traversal, meaningful accessible names and text state indicators; color alone is insufficient.
