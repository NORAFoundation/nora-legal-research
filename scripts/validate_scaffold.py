from pathlib import Path
import sys, yaml

required = [
    "README.md","ARCHITECTURE.md","CONTRIBUTING.md","SECURITY.md","CODE_OF_CONDUCT.md",
    "CURRENT_STATE.md","ROADMAP.md","SOURCE_PROVENANCE.yaml","THIRD_PARTY_NOTICES.md",
    "LICENSE",".github/workflows/ci.yml",".github/PULL_REQUEST_TEMPLATE.md"
]
missing = [p for p in required if not Path(p).exists()]
if missing:
    print("missing:", ", ".join(missing))
    sys.exit(1)

data = yaml.safe_load(Path("SOURCE_PROVENANCE.yaml").read_text())
if not isinstance(data, dict) or "entries" not in data:
    print("invalid SOURCE_PROVENANCE.yaml")
    sys.exit(1)

for forbidden in [".env", "REAL_CASE_DATA", "PRIVATE_MATTER"]:
    if Path(forbidden).exists():
        print("forbidden path:", forbidden)
        sys.exit(1)

print("scaffold validation: PASS")
