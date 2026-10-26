"""Live stdio MCP capacity/retrieval demo using an actual native report file."""
import argparse
import asyncio
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport


async def demonstrate(source_file, output_root, upstream_source, cancellation_source_file):
    repo = Path(__file__).resolve().parents[3]
    out = Path(output_root) / ("transport-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    source = Path(source_file).resolve(strict=True)
    (out / "native-history.out").write_bytes(source.read_bytes())
    cancellation_source = Path(cancellation_source_file).resolve(strict=True)
    cancellation_bytes = cancellation_source.read_bytes()
    if not 500_000 <= len(cancellation_bytes) <= 690_000:
        raise ValueError("Supply a saved native OUT file of 500000-690000 bytes for the cancellation demonstration")
    # These are byte-identical copies of one native report, selected to keep
    # the real ZIP worker active long enough for external request cancellation.
    cancellation_files = [f"cancel-source-{index:02d}.out" for index in range(24)]
    for name in cancellation_files:
        (out / name).write_bytes(cancellation_bytes)
    package = repo / "PyAnsys/src/pyansys_fluent/mcp_additions"
    calls = []

    def dump(name, value):
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")

    launcher = repo / "PyAnsys/scripts/connection/fluent_mcp_contributions.py"
    dump("identity.json", {"transport": "external Python process over stdio", "launcher": str(launcher),
        "launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_file": str(source), "native_input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "cancellation_source_file": str(cancellation_source),
        "cancellation_source_sha256": hashlib.sha256(cancellation_bytes).hexdigest(),
        "cancellation_source_bytes": len(cancellation_bytes), "cancellation_copies": len(cancellation_files),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob("*.py")}})
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join([str(Path(upstream_source) / "src"), str(repo / "PyAnsys/src")])
    transport = PythonStdioTransport(launcher, args=["--transport", "stdio"], env=environment,
        cwd=str(out), python_cmd=sys.executable, keep_alive=False, log_file=out / "server-stderr.log")
    async with Client(transport) as client:
        dump("schemas.json", [t.model_dump(mode="json") for t in await client.list_tools()])

        async def call(label, arguments):
            sent = deepcopy(arguments)
            result = await client.call_tool("bundle_artifacts", arguments, raise_on_error=False)
            calls.append({"label": label, "arguments": sent, "is_error": result.is_error,
                "structured_content": result.structured_content,
                "content": [c.model_dump(mode="json") for c in result.content]})
            if len(calls) % 16 == 0 or label.startswith("boundary"):
                dump("calls.json", calls)
                print("TRANSPORT_DEMO", label, len(calls), flush=True)
            return result

        def arguments(name, files=None):
            return {"root": str(out), "files": files or ["native-history.out"], "output": str(out / name)}

        cancelled_path = out / "cancelled.zip"
        cancellation_arguments = arguments(cancelled_path.name, cancellation_files)
        # The SDK exposes no call handle for ordinary requests. Capture its
        # next protocol ID before dispatch, then send the real MCP notification.
        cancelled_request_id = client.session._request_id
        cancelled = asyncio.create_task(client.call_tool("bundle_artifacts", cancellation_arguments))
        deadline = asyncio.get_running_loop().time() + 30
        while not cancelled_path.exists():
            if cancelled.done():
                raise RuntimeError("Bundle finished before cancellation could be demonstrated")
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError("Native-input ZIP worker did not publish before deadline")
            await asyncio.sleep(0.001)
        extent_at_cancellation = cancelled_path.stat().st_size
        await client.cancel(cancelled_request_id, reason="Demonstrate ownership of an active native-input ZIP publication")
        cancelled.cancel()
        cancellation_observed = False
        try:
            await cancelled
        except asyncio.CancelledError:
            cancellation_observed = True
        cancellation_resource = None
        cancellation_reads = []
        while asyncio.get_running_loop().time() < deadline:
            data = cancelled_path.read_bytes()
            uri = "artifact://mcp-additions/bundles/" + hashlib.sha256(data).hexdigest()
            try:
                cancellation_resource = await client.read_resource(uri)
                break
            except Exception as exc:
                cancellation_reads.append(str(exc))
                await asyncio.sleep(0.01)
        if cancellation_resource is None:
            raise RuntimeError("Cancelled publication never registered its completed resource")
        cancellation_data = b"".join(base64.b64decode(r.blob) for r in cancellation_resource)
        dump("cancellation.json", {"arguments": cancellation_arguments,
            "cancelled_request_id": cancelled_request_id, "cancellation_notification_sent": True,
            "request_cancelled": cancellation_observed, "bytes_at_cancellation": extent_at_cancellation,
            "final_bytes": len(cancellation_data), "worker_continued_after_cancellation": len(cancellation_data) > extent_at_cancellation,
            "resource_uri": uri, "resource_matches_final_file": cancellation_data == cancelled_path.read_bytes(),
            "resource_mime_types": [r.mimeType for r in cancellation_resource],
            "pending_read_errors": cancellation_reads})

        failed = await call("failed-worker-releases-reservation", arguments("failed.zip", ["missing-native.out"]))
        populated = []
        for index in range(126):
            response = await call(f"populate-{index:03d}", arguments(f"bundle-{index:03d}.zip"))
            populated.append(response)
        boundary = await asyncio.gather(
            call("boundary-a", arguments("boundary-a.zip")),
            call("boundary-b", arguments("boundary-b.zip")))
        full = await call("full-registry-refusal", arguments("over-capacity.zip"))
        successful = [r for r in populated + boundary if not r.is_error]
        uri = successful[-1].structured_content["resource_uri"]
        resource = await client.read_resource(uri)
        dump("resource-response.json", {"uri": uri, "contents": [r.model_dump(mode="json") for r in resource]})
        data = b"".join(base64.b64decode(r.blob) for r in resource)
        dump("checks.json", {"failed_worker_refused": failed.is_error,
            "initial_successes": sum(not r.is_error for r in populated),
            "initial_distinct_resources": len({r.structured_content["resource_uri"] for r in populated if not r.is_error}),
            "concurrent_boundary_successes": sum(not r.is_error for r in boundary),
            "concurrent_boundary_refusals": sum(r.is_error for r in boundary),
            "cancelled_publication_registered": cancellation_data == cancelled_path.read_bytes(),
            "total_registered_resources": 1 + len({r.structured_content["resource_uri"] for r in successful}),
            "full_registry_refused": full.is_error,
            "refused_output_absent": not (out / "over-capacity.zip").exists(),
            "resource_bytes": len(data), "resource_sha256": hashlib.sha256(data).hexdigest(),
            "resource_matches_receipt": hashlib.sha256(data).hexdigest() == successful[-1].structured_content["zip"]["sha256"],
            "resource_mime_types": [r.mimeType for r in resource]})
        dump("calls.json", calls)
    print("TRANSPORT_DEMO_RECEIPT", out, flush=True)
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--upstream-source", required=True)
    parser.add_argument("--cancellation-source-file", required=True)
    args = parser.parse_args()
    asyncio.run(demonstrate(args.source_file, args.output_root, args.upstream_source, args.cancellation_source_file))
