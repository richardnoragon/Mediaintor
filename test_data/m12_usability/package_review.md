# M12-07 initial installed candidate verification

Superseded by [focus-fix candidate](focus_fix.md) after desktop feedback; original evidence retained.

**M12-07 COMPLETE; M12-08 KDE acceptance pending. M12-G OPEN.**

Candidate: `0.1.0a1-16e57f586750466b`.
Artifact: [M12 package](../../dist/m12/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz).
SHA-256: `93706e345c2fee5559efe90ab42867f55799d74ff4a204db090fd0f9034faa75`.

- Nine isolated package checks passed, including 61 installed targeted test executions (includes inherited repetitions): [report](package_verification.json), [log](package_output.txt). Correct installed module location, deployment label/manifest build, clean install, smoke, desktop entry and retained-data reinstall verified without mounting accepted libraries or the checkout.
- Source regression evidence remains [220 passing tests](implementation_regression.log); no application-source changes during packaging.
- Verified pre-upgrade backup, explicit M12-only installation, runtime inventory and offscreen startup: [installation report](installed_candidate.json). 457 retained files checked.
- M11 source file hashes match the M12 setup snapshot after installation; source unchanged. M12 uses independent data, deployment and launcher.
- [Desktop fixtures](desktop_fixtures.json): synthetic unsaved Quick Start Guide tag and original import EPUB; library database unchanged during preparation. User must explicitly Save/import. Existing data retained.

Use **Media-inator M12 Test**. Main title must identify **M12 Test** and the build above. [Owner acceptance](desktop_acceptance.json) is pending; no visual or workflow pass inferred from package tests. Namespace uses host system packages, not a new OS. Native KDE acceptance and actual-library workflow verification remain M12-08. No promotion or publication; M11 remains the stable reference.
