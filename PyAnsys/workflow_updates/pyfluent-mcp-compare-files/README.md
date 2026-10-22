# PyFluent MCP comparison fix — review bundle

This is a draft contribution to [ansys/pyfluent-mcp](https://github.com/ansys/pyfluent-mcp). No upstream branch or pull request has been published.

| Item | Record |
| --- | --- |
| Base commit | `f56e540931fbcdf5b9f81871a21934589f256d91` |
| Reviewable implementation | [changes.patch](changes.patch) |
| PR draft | [pyfluent-mcp-comparison-pr.md](../../docs/pyfluent-mcp-comparison-pr.md) |
| Desktop live receipt | [desktop-live-status.json](../../output/pyfluent-mcp-audit/20261022/desktop-live-status.json) |
| Earlier Server 3 receipt | [live-status.json](../../output/pyfluent-mcp-audit/20261021/live-status.json) |

**Status: desktop live acceptance passed on 22 October 2026.** The revised patch changes four upstream files (82 added lines, 27 removed lines) and adds no test code. The earlier, concurrent-session patch failed on Server 3; this revised patch has not been rerun there.

## What changed

`compare_files` could report no differences when both snapshots held the same read errors or omitted-state markers. It now returns `comparison incomplete` with the affected input and path. A lost Fluent connection during named-object fallback traversal also raises an error instead of returning a partial inventory.

The tool still creates and closes a separate temporary Fluent session for each input. It now runs those sessions one after the other. Student Edition could launch one session but refused a second concurrent session. Sequential capture also reduces simultaneous licence and memory use without attaching to or changing the caller's workspace. The patch keeps the headless launch, lightweight file-read, and available run-calculation corrections.

## Desktop live checks

Fluent 2025 R2 Student Edition, PyFluent 0.41.0 and Python 3.13 ran on `HOME-DESKTOP-SH`. The official mixing-elbow case matched SHA-256 `8145813f50f989a521ed8d1b02c891c7ca22ccc5fafa35a4eeba011949f19cbc`.

| Check | Real Fluent result |
| --- | --- |
| Byte-identical case copies | Zero differences |
| Saved energy setting changed from true to false | Change detected; 16 total differences including dependent energy settings and names |
| Real 1-byte capture limit | `comparison incomplete` for both inputs; no summary or difference count |
| Forced loss of an owned test session | Fallback walk raised the native connection-refused `RuntimeError`; it had found 70 collections before disconnect |
| Temporary-session cleanup | No Fluent processes remained after the tool runs |

The [raw desktop receipts and executed harness](../../output/pyfluent-mcp-audit/20261022/raw/) are retained for review. The direct inspection and forced-disconnect harness use the pinned desktop Fluent path and terminate only their own uniquely identified test process tree. Review those scripts before reuse on another machine.

The previous [Server 3 evidence](../../output/pyfluent-mcp-audit/20261021/) remains valid for the older patch: byte-identical cases gave 63 false inventory differences when a connection failed during fallback traversal. The cause of that connection loss was not established. The revised patch has a different session schedule and propagates that failure; its Server 3 result is unverified.

## Reconstruct the upstream checkout

From a separate directory, check out the recorded base and apply this patch:

```sh
git clone https://github.com/ansys/pyfluent-mcp.git pyfluent-mcp-compare
cd pyfluent-mcp-compare
git switch -c fix/compare-files-incomplete-reads f56e540931fbcdf5b9f81871a21934589f256d91
git apply /absolute/path/to/changes.patch
```

The changelog filename `doc/changelog.d/0.fixed.md` is a placeholder for the assigned PR number. Existing upstream tests still assert GUI launch. No offline or mock test run is counted as live acceptance, and no upstream PR has been created.
