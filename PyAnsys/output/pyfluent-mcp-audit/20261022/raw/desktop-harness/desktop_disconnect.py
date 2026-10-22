import json
import os
import subprocess
from pathlib import Path

import ansys.fluent.core as pyfluent
from ansys.fluent.mcp.solve.backends import introspection as intro

root_dir = Path(r"C:\Users\Shuhei Yokkaichi\Documents\CFD\FluentDirectUse")
os.chdir(root_dir)
out = {}
solver = pyfluent.launch_fluent(
    product_version="25.2",
    fluent_path=r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\fluent\ntbin\win64\fluent.exe",
    cwd=str(root_dir),
    mode="solver",
    dimension=3,
    precision="double",
    processor_count=4,
    ui_mode="no_gui",
    py=True,
    cleanup_on_exit=False,
    start_transcript=True,
)
try:
    settings = solver.settings
    solver.settings.file.read(
        file_type="case",
        file_name=str(root_dir / "mcp-compare-cases" / "mixing_elbow.cas.h5"),
        lightweight_setup=True,
    )
    out["before_count"] = len(intro.discover_named_objects_via_walk(settings))
    subprocess.run(
        ["powershell", "-NoProfile", "-File", str(root_dir / "stop-owned-test-fluent.ps1")],
        check=True,
    )
    try:
        out["after_count"] = len(intro.discover_named_objects_via_walk(settings))
    except Exception as exc:
        out["after_error_type"] = type(exc).__name__
        out["after_error"] = str(exc)
finally:
    try:
        solver.exit()
    except Exception:
        pass
    (root_dir / "desktop-disconnect.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("DISCONNECT", out, flush=True)
