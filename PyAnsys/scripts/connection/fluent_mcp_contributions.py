"""Run the official MCP with the opt-in P4P contribution laboratory tools.

Use the same CLI flags, connection tools, and explicit disconnect as upstream.
Requires upstream f56e540 and PyFluent 0.42.x; see the contribution guide.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ansys.fluent.mcp.server import _argparser, _run
from ansys.fluent.mcp.solve import SolveMCP
from pyansys_fluent.mcp_additions.integration import register_additions


def main():
    args = _argparser().parse_args()
    server = SolveMCP(name="ansys-fluent-mcp-contributions", default_backend_kind=args.backend)
    register_additions(server)
    _run(server, args)


if __name__ == "__main__":
    main()
