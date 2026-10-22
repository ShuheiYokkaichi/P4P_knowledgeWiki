import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path

from ansys.fluent.mcp.solve.backends.pyfluent import PyFluentBackend
from ansys.fluent.mcp.solve.backends import introspection as intro
from ansys.fluent.mcp.solve.lib.compare_tools import compare_files_impl

root = Path(r"C:\Users\Shuhei Yokkaichi\Documents\CFD\FluentDirectUse")
cases = root / "mcp-compare-cases"
out = {"machine": os.environ["COMPUTERNAME"], "started": time.time(), "stage": "start"}
target = root / ("desktop-compare-" + "-".join(sys.argv[1:]) + ".json" if len(sys.argv) > 1 else "desktop-compare.json")


def save():
    target.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")


async def main():
    for label, a, b in [
        ("equal", "mixing_elbow.cas.h5", "mixing_elbow_copy.cas.h5"),
        ("energy", "mixing_elbow.cas.h5", "energy_off.cas.h5"),
        ("size_limit", "mixing_elbow.cas.h5", "mixing_elbow_copy.cas.h5"),
    ]:
        if len(sys.argv) > 1 and label not in sys.argv[1:]:
            continue
        out["stage"] = label
        save()
        started = time.monotonic()
        old_limit = intro._MAX_STATE_BYTES
        if label == "size_limit":
            intro._MAX_STATE_BYTES = 1
        try:
            result = await compare_files_impl(PyFluentBackend(), path_a=str(cases / a), path_b=str(cases / b))
        finally:
            intro._MAX_STATE_BYTES = old_limit
        out[label] = {"seconds": round(time.monotonic() - started, 2), "result": result}
        save()
    out["stage"] = "finished"


try:
    asyncio.run(main())
except BaseException:
    out["exception"] = traceback.format_exc()
finally:
    out["finished"] = time.time()
    save()
    print("RESULT", out["stage"], out.get("exception", ""), flush=True)
