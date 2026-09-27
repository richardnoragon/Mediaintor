# Personal installation preview

Target: Ubuntu 26.04.1 KDE, x86_64, system Python 3.14.4, PyQt6/Qt 6.10.2,
PyQt6-sip 13.11.0. See runtime.json for prerequisite packages. Installation
never installs system dependencies and never needs sudo. Calibre 9.2.1 must
be installed separately. M6-03 guards block protected operations when dependencies
are missing or unverified. Recheck prerequisites does not resume pending work.

From the trusted project checkout:

    /usr/bin/python3 -I tools/package_install.py install path/to/bundle.tar.gz

Without a checkout, extract only package_install.py from your trusted bundle
into an empty working folder, then run:

    /usr/bin/python3 -I ./package_install.py install /absolute/path/to/bundle.tar.gz

Keep the original archive intact. Do not run an untrusted installer.
The installer validates the archive without extracting unchecked archive paths.
Checksums detect corruption, not an untrusted publisher.

Close Media-inator before installing, upgrading or uninstalling. The menu entry
and ~/.local/bin/mediainator launch the installed package independently of the
checkout. All installation is for the current user; root execution is refused.
Existing settings, library selection, history and recovery locations remain intact.
The existing private-copy/single-reader access restrictions remain unchanged.

Install a later bundle with the same install command. New content is checked
before activation, and the previous release is retained. There is no automatic
schema downgrade or rollback command. If a later installation fails before
activation, the prior release remains selected. M6-06 verifies build-to-build upgrades with populated settings, history and
recovery data. This does not authorize a schema downgrade.

Uninstall (program files only):

    /usr/bin/python3 -I "$HOME/.local/share/mediainator-install/current/package_install.py" uninstall

Confirm the prompt, or explicitly use --yes. Libraries, settings, recovery data
and operation history are never removed. Modified managed program files cause
uninstall to stop for review. Reinstall uses retained application data.

The Help menu contains offline instructions and troubleshooting. F1 opens the
user guide. About shows application/runtime versions. Help → Preview redacted diagnostics provides an exact preview and explicit
local JSON export. No automatic uploads or raw-log attachments are supported.
M6-G remains open; this artifact is an unpublished personal-use preview.

## Preserved data and troubleshooting

Program releases are under ~/.local/share/mediainator-install/releases; current
selects the active version. The launcher is ~/.local/bin/mediainator and the
menu entry is in the XDG user applications directory. Settings and operation
history use the existing Qt application configuration/data locations; their
identity remains Media-inator. Libraries stay at their original locations.
Never remove the configuration or recovery directories to uninstall the app.

If runtime validation fails, compare its detected/required values with
runtime.json. Install missing prerequisites separately; this installer does not
run a package manager. If a package file or managed launcher changed, stop and
inspect it rather than using a forced overwrite. For library, save, recovery or
viewer problems, choose Help → Troubleshooting, or read TROUBLESHOOTING.md.


## Repair an interrupted installation action

If the installer or launcher reports an interrupted action, close Media-inator.
Use the installer extracted from the same trusted bundle (so it remains available
even if uninstall already removed the launcher):

    /usr/bin/python3 -I ./package_install.py repair

Repair completes the previously recorded install or confirmed uninstall. It does
not replay imports, metadata edits or recovery saves. It validates program-file
hashes and refuses changed files. Keep the transaction record until repair
succeeds; do not delete application data or edit the installation JSON to bypass
it. If repair is interrupted, rerun the same command. Interrupted staging may
leave an unused .staging directory, which is never launched. Installer-managed
release files remain separate from settings, history, library and recovery data.
