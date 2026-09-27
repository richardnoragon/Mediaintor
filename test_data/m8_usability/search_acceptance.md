# M8 search/filter implementation and regression review

M8-04 implementation complete in development code. Text searches title/author/series; tag, format and reading-status filters implement AND across categories and OR within categories. Checkable menus preserve unseen selected values. Search, filters, Needs Metadata Review and panel visibility persist; Clear All updates state immediately without clearing bulk selection. Both views share the same result set. Calibre catalog listing now requests series.

Automated evidence: **185 tests passed** in the full suite ([log](regression_final.txt)). New tests cover series search, combined categories, Unknown status, empty results, restart restoration, Clear All, view consistency and malformed preferences. Updated one prior test to expect approved search persistence rather than automatic clearing.

Progress robustness includes bounded reads, regular-file enforcement, symlink/FIFO rejection, invalid/future/timezone-free timestamps, conflicting equal-time positions, corrupt history preservation, persistent rename provenance and target-record precedence. Existing real Calibre rename/API probes and owner-confirmed integrated EPUB rename/resume remain applicable. No additional application deployment into RC1 or active M8 has occurred.

## Final desktop checks pending

1. In the disposable M8 Hub, combine text and tag/format/status filters; confirm both views show the same matching books. Unknown is expected for this library's unverified reading statuses.
2. Leave a search and filter active, close and reopen this disposable Hub, and confirm restoration. Clear All must restore all results and remain cleared after another restart.
3. Confirm selected-book count survives filtering and Clear All; verify progress details remain available.

## Review disposition

M8-G remains open pending these new controls' owner desktop acceptance and final gate sign-off. Earlier navigation and integrated rename desktop checks passed. The original focus issue did not reproduce; no synthetic-key workaround or claimed focus fix. Percentage/status remain Unknown where unverified. Unobserved external renames and changed-content handoff are intentionally not inferred. Large-library performance beyond the 101-book fixture has not been qualified.
