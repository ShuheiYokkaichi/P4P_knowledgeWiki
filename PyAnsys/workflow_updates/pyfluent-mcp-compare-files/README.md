# PyFluent MCP comparison fix — local review bundle

This is a contribution draft. No upstream pull request or upstream branch was published. The P4P branch `work/pyfluent-mcp-live-comparison` stores the patch and live evidence for continuation on another machine.

- Target repository: <https://github.com/ansys/pyfluent-mcp>
- Base commit: `f56e540931fbcdf5b9f81871a21934589f256d91`
- Upstream implementation branch to reconstruct: `fix/compare-files-incomplete-reads`
- [Reviewable patch](changes.patch)
- [PR title and description](../../docs/pyfluent-mcp-comparison-pr.md)
- [Design and use-case assessment](../../docs/pyfluent-mcp-contribution-audit.md)
- [Live acceptance receipt](../../output/pyfluent-mcp-audit/20261021/live-status.json)

Status: **LIVE VERIFICATION FAILED — NOT READY TO SUBMIT**. The error guard passed real Fluent checks, but the complete identical-case comparison failed.

The patch changes four files: 44 added lines and three removed lines, including documentation and a release note. It adds no test code. The guard adds 35 production lines; three existing lines correct the headless launch mode, lightweight read command and default run-calculation path. The temporary-session ownership and cleanup design remain in place.

## Apply to an upstream checkout

From a clean checkout at the base commit:

```sh
git apply /absolute/path/to/changes.patch
```

The release-note filename `doc/changelog.d/0.fixed.md` is a local placeholder. Rename it to the assigned PR number if this is submitted.

## Real Fluent results

Checks ran on authorised Server 3, Fluent 2025 R2, Python 3.12.13 and PyFluent 0.41.0, using the official mixing-elbow case and real native settings. No fake backends or fabricated errors were used.

| Check | Live result |
| --- | --- |
| Repeated native snapshots with the unavailable `/parameters` path | Old diff returned zero differences; the guard identified the real read error on both sides |
| Complete, explicitly selected solver and energy paths | Equal captures returned no differences and no errors |
| Change energy, read it back, compare, restore it | Change detected and original setting restored |
| Public tool with a real 1-byte capture cap | Returned `comparison incomplete` for both inputs, without summary or difference count |
| Public tool on byte-identical case copies | **Failed:** returned 63 false named-inventory differences |
| Public tool on a saved energy-disabled case | Energy change detected; extra named-inventory differences remain |
| Owned-process cleanup in the full three-comparison run | No new Fluent processes remained after each check |

The remaining blocker is partial named-inventory collection. The fallback traversal catches connection-refused errors and returns the entries already collected. Its existing error suppression prevents the new guard from seeing those failures. The cause of the temporary-session connection loss is not established. A concurrent-capture experiment repeated the failure and was reverted. The later duplicate test process tree was explicitly stopped.

At the final check on 21 October 2026, the original Server 3 session was serving on port 61996. This is a historical endpoint: reconcile the configured connection and current session before any further use. The final source hashes match the full live run, and the final sources were restored in the private host runtime.

Only real Fluent results count as acceptance. The complete identical-case comparison must pass before this draft is called verified. The unchanged upstream tests also contain GUI launch assertions; no test edits or offline executions are included.

## Continue on the desktop

The actual upstream code is stored as `changes.patch`, pinned to the base commit above. The old Mac checkout under `/tmp` is not needed. From a fresh upstream checkout, create `fix/compare-files-incomplete-reads` at that commit and apply this patch using its absolute path. Keep the upstream checkout outside the P4P repository.

For example, from a separate working directory:

```sh
git clone https://github.com/ansys/pyfluent-mcp.git pyfluent-mcp-compare
cd pyfluent-mcp-compare
git switch -c fix/compare-files-incomplete-reads f56e540931fbcdf5b9f81871a21934589f256d91
git apply /absolute/path/to/P4P_knowledgeWiki/PyAnsys/workflow_updates/pyfluent-mcp-compare-files/changes.patch
```

Use the explicitly invoked [direct-fluent-use skill](../../../.agents/skills/direct-fluent-use/SKILL.md) for rapid desktop checks. It is pinned to `HOME-DESKTOP-SH`, Fluent 2025 R2 Student Edition, and a runtime directory outside the repository. Check the host and installation first. The old Server 3 results came from a different machine and licence; establish desktop results separately. Start with one persistent, owned local Fluent session to inspect the discovery failure directly, then verify the full official temporary-session comparison where the local licence supports it. Do not change the official tool into an attach-only workflow.

The [executed live harness sources](../../output/pyfluent-mcp-audit/20261021/raw/live-harness/) are archived with hashes. These are historical execution evidence, not portable launch scripts. They contain the Server 3 scratch path and Windows runtime layout. Review and adapt them before reuse. `mcp-full-live.py` deploys two source files into its private Python runtime before invoking the actual public comparison function; do not point it at an unrelated environment.

That harness expects `compare_tools_v2.b64` and `introspection_v2.b64` beside it. Regenerate those from the applied upstream `src/ansys/fluent/mcp/solve/lib/compare_tools.py` and `src/ansys/fluent/mcp/solve/backends/introspection.py` using Python `base64.b64encode`. Their decoded SHA-256 hashes must match `source_hashes` in the live receipt if reproducing the recorded run. It also expects the original official mixing-elbow case, a byte-identical copy, and the saved energy-disabled case. The case-preparation source shows how the changed case was created with native readback.

The official starting case is <https://raw.githubusercontent.com/ansys/example-data/main/pyfluent/mixing_elbow/mixing_elbow.cas.h5>. Its SHA-256 is `8145813f50f989a521ed8d1b02c891c7ca22ccc5fafa35a4eeba011949f19cbc`. No case binaries, virtual environments, server credentials or `.env` files are included in this branch.

The old Server 3 private scratch directory was `C:\Users\syok443\Documents\FluentRuns\MCPContribution\20261021`, with Python at `runtime\Scripts\python.exe`. Its files and live status must be reconciled if that machine is used again. For the new desktop work, follow the direct-use skill's local paths instead.
