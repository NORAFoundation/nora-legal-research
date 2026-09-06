import json
from pathlib import Path

import pytest

from nora_legal_research.contracts import TreatmentStatus
from nora_legal_research.normalize import normalize_provider_result
from nora_legal_research.provider_contract import ProviderSearchRequestModel, ProviderSearchResponseModel
from nora_legal_research.providers import AuthorityResearchRequest, CourtListenerMirrorProvider
from nora_legal_research.transport import (
    FixtureTransport,
    McpMirrorTransport,
    ProviderContractError,
    ProviderUnavailable,
)


ROOT = Path(__file__).parents[1]


def request() -> AuthorityResearchRequest:
    return AuthorityResearchRequest(
        research_id="R-004", jurisdiction="US-WI", court_level="state_appellate",
        doctrinal_issue="speedy_trial", target_proposition="P-004",
        query_variants=("speedy trial continuance",),
    )


def response(name: str) -> ProviderSearchResponseModel:
    return ProviderSearchResponseModel.model_validate_json(
        (ROOT / "fixtures/provider-contract" / name).read_bytes()
    )


def test_fixture_mirror_provider_to_snapshot_preserves_snapshot_and_unknown_currentness() -> None:
    provider = CourtListenerMirrorProvider(FixtureTransport(response("response-supporting.json")))
    result = provider.search(request())
    snapshot = normalize_provider_result(request(), result)
    assert snapshot.provider.provider_name == "COURTLISTENER_MIRROR"
    assert snapshot.provider.snapshot_id == "CL-2026-06-30"
    assert snapshot.currentness.status == TreatmentStatus.UNKNOWN
    assert snapshot.authorities[0].quote_verification.value == "not_available"


def test_empty_and_partial_results_are_not_failures_or_no_law_claims() -> None:
    empty = CourtListenerMirrorProvider(FixtureTransport(response("response-empty.json"))).search(request())
    partial = CourtListenerMirrorProvider(FixtureTransport(response("response-partial.json"))).search(request())
    assert empty.authorities == ()
    assert partial.limitations


def test_malformed_response_and_request_canary_fail_closed() -> None:
    with pytest.raises(Exception):
        ProviderSearchResponseModel.model_validate_json((ROOT / "fixtures/provider-contract/response-malformed.json").read_bytes())
    with pytest.raises(ValueError):
        ProviderSearchRequestModel(research_id="R-004", jurisdiction="US-WI", court_level="state_appellate", doctrinal_issue="speedy_trial", target_proposition="P-004", query_variants=["private@example.invalid"])


def test_fixture_provider_rejects_wrong_research_id() -> None:
    fixture = response("response-supporting.json").model_copy(update={"research_id": "R-999"})
    provider = CourtListenerMirrorProvider(FixtureTransport(fixture))
    with pytest.raises(ProviderContractError):
        provider.search(request())


def test_mcp_transport_requires_versioned_provider_envelope() -> None:
    fixture = response("response-adverse.json").model_dump(mode="json")
    calls = []

    def invoke(tool_name, arguments):
        calls.append((tool_name, arguments))
        return fixture

    result = McpMirrorTransport(invoke).search(request())
    assert result.provider == "COURTLISTENER_MIRROR"
    assert result.authorities[0]["provider_record_id"] == "CL-A-2"
    assert calls[0][0] == "search_authorities"
    assert "research_id" in calls[0][1]


def test_mcp_transport_rejects_service_native_unwrapped_payload() -> None:
    def invoke(_tool_name, _arguments):
        return {"query": "speedy trial", "authorities": []}

    with pytest.raises(ProviderContractError):
        McpMirrorTransport(invoke).search(request())
