# Small contributions to PyFluent MCP

Review date: 20 October 2026. Scope: compare the public PyFluent MCP implementation with this project's reusable code and working practices. This is a contribution proposal, not an implementation or a live Fluent qualification.

**Recommendation:** improve the existing `compare_files` result when reads are incomplete, then consider optional comparison of selected named-object values. Correct the bundled tool examples as a separate small contribution. Preserve the official session lifecycle, client-led execution loop, and temporary-session comparison design. A preserve-on-detach option is no longer recommended: it mainly serves our different operating model.

[Interactive official-workflow and contribution map](pyfluent-mcp-contribution-map.html).

The first contribution is prepared locally. The 21 October version failed the complete identical-case comparison. The revised patch passed the desktop real-Fluent checks on 22 October, including identical cases, a saved energy change, incomplete reads, and owned-session cleanup. The revised patch has not been rerun on Server 3, and no upstream PR has been created. Offline checks are not acceptance evidence: [PR draft](pyfluent-mcp-comparison-pr.md), [patch with review instructions](../workflow_updates/pyfluent-mcp-compare-files/README.md), and [desktop receipt](../output/pyfluent-mcp-audit/20261022/desktop-live-status.json).

## Evidence and version boundary

| Item | Checked result |
| --- | --- |
| Upstream | [`ansys/pyfluent-mcp`](https://github.com/ansys/pyfluent-mcp), not the similarly named third-party repositories |
| Source reviewed | [`f56e540931fbcdf5b9f81871a21934589f256d91`](https://github.com/ansys/pyfluent-mcp/tree/f56e540931fbcdf5b9f81871a21934589f256d91), main, commit dated 15 October 2026 |
| Latest public release | [`v0.5.0`](https://github.com/ansys/pyfluent-mcp/releases/tag/v0.5.0), published 25 September 2026; PyPI also reports 0.5.0 |
| Release versus main | No changes under `src/` between v0.5.0 and the reviewed main commit; changes are dependencies, CI and maintenance files |
| Project MCP pin | `65de7c8226d1382c9620f11fac32def059a48e79` in [mcp_policy.py](../src/pyansys_fluent/mcp_policy.py). The upstream audit used current source, not that older pin |
| Tool inventory | Constructed `SolveMCP` from reviewed source and called `list_tools()` offline: 25 registered tools, with their actual input schemas |
| Open work | GitHub public open issue list and open PR list both returned empty during this review. This does not establish maintainer interest or exclude private plans |
| Initial source probes (mechanics only) | Mocked attached-session cleanup called `solver.exit()` once; status reported `iterations=1000` from a supplied `iter_count=1000` control; existing snapshot diff returned no change for `True` versus `1` |
| Original audit boundary, 20 October | No Fluent session was controlled during that source audit. Subsequent live checks and their failed acceptance result are recorded in the linked review bundle |

The source review and synthetic probes describe code behaviour only. They do not establish that the contribution works in Fluent. The subsequent live acceptance result is recorded in the [review bundle](../workflow_updates/pyfluent-mcp-compare-files/README.md).

Machine evidence is retained under `../output/pyfluent-mcp-audit/20261020/`: `tool-inventory.json`, `source-probes.json`, `upstream-tests.txt`, `review-evidence.json`, and the subsequent use-case review files `fit-probes.json`, `fit-probes.py`, and `official-use-case-evidence.json`. The output directory is generated evidence and can be ignored by Git.

## The official use case and contribution boundary

The official workflow is an interactive assistant controlling a Fluent workspace through deterministic MCP operations. The quick start recommends **launching a new Fluent session**; attaching to an existing local or remote instance is also supported. The client generates Python and decides what to do next. MCP discovers APIs, validates and runs calls, and returns values or errors.

The user-facing workflow is:

```text
user asks a CFD question / requests a setup change
    -> client connects (new session recommended; attach also supported)
    -> discover paths, object names, active settings and allowed values
    -> client writes Python -> validate_code -> run_code
    -> inspect state / mesh / results / reports
    -> reuse the same session for the next interaction
    -> disconnect when finished; Fluent resources are released
```

Meshing is also within scope: launch in meshing mode, discover standard workflow tasks, import geometry, generate/check the mesh, then switch to solver mode. The MCP is not only a case-file reader. There is no evidence that it is restricted to small or short CFD problems; the evidence concerns interaction and ownership boundaries, not problem size.

| Official evidence | What it establishes | Contribution implication |
| --- | --- | --- |
| [Quick start](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/doc/source/getting_started/quick_start.rst): “Launch a new Fluent session (recommended)” | Launch is the default documented entry; remote attach is an option | Do not make attach-only fleet operation the assumed upstream user |
| [Best practices](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/doc/source/user_guide/best_practices.rst): “Keep the same Fluent session open for multiple operations” and “Always call disconnect when finished to free resources” | Tools reuse a persistent session; cleanup at task end is deliberate | Ordinary reads do not each exit Fluent. Preserve normal disconnect and shutdown semantics |
| [Usage examples](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/doc/source/examples/usage_examples.rst) | Load/summarise a case, inspect quality, change an inlet, learn API paths, compare two files | Start from one of these user requests and improve its existing result |
| Approved and merged [PR 19](https://github.com/ansys/pyfluent-mcp/pull/19) | Removed in-server LLM code generation, provider transport and conversation state; client generates code | Do not reintroduce a planner, autonomous campaign engine or embedded reasoning |
| PR 19's reported live smoke sequence: connect → inspect → modify BC → solve 60 iterations → post-process → report → disconnect | A concrete end-to-end use of the official pattern | The useful contribution can be a more accurate inspection/report result inside this sequence |
| Approved and merged [PR 71](https://github.com/ansys/pyfluent-mcp/pull/71) | Added live dry-run write checks and mode-aware API routing | Small improvements to valid API use fit the direction. Do not duplicate this write-preview capability |
| Approved and merged [PR 75](https://github.com/ansys/pyfluent-mcp/pull/75) | Tightened access to OS/sys methods and workarounds | Do not port our OS-command/Scheme bridge as a new unrestricted execution route |
| [Current backend](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/src/ansys/fluent/mcp/solve/backends/pyfluent.py#L942) explicitly serialises solver calls with a single-flight lock | Concurrent solver access is deliberately controlled | Do not bypass the lock to retrofit our continuous supervision model |
| [`compare_files` implementation](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/src/ansys/fluent/mcp/solve/lib/compare_tools.py#L361) creates and cleans up separate temporary sessions | File comparison is intentionally isolated from the active workspace | Extend that operation while retaining its session isolation and cleanup |

Our project often starts with a valuable existing remote endpoint, preserves it across chats, dispatches long native runs, reconciles lost connections, and maintains scientific acceptance records. Those are valid host/application choices. They are not evidence that the official MCP's simpler lifecycle needs changing.

**Fit test for each proposal:** name an official user request; identify an insufficient result in that request; improve one deterministic tool/helper or example; retain current lifecycle, validation, backend and orchestration boundaries. A function being small or reusable is not sufficient by itself.

These are documented product choices and public implementation/PR evidence. They do not establish the maintainers' private working practices or guarantee acceptance of any proposal.

## What upstream already provides

The server provides tools and backend operations. It deliberately leaves model selection, agent reasoning, retry policy, workflow planning and experiment acceptance to its host. That boundary is explicit in the [README](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/README.md) and [domain-tool contract](https://github.com/ansys/pyfluent-mcp/blob/f56e540931fbcdf5b9f81871a21934589f256d91/src/ansys/fluent/mcp/solve/lib/domain_tools.py).

These signatures come from offline tool registration. Optional arguments are marked `?`.

| Area | Tool and actual inputs | Current function / boundary |
| --- | --- | --- |
| Session | `session_status()` | MCP connection and backend identity; endpoint identity does not prove loaded case identity |
| Session | `connect(backend_kind?, connect_kwargs?)` | Launch or attach. Backend options are nested under `connect_kwargs` |
| Session | `disconnect()` | Backend teardown; PyFluent implementation explicitly calls solver exit/close |
| Session | `solver_status()` | Best-effort initialization, iteration control, solver mode and UTL status; limited native progress evidence |
| Session | `manage_fluent(action)` | Component activate/deactivate/update/refresh hook; usefulness depends on backend support |
| Discovery | `find_api(query, top_k?, kinds?, under?, compact?)` | Ranked API/schema search; bundled schema is `settings_271.json.gz` |
| Discovery | `get_help(path)` | Help for an API node |
| Discovery | `get_state(paths?, key?)` | Read selected live paths; optional key selects one object from a collection |
| Discovery | `get_targeted_context(paths_to_check, named_object_types?, instance_state_fetch?)` | Batched context and live probes for selected paths |
| Named objects | `list_named_objects(limit?, offset?)` | Global inventory with paging; no public `path` argument |
| Named objects | `find_named_object(name)` | Find a named object in the inventory |
| Named objects | `select_named_objects(collection, pattern?, include_shadows?, exclude?)` | Select names using glob patterns |
| Schema probes | `probe_path(paths)` | Existence, activity, node kind and user-creatability for API paths; this does not probe disk paths |
| Schema probes | `get_active_status(paths)` | Batch activity queries |
| Schema probes | `get_allowed_values(paths)` | Batch enum/value constraints |
| Schema probes | `describe_named_object_template(path)` | Child shape, types, constraints and creation metadata |
| Schema probes | `describe_path(paths, include_template?, include_command_arguments?)` | Unified descriptors including command arguments; unknown metadata is represented explicitly |
| Execution | `validate_code(code)` | Precheck Python and supported API usage; no proof of scientific correctness or successful mutation |
| Execution | `run_code(code)` | Execute validated Python with solver/session bindings; captures stdout/stderr and returned value |
| Reports | `summarize_setup()` | Native Fluent setup summary; no public scope argument in the reviewed code |
| Reports | `simulation_report(action?, report_name?, output_path?)` | List/generate reports and export HTML/PDF/PPTX; not a general numerical acceptance check |
| Graphics | `screenshot(view?)` | Capture solver graphics |
| Mesh | `mesh_quality(include_check?)` | Structured quality metrics/histograms and optional native mesh check |
| Fields | `list_fields(scope?)` | Enumerate available fields |
| Comparison | `compare_files(path_a, path_b)` | Open two temporary Fluent sessions; compare global settings and named-object inventories; return structured differences and a Markdown summary |

Other existing facilities matter when choosing contributions:

| Facility | Existing upstream support | Implication |
| --- | --- | --- |
| Transport/runtime | STDIO and streamable HTTP; Python 3.12+; PyFluent dependency; optional HDF5 file-probe support | A remote solver is supported; do not assume MCP-host paths refer to solver-host files |
| Validation | AST sandbox, restricted imports/builtins, signature/path checks, reflection-write checks, intent guards and advice | Do not contribute another generic Python validator or bypass these paths |
| Live discovery | Named-object caches, targeted inspection, activity and allowed-value probes, cache invalidation | Our old recursive tree mapper would largely duplicate this |
| Introspection | Additional backend methods include command-argument queries, mesh adjacency, mesh counts, and dry-run writes | A missing public tool does not always mean missing implementation |
| Files | Suffix handlers, path normalisation, HDF5 metadata probes for dimension/precision | Extend these for extra file metadata rather than inventing a parallel file registry |
| Extension | External solve backends through `ansys.fluent.mcp.solve_backends`; typed domain-tool registry; run-code observer hooks | Small deterministic tools have a documented insertion point |
| Resources and diagnostics | `toolsets://definition`, bundled authoring skill, session/activity logs, timing, telemetry and backend traces | Documentation and tests are valid contributions; full project/agent orchestration does not belong in this layer |

## Contributions that fit the official workflow

Size describes relative scope, not a delivery promise. “Confirmed” means a code path or offline reproduction was checked; it is not a live Fluent qualification. Suggested fields and inputs below are proposals, not current APIs.

| Priority | Official user request | Small contribution | Project material to extract | Fit / evidence |
| --- | --- | --- | --- | --- |
| F01 | “Compare these two cases. What changed?” | Make incomplete reads visible in `compare_files` | Failed/omitted-read checks from `setup_snapshot_diff.py`; verification fixtures | Strongest first code contribution; offline reproduction |
| F02 | “Did the inlet value change between these cases?” | Optional selected-path values in `compare_files` | Narrow path captures and recursive state comparison | Direct extension of an official use case; current scope confirmed |
| F03 | “Use this MCP from my assistant” | Correct examples and test documented tool arguments | Upstream contract-test pattern | Smallest contribution; signature mismatches confirmed |
| F04 | “What did the solve complete?” | More precise fields in existing `solver_status` | Native counter/activity reads from `native_run_monitor.py` | Good fit as an on-demand snapshot; version qualification needed |
| F05 | “Show the residual history for this solve” | Bounded monitor-history data through a domain tool | `capture_residual_history` and optional Matplotlib example | Explicitly matches interactive-analysis use; new capability needs design discussion |
| F06 | “Summarise the case in my remote Fluent session” | Retrieve generated summary from the correct host | Bounded report read/capture pattern from `remote_text.py` and `dpm_transcript.py` | Source-level host-path concern; reproduce with a supported remote setup before proposing a fix |

### F01 — Avoid a false no-differences result when reads fail

**User benefit.** A case comparison should distinguish successfully compared data from unavailable data. The assistant should be able to explain what it could and could not compare.

**Current behaviour, reproduced offline.** `collect_compare_snapshot()` records failed reads as `{"_error": "..."}`. If both backends fail with the same messages, the dictionaries compare equal. `compare_files()` then returns:

```json
{
  "status": "ok",
  "diff_count": 0,
  "summary": "No differences between **a.cas** and **b.cas**."
}
```

The fake backends both raised `state unavailable` and `names unavailable`. Both temporary-session disconnects were still called once. This is a reporting-completeness problem inside the existing operation; it requires no new lifecycle or workflow.

**Small change.** Carry read-completeness information through snapshot collection, comparison and summary formatting. If no requested data was read, return a comparison failure. If only some data was read, identify the missing scope and say whether differences were found in the successfully compared data. Continue to close both temporary sessions in `finally`.

**Project source.** [compare_snapshots and _has_missing_evidence](../src/pyansys_fluent/setup_snapshot_diff.py), plus the failed/truncated/missing-state tests in [test_mcp_verification.py](../tests/test_mcp_verification.py). Extract the distinction between data and failed observation; do not copy the project schema, acceptance gates or broad missing-value policy.

**Important adaptation.** A literal null can be a valid setting. An inactive model branch can be a legitimate result of the case setup. Do not reject those blindly. Separate read failure/truncation from a successful observation of inactivity or null, and state which fields were inapplicable.

**Acceptance checks.** Both reads fail; one side fails; one branch fails; ordinary equal cases; ordinary differences; inactive model; valid null; truncation; all cleanup paths. Keep the normal successful result shape and Markdown comparison format where practical. This is tool-result integrity, not physical validation.

### F02 — Compare selected named-object values in the existing tool

**User benefit.** “Did this inlet change from 1 to 2 m/s?” is a natural extension of the documented case-comparison request.

**Current scope.** The default snapshot collects a fixed global setting set and named-object **names**. The global set covers solver/model state, some solution controls, gravity and operating pressure; it does not include boundary-condition values. Equal inlet names alone therefore cannot reveal a changed velocity. An offline fake-backend example with different inlet values produced equal default snapshots. This is a scope limitation, not proof that its documented compact comparison is defective.

**Small change.** Consider an optional list of exact settings paths on `compare_files`. Read those paths in both existing temporary sessions, return a bounded value diff, and identify the compared scope. Keep the default global/inventory comparison, isolation and cleanup. A separate snapshot-comparison tool is not needed for this first extension.

**Project source.** [mcp_inspection.py](../src/pyansys_fluent/mcp_inspection.py), [setup_snapshot_diff.py](../src/pyansys_fluent/setup_snapshot_diff.py), and [execution_contract.py](../src/pyansys_fluent/execution_contract.py). Reuse narrow reads and structural comparison, not scientific expected-change rules.

**Acceptance checks.** Same name/different scalar value, missing object, inactive physics, read failure, ordered vector, duplicate inventory names, bounded output and correct path names in the summary. Preserve inventory semantics for collections. Numerical tolerance, automatic unit conversion and role mapping can wait; they enlarge the first change unnecessarily. F01 should establish incomplete-read semantics first.

### F03 — Make the documented interaction loop executable

**User benefit.** Users and their assistants can follow the official examples without receiving argument errors or being told an available tool does not exist.

**Current gap.** The official tools reference correctly lists 25 tools, while README and the bundled skill contain older counts. The skill also states `get_allowed_values` does not exist, and shows `get_state(path=...)` although the registered input is `paths`. Other examples have drifted from the current signatures.

**Small change.** Align README, the bundled skill and usage examples with the registered tools; add a contract test for the tool names and structured example inputs. Keep the documented discover → validate → execute → verify → disconnect pattern.

**Project source.** [test_mcp_upstream_contract.py](../tests/test_mcp_upstream_contract.py) demonstrates the contract-test approach. Remove our P4P allowlist and session policy. No need to change the official authoring workflow.

**Acceptance checks.** Structured example arguments match `SolveMCP.list_tools()` schemas, searches use real indexed paths, and fake-backend examples exercise the normal workflow. A schema test cannot prove that every live Fluent setting is available in every release; label that boundary.

### F04 — Precise on-demand solver status

**User benefit.** After running a solve, the assistant can distinguish the configured iteration request from actual completed progress.

**Current evidence.** `solver_status()` reads the run-calculation settings. Its live integration tests explicitly note that iteration count and initialization flags are unreliable across builds. Our native monitor distinguishes a completed native counter, configured limit, and direct `iterating()` query.

**Small change.** Improve the existing result with separately named native progress and configured-control fields, source and unknown values. A read after a solve fits their normal interaction loop. Keep the single-flight lock. Do not add a background poller, bypass serialisation, or promise concurrent status during blocking `run_code`.

**Project source.** [_read_activity and _read_runtime](../src/pyansys_fluent/native_run_monitor.py). Extract only the snapshot reads and fake tests; leave fleet configuration, reconnect, previous-state files and controller policy in this project.

**Acceptance checks.** Native counter differs from requested count, reset/reload, unavailable native query, idle state, transient time and supported Fluent releases. Film time must remain separate from bulk flow time. Native queries require current-version verification; the project source is a starting point.

### F05 — A bounded residual-history query

**User benefit.** The overview explicitly names residual inspection as an interactive-analysis use case. A user can ask for the residual history after an iteration block.

**Small contribution.** A stateless domain operation returns selected monitor series and their iteration/time coordinates, with a point limit, capture source and incomplete-history notice. An optional example plots those values with Matplotlib. It does not decide convergence or change solver controls.

**Project source.** [capture_residual_history and plot_residual_history](../src/pyansys_fluent/postprocess_live.py), [_read_monitors](../src/pyansys_fluent/native_run_monitor.py), and [test_postprocess_live.py](../tests/test_postprocess_live.py).

**Adaptation.** Preserve an existing monitor stream's ownership. Replace our settling sleep with a bounded readiness condition, avoid stopping another subscriber, and label unavailable or partial history. Ordinary settings readback contains monitor configuration and does not automatically provide historical solution values. Use the existing backend/domain-tool pattern; keep calls serialised.

**Acceptance checks.** Missing history, fresh attachment, uneven series, nonfinite values, output bound and owned-versus-existing stream. No persistent monitoring process or scheduler. This is the clearest new-tool candidate if maintainers want another results query.

### F06 — Correct report retrieval for a supported remote session

**User benefit.** Remote attach is an official option. “Summarise the current setup” should either return the summary or explain why it could not retrieve it.

**Source-level concern.** `summarize_setup()` creates a temporary pathname on the MCP host, passes it to Fluent to write, then reads that pathname on the MCP host. A remote solver without a shared filesystem can write elsewhere or reject the path. The current result can be `(no output)` after successful command execution. This review did not reproduce the complete operation against a live remote solver, so the exact failure depends on host paths and deployment.

**Possible small change.** Retrieve that operation's output through a supported backend file-transfer service or a narrowly scoped transcript capture. Report retrieval failure explicitly. Preserve the tool and session lifecycle; do not add an arbitrary remote-file browser or shell bridge.

**Project source.** [read_text_bounded](../src/pyansys_fluent/remote_text.py) demonstrates distinguishing missing text from empty text, and [SessionTranscriptCapture](../src/pyansys_fluent/dpm_transcript.py) demonstrates callback-based capture. Prefer a supported upstream file service over copying our Scheme route. Capture the generated report, not general remote files.

**Acceptance checks.** Local, remote without shared paths, remote with shared paths, empty report, unavailable transfer and delayed output. First establish the supported remote path/service route; this candidate is below the confirmed comparison issue.

## Disposition of the initial 12 ideas

| Initial candidate | Revised decision | Reason |
| --- | --- | --- |
| C01 documentation | Keep as F03 | Supports the official interaction loop directly |
| C02 preserve attached Fluent | Drop from recommended upstream work | Official docs explicitly require cleanup when finished; our long-lived endpoint policy is a different host choice |
| C03 native progress | Narrow to F04 | Improve a single existing status response; keep serial execution and normal cleanup |
| C04 standalone captured-snapshot comparison | Replace with F01/F02 in existing `compare_files` | Improve their documented comparison operation rather than introduce our evidence-file workflow |
| C05 new `verify_state` tool | Defer; use an example first | Existing `get_state` and targeted context already let the client verify a change; a new tool needs demand beyond our acceptance contract |
| C06 monitor history | Keep as F05, conditional new capability | Matches explicit interactive residual-analysis use; no background monitor |
| C07 generic remote file preflight | Defer; narrower report retrieval is F06 | Improve a supported tool outcome before adding another general inspection surface |
| C08 DPM summary parser | Keep as a later domain-specific possibility | Could serve particle-analysis users, but current evidence does not make it the strongest general contribution; needs neutral version fixtures and unknown-counter handling |
| C09 general transcript tool | Reuse capture internals in F06 first | A whole persistent transcript buffer/cursor service is larger than the current request |
| C10 parallel ranks | Optional metadata in F04 later | Informative, but not the first demonstrated failure in their documented workflow |
| C11 offline HDF5 mesh metadata | Defer | Their normal mesh-inspection path already uses `mesh_quality`; a separate offline route needs a clear user request |
| C12 save/reopen and recovery procedure | Narrow to an official-style example | Keep validation/readback examples; do not impose our scientific acceptance or preserve-across-chats policy |

Our EWF drain mechanisms, separator mass ledgers, native campaign dispatch, Windows OS-command helpers, and exact-thread wakeups remain project/host work. DPM or EWF examples can still be useful contributions when they use the official client-led workflow and establish only the behaviour they demonstrate.

## Recommended first contribution brief

**Proposed title:** `fix: report incomplete state reads in compare_files`

**Problem:** comparing two identical error snapshots can produce a successful “No differences” summary, even when no state was read.

**Scope:** snapshot completeness/error metadata, result status/coverage, and comparison summary. No new MCP tool or persistent state. Keep file loading, temporary-session ownership, default comparison scope and cleanup.

**Project contribution:** extract the principle and small checks from our failed-observation handling, plus regression cases. Do not copy our `p4p.*` schema or scientific acceptance engine.

**Reviewable change:** one focused patch to comparison collection/formatting and tests, plus a changelog fragment and one documentation example of an incomplete comparison. The exact partial-result schema must match maintainer conventions.

**Follow-up only:** optional selected named-object values, then on-demand residual history if maintainers want the extra result tool. Both need appropriate live qualification.

The use-case reproductions are retained in `../output/pyfluent-mcp-audit/20261020/fit-probes.py` and `fit-probes.json`. They run current upstream code with fake backends; no Fluent session was used. The subsequently prepared local implementation and its validation are owned by the linked patch bundle. No upstream issue, PR or external message has been submitted. Upstream acceptance remains a maintainer decision.
