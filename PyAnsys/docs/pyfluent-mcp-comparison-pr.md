# feat: compare selected Fluent settings in compare_files

The default `compare_files` result shows global model settings and named-object names. If a named inlet keeps its name but its velocity changes, that change is outside the default snapshot.

Add optional `settings_paths` for up to 10 exact Fluent settings paths. The tool reads each path in both case files, lists the requested scope, and adds changed values to the normal diff and Markdown summary. Omitting `settings_paths` preserves the default comparison. A requested path that cannot be read returns `comparison incomplete` with the affected input and path.

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
| Saved `cold-inlet` velocity changed from 1 to 2 | Default returned 0 differences; `settings_paths` returned one correct value difference |
| Unreadable selected path | `comparison incomplete` for both inputs; no difference count |

The selected-path run and the three-check regression used the same combined patch. The [regression receipt](../output/pyfluent-mcp-audit/20261022-selected-paths/live-status.json) and its raw JSON and log record the final results: 0 differences for byte-identical copies, 16 differences for the saved energy change including `enabled: true` to `false`, and `comparison incomplete` for both inputs at the 1-byte capture limit. No Fluent processes remained after the runs.

The earlier concurrent-session version failed its identical-case check on a different host after connection loss. The revised patch has not been rerun on that host. No mock or offline tests were run as acceptance checks, and no test code is added. Existing upstream tests still contain GUI launch expectations; those need review before submission.

This is a PR **draft only**. No upstream pull request has been created.
