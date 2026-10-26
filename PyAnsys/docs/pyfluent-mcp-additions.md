# PyFluent MCP contribution laboratory

This branch develops ten small additions for agents that use the official
`ansys/pyfluent-mcp` server. This is a P4P review PR, not an upstream PR.

## Scope

The official server owns a local interactive Fluent session. Keep that session
lifecycle, client-written code, and explicit disconnect behaviour. Do not port
P4P fleet scheduling, scientific acceptance rules, or remote-session ownership.

The attached **Expand PyFluent MCP Capabilities** discussion is background.
Its comparison work is retained in `work/pyfluent-mcp-live-comparison`; this
branch will identify the current upstream base separately.

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
| Upstream inventory and intended workflow | In progress |
| Repository source extraction | In progress |
| Live demonstrations | Pending |
| Independent ratings | Pending |

Implementation belongs under `PyAnsys/src/` and `PyAnsys/scripts/`.
Selected demonstration evidence belongs under `PyAnsys/output/`.
