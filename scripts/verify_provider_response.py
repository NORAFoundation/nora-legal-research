from __future__ import annotations

import argparse
import json
from pathlib import Path

from nora_legal_research.provider_contract import ProviderSearchResponseModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args()
    ProviderSearchResponseModel.model_validate_json(args.response.read_bytes())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
