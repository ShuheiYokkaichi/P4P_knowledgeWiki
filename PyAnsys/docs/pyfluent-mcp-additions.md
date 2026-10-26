# PyFluent MCP contribution laboratory

This branch develops ten small additions for agents that use the official
`ansys/pyfluent-mcp` server. This is a P4P review PR, not an upstream PR.

## Scope

The official server owns a local interactive Fluent session. Keep that session
lifecycle, client-written code, and explicit disconnect behaviour. Do not port
P4P fleet scheduling, scientific acceptance rules, or remote-session ownership.

The attached **Expand PyFluent MCP Capabilities** discussion is background.
Its comparison work is retained in `work/pyfluent-mcp-live-comparison`; this
branch uses upstream main `f56e540931fbcdf5b9f81871a21934589f256d91`, verified
through GitHub on 26 October 2026. That source registers 25 tools. It already
provides screenshots, report generation/export, named-object discovery, mesh
quality headlines, and arbitrary supported Fluent API execution.

## Contribution candidates

The additions extend the information returned to an agent. Basic API wrappers,
ordinary screenshots, report generation, and P4P fleet control are excluded.

| # | Concrete addition | New result for an MCP agent | P4P source idea |
| --- | --- | --- | --- |
| 1 | `surface_geometry` | SI bounds, spans, native area/centroid and measured orientation coherence per selected surface | `scripts/inspection/inspect_phase07b_geometry.py` |
| 2 | `boundary_fingerprint` | Exact boundary tessellation identity that survives ID ordering changes and exposes actual mesh changes | `scripts/meshing/mesh_boundary_fingerprint.py` |
| 3 | `surface_field_summary` | Surface-specific finite coverage and extrema before an agent selects a plot range | `scripts/inspection/export_phase8_storyline.py` |
| 4 | `export_surface_data` | Compact MCP reply plus an indexed, hashed NPZ dataset with aligned face values and geometry | `scripts/inspection/export_phase07b_sections.py` |
| 5 | `read_live_monitor_history` | Bounded, aligned monitor snapshot with native coordinate label and explicit buffer/truncation scope; optional plot | `src/pyansys_fluent/postprocess_live.py` |
| 6 | `read_report_file_history` | Durable multi-column history recovery when live buffers are unavailable; explicit partial rows and restart segments | `scripts/inspection/extract_report_plot_histories.py` |
| 7 | `join_history_segments` | Restart-aware data assembly that exposes gaps/conflicts and preserves missing equations as null | `scripts/setup/resume_phase07b_mixture_startup.py` |
| 8 | `solver_progress` | Native Iteration expression, physical clock and activity separately from configured run limits | `src/pyansys_fluent/native_run_monitor.py` |
| 9 | `route_report_files` | Selected inherited report outputs moved to a new directory with sampling/definition invariants and readback | `src/pyansys_fluent/stage4_native.py` |
| 10 | `export_contour` | Native fixed-range PNG from an explicitly loaded, hashed case/data pair, plus view/settings provenance | `scripts/inspection/export_phase72a_stage4_spatial.py` |

All source paths above are relative to `PyAnsys/`. The extracted code is in
[`mcp_additions`](../src/pyansys_fluent/mcp_additions/). These are candidates,
not ten claims of upstream readiness. Each must still pass live review.

## Try the tools

Use Python 3.12 or later with upstream at the pinned commit, PyFluent 0.42.x,
NumPy, and optional Matplotlib for history plots. No upstream checkout is
modified. Start the opt-in server from this checkout:

```powershell
python PyAnsys/scripts/connection/fluent_mcp_contributions.py --transport stdio
```

The same upstream `connect` and `disconnect` tools own the session. The bridge
registers ten extra typed tools using the public backend execution namespace
and existing lock. It binds arguments as Python objects, not generated code.
It is a small review bridge; a maintainer can extract one helper into the
upstream Backend/domain-tool layers independently. Local file operations apply
to the MCP host, consistent with upstream's local workflow. They do not read
remote paths. Native figure export explicitly loads its supplied saved pair;
preserve unsaved work first. Report routing requires a fresh directory.

`solver_progress` is an on-demand observation. It does not solve upstream's
shared-lock limitation during a blocking solve. Fluent's `Iteration` expression
is labelled as such; an initialized case can show 1 before any solve.

## Acceptance

Each retained addition must supply a new agent-visible result, name its P4P
source and upstream integration point, pass a real Fluent demonstration, and
receive an independent subagent assessment. Unit tests and mocks do not count
as live acceptance. Failed demonstrations and review objections remain visible.

Live work uses the explicitly invoked `direct-fluent-use` workflow on
HOME-DESKTOP-SH, Fluent 2025 R2 Student Edition, in `FluentDirectUse` outside
the repository. Only sessions created for this work may be closed.

## Status

Investigation in progress. No addition is accepted yet.

| Work | Evidence |
| --- | --- |
| Upstream inventory and intended workflow | Main SHA and 25 registered tools verified |
| Repository source extraction | Ten implementations and opt-in MCP registration written |
| Live demonstrations | Running through real MCP calls and local Fluent |
| Independent ratings | Pending |

Implementation belongs under `PyAnsys/src/` and `PyAnsys/scripts/`.
Selected demonstration evidence belongs under `PyAnsys/output/`.
