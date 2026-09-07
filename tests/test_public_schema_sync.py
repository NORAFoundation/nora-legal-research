from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
TARGETS = [
    ROOT.parent / "litigation-db/12_APPS_AND_PIPELINES/apps/nora_public_law_sidecar/src/nora_public_law_sidecar/schemas/research-snapshot-v1.schema.json",
    ROOT.parent / "litigation-db/12_APPS_AND_PIPELINES/apps/nora_public_demo/src/nora_public_demo/schemas/research-snapshot-v1.schema.json",
]


def test_public_consumer_schema_bundles_match_canonical_source() -> None:
    if not all(path.exists() for path in TARGETS):
        pytest.skip("public consumer repositories are not present in this checkout")
    completed = subprocess.run(
        [sys.executable, "scripts/sync_public_snapshot_schema.py", "--check", *[item for path in TARGETS for item in ("--target", str(path))]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
