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
| 1 | `inspect_mesh_file` | Zone inventory, stored-coordinate extents and boundary geometry before a solver is launched | `scripts/inspection/inspect_fluent_mesh_h5.py`, `inspect_phase07b_geometry.py` |
| 2 | `compare_surface_datasets` | Scalar differences after exact geometry matching; handles row reordering and refuses changed geometry | Surface-export and boundary-fingerprint ideas |
| 3 | `bundle_artifacts` | Native artifacts in a hashed ZIP/manifest with a retrievable MCP resource link | Plot/history artifact provenance and report delivery |
| 4 | `export_surface_data` | Versioned, indexed, hashed NPZ dataset with node/face scalar values, geometry and sampling metadata | `scripts/inspection/export_phase07b_sections.py` |
| 5 | `read_live_monitor_history` | Bounded snapshot and exact-snapshot CSV/JSON/PNG; coordinate meaning stays explicitly unverified | `src/pyansys_fluent/postprocess_live.py` |
| 6 | `read_report_file_history` | Durable multi-column history recovery when live buffers are unavailable; explicit partial rows and restart segments | `scripts/inspection/extract_report_plot_histories.py` |
| 7 | `join_history_segments` | Restart-aware data assembly that exposes gaps/conflicts and preserves missing equations as null | `scripts/setup/resume_phase07b_mixture_startup.py` |
| 8 | `solver_progress` | Native Iteration expression, physical clock and activity separately from configured run limits | `src/pyansys_fluent/native_run_monitor.py` |
| 9 | `route_report_files` | Selected future outputs redirected to a fresh directory with preserved sampling/definitions and verified rollback | `src/pyansys_fluent/stage4_native.py` |
| 10 | `export_contour` | Native fixed-range PNG from an explicitly loaded, hashed case/data pair, plus view/settings provenance | `scripts/inspection/export_phase72a_stage4_spatial.py` |

All source paths above are relative to `PyAnsys/`. The extracted code is in
[`mcp_additions`](../src/pyansys_fluent/mcp_additions/). These are candidates,
not ten claims of upstream readiness. Each must still pass live review.

## Try the tools

The live environment used Python 3.13.2, PyFluent 0.42.0, Fluent 2025 R2
Student Edition and FastMCP from the upstream environment. Use the pinned
upstream requirements, NumPy, h5py for mesh files, and Matplotlib for history plots. Other package
versions are not qualified by these demonstrations. No upstream checkout is
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
is labelled as such; an initialized case can show 1 before any solve. Counter
decreases return no numerical delta and flag a possible reload/reset. Probe
failures produce a partial observation, not an invented zero.

### Use the outputs

An MCP client can list the ten added tools after starting the opt-in server.
Call `inspect_mesh_file` with an absolute `path` and a containing absolute
`allowed_root`. No Fluent connection is required. The reader supports the
evidenced Fluent 25.2 version-2 3D layouts. It reports raw coordinate units,
approximate polygon areas/vertex-centres, winding-based normals and source
slices. It does not infer flow roles, native centroids, cell volumes or SI scale.

Dataset paths are files on the MCP host, not download URLs or MCP resources.
To load an exported dataset without enabling pickle:

```python
import json
import numpy as np

metadata = json.loads(open("surfaces.json", encoding="utf-8").read())
with np.load("surfaces.npz", allow_pickle=False) as arrays:
    prefix = metadata["surfaces"]["outlet"]["prefix"]
    xyz = arrays[prefix + "_vertices"]
    values = arrays[prefix + "_values"]
    connectivity = arrays[prefix + "_connectivity"]
```

Read `sampling` before pairing arrays: node values align with vertices; face
values align with face order. A face value may come from the adjacent cell and
need not equal a field evaluated at the geometric face centroid. Connectivity
stores a vertex count followed by that face's zero-based vertex IDs. The
`max_faces` bound applies after retrieval and does not cap RPC memory.

Call `compare_surface_datasets` with two absolute `.npz` paths; each sidecar is
the adjacent `.json`. It verifies integrity and metadata, decodes geometry and
matches exact coordinate groups. It handles row reordering, refuses changed
geometry or ambiguous duplicate values, and reports finite/nonfinite coverage.
Deltas are B minus A with equal sample weights, not area-weighted integrals.
Explicit value tolerance affects only changed-sample counts. The caller still
establishes physical comparability. Matching does not prove interior-mesh or
CAD equivalence.

History transport success does not establish complete data. Inspect `status`,
truncation, rejected/provisional rows and source scope. A live snapshot covers
the current client buffer only. A file reader covers its bounded byte window.
Native display labels are separate: the demonstrated `flow-time` label
accompanied time-step indices. JSON, CSV and PNG therefore label monitor
coordinates as unverified and do not infer seconds or iterations.
For joins, supply source hashes, axis/units, aligned arrays and explicit stages
for resets. Hashes and common physical lineage remain caller assertions. The
joiner never interpolates or rebases missing samples, and retains conflicts.

