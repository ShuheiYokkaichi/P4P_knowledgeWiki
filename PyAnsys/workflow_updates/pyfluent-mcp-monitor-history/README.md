# PyFluent MCP monitor-history draft

[Upstream issue #93](https://github.com/ansys/pyfluent-mcp/issues/93) proposes
access to the numerical samples behind Fluent residuals and report monitors.
[The patch](changes.patch) adds a Solve MCP tool that reads samples already
captured by the connected PyFluent session.

| Call | Result |
| --- | --- |
| `read_monitor_history()` | Monitor-set names known to the session |
| `read_monitor_history(monitor_set="residual", max_points=50)` | Up to 50 latest samples, the x-axis label and coordinates, and one series per monitor |
| A known set with no samples | `no_samples` with empty arrays |
| A set absent from the session | `monitor_set_unavailable` with the known set names |

The default point limit is 100 and the maximum is 1,000 per series. Nonfinite
values become JSON nulls. A freshly attached session can have partial or empty
history. The tool uses the backend's read lock and leaves the PyFluent monitor
stream under the control of its existing owner.

The case must expose the monitor to the stream before the solve. In Fluent
2025 R2, the mixing-elbow example has residual printing enabled and residual
plotting disabled. Enable the residual plot before initialization to capture
its residual samples through PyFluent.

## Review the patch

Apply [changes.patch](changes.patch) from the root of a clean
[upstream checkout at `8a712b3b`](https://github.com/ansys/pyfluent-mcp/tree/8a712b3b091932f63105d9e54cc6a725f14e7100).

```sh
git apply --check /path/to/changes.patch
git apply /path/to/changes.patch
python -m pip install -e '.[tests]'
python -m pytest --no-cov --ignore=tests/test_pyfluent_live_integration.py
```

For changes to this draft, edit the upstream checkout, stage the intended files,
and regenerate the patch with `git diff --cached --binary --full-index`.

## Verification

| Check | Result |
| --- | --- |
| Apply patch to a clean upstream checkout | Passed |
| Upstream tests that run without Fluent | 473 passed, including the new backend and MCP tool tests |
| Ruff lint and formatting for the changed Python files | Passed |
| Desktop smoke test | Fluent 2025 R2 Student and PyFluent 0.43.0, public mixing-elbow case, 3D double precision, one process |
| Residual results through the MCP tool | Before solving, the residual set returned `no_samples`. An unknown set returned `monitor_set_unavailable`. After five iterations, the tool returned iterations 1–5. With a limit of two it returned iterations 4–5 across seven residual series. |

The live smoke test covered steady residuals. Transient coordinates and report
monitor samples still need a live test.
