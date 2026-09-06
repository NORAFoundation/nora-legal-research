from __future__ import annotations

import argparse
import json
from pathlib import Path

from nora_legal_research.contracts import ResearchSnapshot
from nora_legal_research.provider_contract import ProviderSearchRequestModel, ProviderSearchResponseModel


SCHEMAS = {
    "research-snapshot-v1.schema.json": ResearchSnapshot,
    "provider-search-request-v1.schema.json": ProviderSearchRequestModel,
    "provider-search-response-v1.schema.json": ProviderSearchResponseModel,
}


def generate(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMAS.items():
        output = model.model_json_schema()
        output["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (destination / filename).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("schemas"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            generate(Path(directory))
            for filename in SCHEMAS:
                expected = (args.output / filename).read_bytes()
                actual = (Path(directory) / filename).read_bytes()
                if expected != actual:
                    raise SystemExit(f"schema is stale: {filename}")
        return 0
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