Routing closes each writer, changes its path, restores its original activation
and checks readback. It preserves selected definition mappings and sampling;
existing histories remain at their old paths. A failure returns a structured
rollback receipt, which must be checked before solving. Managed run/index
counters are outside restoration scope. Native file operations verify the
Fluent controller's local host and working directory.

Figure export needs a graphics-enabled session. The demonstrated local setup
used `ui_mode="hidden_gui", graphics_driver="msw"`; default no-GUI/null graphics
could not save the native image. Export replaces live state with the supplied
saved pair. It uses private scratch outputs, publishes validated files without
overwrite, attempts graphics cleanup independently, and invalidates upstream
live/mesh caches even after failure. The active graphics window changes.

Call `bundle_artifacts` with an absolute `root`, 1–32 explicitly selected files
inside it, and a new ZIP `output` inside it. Its manifest maps numbered archive
members to source-relative paths and hashes. Grouping proves neither common
case lineage nor scientific completeness; HTML dependencies are not fetched.
The reply provides `resource_uri` and an MCP resource link. Fetch it with MCP
`resources/read`; the server verifies size/hash before returning bytes. A
client needs no access to the Fluent host's paths. The registry holds at most
128 bundles and expires when the server process ends.

## Acceptance

Each retained addition must supply a new agent-visible result, name its P4P
source and upstream integration point, pass a real Fluent demonstration, and
receive an independent subagent assessment. Unit tests and mocks do not count
as live acceptance. Failed demonstrations and review objections remain visible.

Live work uses the explicitly invoked `direct-fluent-use` workflow on
HOME-DESKTOP-SH, Fluent 2025 R2 Student Edition, in `FluentDirectUse` outside
the repository. Only sessions created for this work may be closed.

## Evidence and review status

The current ratings are tracked below. Scores are independent reviewer
judgements, not upstream maintainer acceptance. Earlier findings and failed
demonstrations remain in the selected evidence.

| Addition | Latest completed rating | State |
| --- | --- | --- |
| Mesh-file atlas | Pending | Live file/solver cross-check passed |
| Dataset comparison | Pending | Native reorder and scalar-patch checks passed |
| Artifact bundle/resource | Pending | Live ZIP/resource round trip passed |
| Dataset export | 8.5 | Retained |
| Live history | 7.8 | Coordinate-label defect repaired; fresh live evidence |
| File history | 8.5 | Retained |
| History join | 8.2 | Retained |
| Solver progress | 8.5 | Retained |
| Report routing | 8.5 | Retained |
| Native figure | 8 | Diagnostics repaired; native publication rollback demonstrated |

Geometry summaries, standalone boundary fingerprints and field-range summaries
each reached 8/10. They were replaced in the default set. The laboratory can
register them with `register_additions(server, include_experimental=True)` for
exploratory demonstrations; they are not retained additions.

Selected machine evidence is under
[`output/mcp-contributions/20261026`](../output/mcp-contributions/20261026/).
The local runtime preserves the larger saved pairs outside Git. Each run's
`identity.json` pins implementation hashes. Later runs also record the actual
loaded upstream path, its clean Git status and revision. Request arguments and
results are copied when recorded; historical receipts with the earlier mutable
argument bug are not replay evidence for the conflict call.

The initial public mixing-elbow case came from
[`ansys/example-data`](https://raw.githubusercontent.com/ansys/example-data/main/pyfluent/mixing_elbow/mixing_elbow.cas.h5)
(3,062,081 bytes; Git blob `a186ebbc7c0578b94668f51425a20cdc6ac9c011`).
The current live harness is
[`demo_mcp_additions_final.py`](../scripts/inspection/demo_mcp_additions_final.py).
The older `demo_mcp_additions.py` covers the exploratory set.
It runs on an explicitly supplied owned solver and official `SolveMCP` instance;
it does not launch or claim ownership of arbitrary sessions. Its examples use
the mixing-elbow surfaces and named temperature/pressure/time reports prepared
in the saved demonstration case. The contribution tools themselves accept
caller-selected names.

Qualification covers one case and Fluent/PyFluent version. Large selections,
other versions, multiphase fields and live 2D operation remain unqualified.
Some invalid-data and exceptional recovery branches have source review only.
There are no unit-test or mock results presented as Fluent acceptance.

Implementation belongs under `PyAnsys/src/` and `PyAnsys/scripts/`.
Selected demonstration evidence belongs under `PyAnsys/output/`.
