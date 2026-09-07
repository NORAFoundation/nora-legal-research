# Validation evidence

| Check | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q` | PASS — 71 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/generate_schemas.py --check` | PASS |
| Draft 2020-12 parse plus request/response/snapshot fixture validation via `jsonschema` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m nora_legal_research.provider_contract_check --response fixtures/provider-contract/response-supporting.json` | PASS |
| Same checker with `response-unavailable.json` | PASS — typed `PROVIDER_UNAVAILABLE` |
| Same checker with `response-malformed.json` | PASS — rejected, exit 2 |
| Sidecar `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q -p no:cacheprovider` | PASS — 31 passed |
| Public demo `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q -rA` | PASS — 1 passed |
| Sidecar image build `nora-public-law-sidecar:0.1.4` | PASS — digest `sha256:875757c63d604cb471d0dd86a58f2b66aa080335904f3b2d62452f05a9a35c65` |
| Trivy sidecar scan | PASS — CRITICAL/HIGH/MEDIUM/LOW all 0 |
| `ruff check .` / `python3 -m ruff check .` | SKIPPED — ruff unavailable; not installed because not a required release dependency |
| `git diff --check` | PASS |
| `make validate` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q tests/test_narrative_compiler.py` | PASS — 12 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q` | PASS — 71 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/generate_schemas.py` plus `--check` | PASS — derived artifact schemas generated from canonical models and current |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src tests` | PASS |
| Draft 2020-12 validation of all generated schemas | PASS — 16 schemas |
| `scripts/sync_public_snapshot_schema.py --check` for sidecar and public demo | PASS |
| `make validate` | PASS |
| Read-only mirror poll after quality pass | PASS — `origin/main` `ca9201f`, `COURTLISTENER_MIRROR_PROVIDER=BLOCKED_BOUNDED_LIVE_PROOF` |
