#!/usr/bin/env python3
"""Build both distributions and smoke-test the installed wheel in isolation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REQUIRED_WHEEL = {
    "nsforge_mcp/capabilities.json",
    "nsforge_mcp/server.py",
    "nsforge_mcp/primitives.py",
    "nsforge_mcp/tool_contract.py",
    "nsforge/domain/strict_provenance.py",
    "nsforge/application/strict_run.py",
    "nsforge/infrastructure/sqlite_run_store.py",
    "nsforge/infrastructure/storage_paths.py",
}
REQUIRED_SDIST_SUFFIXES = {
    "/pyproject.toml",
    "/README.md",
    "/src/nsforge_mcp/server.py",
    "/docs/agent/capabilities.json",
}


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(  # noqa: S603
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> int:
    uv = shutil.which("uv")
    if uv is None:
        print("package smoke requires uv", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="nsforge-package-") as tmp:
        workspace = Path(tmp)
        output = workspace / "dist"
        _run([uv, "lock", "--check"], cwd=REPO)
        _run([uv, "build", "--out-dir", str(output)], cwd=REPO)

        wheels = list(output.glob("*.whl"))
        sdists = list(output.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise RuntimeError(f"expected one wheel and one sdist, got {wheels=} {sdists=}")

        with zipfile.ZipFile(wheels[0]) as archive:
            wheel_names = set(archive.namelist())
        missing_wheel = REQUIRED_WHEEL - wheel_names
        if missing_wheel:
            raise RuntimeError(f"wheel is missing required files: {sorted(missing_wheel)}")

        with tarfile.open(sdists[0], mode="r:gz") as archive:
            sdist_names = archive.getnames()
        missing_sdist = {
            suffix
            for suffix in REQUIRED_SDIST_SUFFIXES
            if not any(name.endswith(suffix) for name in sdist_names)
        }
        if missing_sdist:
            raise RuntimeError(f"sdist is missing required files: {sorted(missing_sdist)}")

        venv = workspace / "venv"
        _run([uv, "venv", "--python", sys.executable, str(venv)], cwd=workspace)
        python = _venv_python(venv)
        _run([uv, "pip", "install", "--python", str(python), str(wheels[0])], cwd=workspace)

        smoke = """
import asyncio
import os
from mcp import Client
from mcp.types import ResourceLink
from nsforge_mcp.server import create_server

async def main():
    # Compatibility surface: the installed wheel must retain the default 82.
    os.environ.pop("NSFORGE_ENABLE_MUSIC", None)
    os.environ.pop("NSFORGE_TOOL_PROFILE", None)
    async with Client(create_server(), raise_exceptions=True) as client:
        assert client.protocol_version == "2026-07-28"
        tools = await client.list_tools()
        assert len(tools.tools) == 82
        result = await client.call_tool("parse_expression", {"expression": "x + 1"})
        assert result.is_error is False
        assert result.structured_content["success"] is True

    # Complete discovery surface: all 91 catalog tools remain installable.
    os.environ["NSFORGE_TOOL_PROFILE"] = "full"
    async with Client(create_server(), raise_exceptions=True) as client:
        assert len((await client.list_tools()).tools) == 91

    # Recommended strict workflow: trusted verification persists immutable run
    # and artifact resources, and returns resolvable ResourceLinks.
    os.environ["NSFORGE_TOOL_PROFILE"] = "workflow"
    os.environ["NSFORGE_TENANT_ID"] = "package-smoke"
    os.environ["NSFORGE_RUN_DB"] = "strict-smoke.sqlite3"
    spec = {
        "name": "package_smoke",
        "goal": "derive y",
        "given": {"x": "scalar"},
        "unknowns": ["y"],
        "base_formulas": ["y = x + 1"],
        "acceptance": [
            {"kind": "equivalence", "params": {"reference": "x + 1"}}
        ],
    }
    async with Client(create_server(), raise_exceptions=True) as client:
        assert len((await client.list_tools()).tools) == 17
        result = await client.call_tool("task_run", {"spec": spec})
        payload = result.structured_content
        assert payload["execution_status"] == "completed"
        assert payload["verification_status"] == "verified"
        assert payload["generated_code"]
        links = [item for item in result.content if isinstance(item, ResourceLink)]
        assert len(links) >= 4
        for link in links:
            assert (await client.read_resource(str(link.uri))).contents

asyncio.run(main())
"""
        clean_env = dict(os.environ)
        clean_env.pop("PYTHONPATH", None)
        clean_env.pop("NSFORGE_ENABLE_MUSIC", None)
        clean_env.pop("NSFORGE_TOOL_PROFILE", None)
        clean_env.pop("NSFORGE_TENANT_ID", None)
        clean_env.pop("NSFORGE_RUN_DB", None)
        _run([str(python), "-c", smoke], cwd=workspace, env=clean_env)

    print("package smoke ok: sdist + wheel inventory and isolated MCP client")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
