# M12 workspace feedback correction

Source and isolated package verification passed. M12 installation and KDE acceptance pending; M12-G open. M11 unchanged.

Automatic Last Session saving previously reported normal busy periods as persistent failures. Successful restoration did not clear that message. The owner screenshots alone therefore did not prove restoration was blocked.

The correction defers background saving quietly during temporary library operations, while blocking explicit restore during those operations. A fully committed restore now reports “Workspace restored.” Pending asynchronous restores and failed commits do not report success.

223 source tests passed. Nine isolated package checks passed, including 64 installed targeted tests, install/reinstall/uninstall retained-data checks and checkout isolation.

Candidate: 0.1.0a1-f59e8af9b043f304
Archive: dist/m12-workspace/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz
SHA-256: 21af3e215de06a32d1088ad6a980f189407af99b5dcbce3074d081448aad458b

Next: close M12 and readers normally, back up and install with install_workspace_candidate.py, then perform KDE acceptance. No installed desktop pass is claimed for this replacement.

## Replacement installation completed

Owner confirmed normal shutdown. Build `0.1.0a1-f59e8af9b043f304` installed; backup verified, 459 retained files unchanged, runtime inventory and package smoke passed. M12 launched for KDE workspace feedback retest. See `installed_workspace_candidate.json`. M12-G open; M11 unchanged.

Personal KDE retest passed: owner confirmed and screenshot shows “Workspace restored.” after restoring the copied M11 Everyday workspace on build `0.1.0a1-f59e8af9b043f304`. Misleading workspace feedback issue resolved. Remaining M12 acceptance and final gate review stay open; M11 unchanged.
