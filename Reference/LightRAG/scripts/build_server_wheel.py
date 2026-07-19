"""Build a LightRAG server wheel and verify that it contains the WebUI.

Run from any directory with::

    python scripts/build_server_wheel.py

Bun and uv must already be available on PATH. The frontend dependency graph is
resolved from ``lightrag_webui/bun.lock`` with ``--frozen-lockfile``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEBUI = ROOT / "lightrag_webui"
WEBUI_INDEX = ROOT / "lightrag" / "api" / "webui" / "index.html"
DIST = ROOT / "dist"
WHEEL_INDEX = "lightrag/api/webui/index.html"


def require_command(name: str) -> str:
    command = shutil.which(name)
    if command is None:
        raise SystemExit(f"Required command not found on PATH: {name}")
    return command


def run(command: list[str], *, cwd: Path) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    bun = require_command("bun")
    uv = require_command("uv")

    run([bun, "install", "--frozen-lockfile"], cwd=WEBUI)
    run([bun, "run", "build"], cwd=WEBUI)
    if not WEBUI_INDEX.is_file():
        raise SystemExit(f"WebUI build did not create {WEBUI_INDEX}")

    DIST.mkdir(exist_ok=True)

    # setuptools reuses build/lib between invocations. Remove stale package
    # discovery output so a previous build cannot leak frontend dependencies
    # into the release wheel.
    for stale_dir in (ROOT / "build", ROOT / "lightrag_hku.egg-info"):
        if stale_dir.exists():
            shutil.rmtree(stale_dir)
    for stale_wheel in DIST.glob("lightrag_hku-*.whl"):
        stale_wheel.unlink()

    run([uv, "build", "--wheel", "--out-dir", str(DIST)], cwd=ROOT)

    wheels = sorted(DIST.glob("lightrag_hku-*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise SystemExit(f"No LightRAG wheel found in {DIST}")
    wheel = wheels[-1]

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    if WHEEL_INDEX not in names:
        raise SystemExit(f"Built wheel does not contain {WHEEL_INDEX}: {wheel}")

    unexpected = sorted(
        name
        for name in names
        if name.startswith("lightrag_webui/") or "/node_modules/" in name
    )
    if unexpected:
        preview = "\n  ".join(unexpected[:10])
        raise SystemExit(
            f"Built wheel contains frontend source dependencies:\n  {preview}"
        )

    print(f"Verified WebUI-enabled wheel: {wheel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
