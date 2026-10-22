# fix: report incomplete snapshots in compare_files

`compare_files` can report “No differences” when both snapshot reads fail with the same error or omit state at the capture size limit. A lost connection during named-object discovery can also produce a partial inventory that looks complete.

This change checks snapshot errors before diffing. It returns `{"error": "comparison incomplete", "detail": {...}}` with the affected input and section or settings path. The fallback named-object walk propagates connection failures. Valid null, inactive and empty settings remain valid.

The two case captures use separate, sequential temporary Fluent sessions. Each session is owned and closed by the tool; the caller's workspace is untouched. This removes the need for two concurrent Fluent licences. The patch also uses headless launch, passes `lightweight_setup` to `file.read`, and captures the available `solution/run-calculation` group.

## Live validation

On `HOME-DESKTOP-SH`, Fluent 2025 R2 Student Edition with PyFluent 0.41.0:

| Check | Result |
| --- | --- |
| Byte-identical official mixing-elbow case copies | Zero differences |
| Saved energy setting changed from true to false | Correct change detected |
| Real 1-byte capture limit | `comparison incomplete` for both inputs; no summary or difference count |
| Forced loss of an owned Fluent test session during fallback walk | Native connection-refused error propagated |
| Tool process cleanup | No Fluent processes remained after the comparisons |

The earlier concurrent-session version failed its identical-case check on a different host after connection loss. The revised patch has not been rerun on that host. No mock or offline tests were run as acceptance checks, and no test code is added. Existing upstream tests still contain GUI launch expectations; those need review before submission.

This is a PR **draft only**. No upstream pull request has been created.
