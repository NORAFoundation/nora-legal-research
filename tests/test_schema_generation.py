from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_generated_schemas_are_not_stale() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/generate_schemas.py", "--check"],
        cwd=ROOT,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_required_canonical_schema_vectors_exist() -> None:
    expected = {
        "provider-search-request-v1.schema.json",
        "authority-research-request-v1.schema.json",
        "provider-search-result-v1.schema.json",
        "provider-search-response-v1.schema.json",
        "research-snapshot-v1.schema.json",
    }
    assert expected.issubset({path.name for path in (ROOT / "schemas").glob("*.json")})
