# M14 scale fixture and baseline performance

M14-02 COMPLETE: independent environment, disposable scale fixture, correctness audit and installed-baseline timings recorded. M14-G remains OPEN; M14 discovery features are not implemented.

## Fixture

10,000 books: 100 verified Project Gutenberg samples plus 9,900 generated books, as selected by the owner. 10,020 format files, 7,500 covers, 100 exact-content duplicate groups and 180 conservative similar-metadata groups. Approximately 231.6 MiB of logical file data. Build used Calibre 9.2.1 add_books/set_cover, not direct database writes.

Fixture: scale/library; logical oracle: scale/oracle.json; count/hash/expected-query audit: scale_verification.json. Large rebuildable fixture excluded from version control. Original sample licenses retained. [Sources and web research](sources.md).

Known reading statuses and review flags are oracle overlays, not capabilities supplied by the current baseline loader. Metadata and cover distributions are synthetic. Logical cases are reproducible; ZIP/Calibre timestamps prevent byte-identical regeneration. Generated books are small text-heavy EPUBs; this is not representative of 10,000 image-heavy or full-length publications.

## Measured baseline

Accepted installed build 0.1.0a1-db6a7fb8885f9bd9; actual application search handler through offscreen paint, 1280×900 window. Three warmups and twenty measured repetitions per case. No fabricated M14 feature results. All baseline result sets matched independent expected UUID sets on every run.

| Case | Results | Search median | UI median | UI p95 |
| --- | ---: | ---: | ---: | ---: |
| all | 10000 | 4.5 ms | 1863.1 ms | 1887.0 ms |
| generated | 9632 | 3.9 ms | 1789.3 ms | 1815.8 ms |
| specific | 1 | 2.8 ms | 4.8 ms | 5.0 ms |
| tag | 247 | 3.4 ms | 63.6 ms | 69.8 ms |
| tag_any | 494 | 3.6 ms | 90.1 ms | 94.6 ms |
| unknown | 10000 | 4.3 ms | 1841.1 ms | 1867.7 ms |

Snapshot: 3.162 s; Calibre listing: 0.535 s; parsing: 0.515 s; loaded-handler plus initial painting: 2.195 s. Peak process RSS: 780.2 MiB.

Broad result rendering exceeds the approximate one-second M14 discovery target. Backend filtering is inexpensive; prioritize model-backed views, bounded thumbnail loading and avoiding full row reconstruction. Selective baseline searches already fall below the target in this fixture.

Raw samples/hardware: baseline_performance.json. Process-cold is not guaranteed storage-cold: OS caches were not cleared. Initial snapshot/loading is outside the warm search target. Offscreen results are not compositor/keyboard-to-screen KDE acceptance; rerun installed M14 on KDE after implementation. Saved searches, advanced AND/OR filters, review queue and duplicate-scan responsiveness/cancellation remain implementation acceptance work.

## Isolation and reproduction

M13 Everyday and the M14 copied baseline both still match all 967 entries of the pre-setup source backup (scale_isolation.json). Build mounts only the seed backup read-only and the scale directory writable. Benchmark mounts the fixture/release read-only, uses temporary settings and a read-only Wayland socket for the enforced Calibre version probe. The first benchmark attempt lacked that socket and correctly failed compatibility; no guard was bypassed.

Scripts: build_scale.py (requires a new empty disposable library and Calibre runtime), verify_scale.py, benchmark_scale.py and run_baseline.py. run_baseline.py reruns audit and timings against the completed fixture. Keep the 10,000-book library separate from the copied baseline and Everyday libraries.

Next: M14-03 discovery implementation, then use the same oracle and benchmark to compare correctness and performance.


Oracle correction during M14 implementation: two free samples have Unknown authors. Their missing-author classification was corrected without changing book files. Current expected counts are 505 for missing author OR title and 3,092 for the synthetic default review queue. Historical baseline catalog timings remain valid. See [installed M14 verification](implementation.md).
