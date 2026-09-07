# Validation evidence

| Check | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q` | PASS — 47 passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 scripts/generate_schemas.py --check` | PASS |
| Draft 2020-12 parse plus request/response/snapshot fixture validation via `jsonschema` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m nora_legal_research.provider_contract_check --response fixtures/provider-contract/response-supporting.json` | PASS |
| Same checker with `response-unavailable.json` | PASS — typed `PROVIDER_UNAVAILABLE` |
| Same checker with `response-malformed.json` | PASS — rejected, exit 2 |
| Sidecar `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q -p no:cacheprovider` | PASS — 31 passed |
| Public demo `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q -p no:cacheprovider` | PASS — 42 passed |
| Sidecar image build `nora-public-law-sidecar:0.1.3` | PASS — digest `sha256:5fcffa4c564324fc8175ac23a4b43a68da6bc1eceb4dcc241b6f51e18b1a960f` |
| Trivy sidecar scan | PASS — CRITICAL/HIGH/MEDIUM/LOW all 0 |
| `ruff check .` / `python3 -m ruff check .` | SKIPPED — ruff unavailable; not installed because not a required release dependency |
| `git diff --check` | PASS |
| `make validate` | PASS |
