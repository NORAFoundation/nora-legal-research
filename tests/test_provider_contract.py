from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from nora_legal_research.errors import ProviderErrorEnvelope
from nora_legal_research.provider_contract import ProviderSearchResponseModel
from nora_legal_research.provider_contract_check import validate_provider_payload


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "fixtures/provider-contract"


@pytest.mark.parametrize(
    "name",
    [
        "response-supporting.json",
        "response-adverse.json",
        "response-empty.json",
        "response-partial.json",
        "response-multi-opinion.json",
    ],
)
def test_success_fixture_vectors_validate(name: str) -> None:
    body = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    response = ProviderSearchResponseModel.model_validate(body)
    assert response.provider_name == "COURTLISTENER_MIRROR"
    assert response.snapshot_id


def test_malformed_and_wrong_version_vectors_fail_closed() -> None:
    for name in ("response-malformed.json", "response-wrong-version.json"):
        with pytest.raises(ValidationError):
            ProviderSearchResponseModel.model_validate_json((FIXTURES / name).read_bytes())


def test_unavailable_vector_is_typed_failure_not_empty_success() -> None:
    body = json.loads((FIXTURES / "response-unavailable.json").read_text(encoding="utf-8"))
    failure = ProviderErrorEnvelope.model_validate(body)
    assert failure.error.code == "PROVIDER_UNAVAILABLE"
    assert validate_provider_payload(body).startswith("failure code=PROVIDER_UNAVAILABLE")


def test_provider_contract_checker_rejects_marker_only_or_private_response() -> None:
    with pytest.raises(ValueError):
        validate_provider_payload({"provider_name": "COURTLISTENER_MIRROR", "research_id": "R-004"})
    private = json.loads((FIXTURES / "response-supporting.json").read_text(encoding="utf-8"))
    private["authorities"][0]["private_case_number"] = "CONFIDENTIAL-123"
    with pytest.raises(ValueError):
        ProviderSearchResponseModel.model_validate(private)
