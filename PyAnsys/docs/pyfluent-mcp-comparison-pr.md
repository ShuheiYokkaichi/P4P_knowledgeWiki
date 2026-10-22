# fix: report incomplete snapshots in compare_files

`compare_files` can report “No differences” when both snapshot reads fail with the same error or omit state at the capture size limit. The error records compare equal even though the settings were not read.

Check the existing snapshot error markers before diffing and return the usual `error`/`detail` response, identifying the affected input and section or settings path. Complete comparisons retain their result format. Valid null, inactive and empty settings remain valid.

Use the documented headless launch mode, pass `lightweight_setup` to `file.read`, and capture the available `solution/run-calculation` group. These three one-line corrections allow real Fluent 2025 R2 case reads and complete global-state capture. The tool still owns, loads and closes its two temporary Fluent sessions.

Validation: **incomplete; do not submit yet**. Real Fluent 2025 R2 with PyFluent 0.41.0 verified the read-error guard, omitted-state rejection through the public tool, energy-setting change detection, and temporary-process cleanup. However, byte-identical case copies returned 63 false named-inventory differences. Debug logs show that the existing fallback traversal suppresses connection-refused errors and returns a partial inventory. The cause of the temporary-session connection loss remains unresolved. Concurrent snapshots did not fix it, and that experiment was reverted.

No test code is added, and no offline checks count as acceptance. Existing upstream tests still encode GUI launch expectations; those were not changed or executed.
