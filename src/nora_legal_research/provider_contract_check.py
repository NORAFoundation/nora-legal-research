from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .errors import ProviderErrorEnvelope
from .provider_contract import ProviderSearchResponseModel


def validate_provider_payload(value: object) -> str:
    """Validate one successful or typed-failure provider envelope."""

    try:
        response = ProviderSearchResponseModel.model_validate(value)
        return f"response provider={response.provider_name} research_id={response.research_id} authorities={len(response.authorities)}"
    except ValidationError:
        try:
            failure = ProviderErrorEnvelope.model_validate(value)
        except ValidationError as failure_error:
            raise ValueError("payload is neither a valid provider response nor typed failure") from failure_error
        if failure.provider_contract_version != 1:
            raise ValueError("unsupported provider contract version")
        return f"failure code={failure.error.code} research_id={failure.research_id}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a canonical mirror-provider contract payload.")
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.response.read_text(encoding="utf-8"))
        print(validate_provider_payload(value))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"provider contract validation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
