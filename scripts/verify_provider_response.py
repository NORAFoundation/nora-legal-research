from __future__ import annotations

import argparse
from pathlib import Path

from nora_legal_research.provider_contract_check import validate_provider_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args()
    import json

    validate_provider_payload(json.loads(args.response.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
