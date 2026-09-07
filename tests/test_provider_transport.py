import json
from pathlib import Path

import pytest

from nora_legal_research.contracts import TreatmentStatus
from nora_legal_research.normalize import normalize_provider_result
from nora_legal_research.provider_contract import (
    ProviderSearchRequestModel,
    ProviderSearchResponseModel,
    serialize_provider_request,
)
from nora_legal_research.providers import AuthorityResearchRequest, CourtListenerMirrorProvider
from nora_legal_research.transport import (
    FixtureTransport,
    McpMirrorTransport,
    ProviderContractError,
    ProviderPartialResult,
    ProviderUnavailable,
)


ROOT = Path(__file__).parents[1]


def request() -> AuthorityResearchRequest:
    return AuthorityResearchRequest(
        provider_contract_version=1,
        research_id="R-004", jurisdiction="US-WI", court_level="state_appellate",
        doctrinal_issue="speedy_trial", target_proposition="P-004",
        query_variants=("speedy trial continuance", "adverse speedy trial"),
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
    assert snapshot.provider.mirror_git_sha == "a" * 64
    assert snapshot.provenance[0].retrieved_at is not None
    assert snapshot.provenance[0].query_plan_hash == snapshot.reproducibility["query_plan_hash"]
    assert snapshot.currentness.status == TreatmentStatus.UNKNOWN
    assert snapshot.authorities[0].quote_verification.value == "not_available"
    assert snapshot.authorities[0].provider_rank == 1
    assert snapshot.provider.access_mode == "FIXTURE"


def test_empty_and_partial_results_are_not_failures_or_no_law_claims() -> None:
    empty = CourtListenerMirrorProvider(FixtureTransport(response("response-empty.json"))).search(request())
    partial = CourtListenerMirrorProvider(FixtureTransport(response("response-partial.json"))).search(request())
    assert empty.authorities == ()
    assert empty.retrieval_status.value == "empty"
    assert partial.retrieval_status.value == "partial"
    assert partial.limitations
    with pytest.raises(ProviderPartialResult):
        normalize_provider_result(request(), partial)


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
    assert result.access_mode == "MCP"
    assert result.authorities[0]["provider_record_id"] == "CL-A-2"
    assert calls[0][0] == "search_authorities"
    assert "research_id" in calls[0][1]
    assert calls[0][1]["query"] == "speedy trial continuance OR adverse speedy trial"


def test_mcp_transport_rejects_service_native_unwrapped_payload() -> None:
    def invoke(_tool_name, _arguments):
        return {"query": "speedy trial", "authorities": []}

    with pytest.raises(ProviderContractError):
        McpMirrorTransport(invoke).search(request())


def test_request_serialization_is_an_explicit_public_allowlist() -> None:
    value = request()
    payload = serialize_provider_request(value)
    assert set(payload) == {
        "provider_contract_version", "research_id", "jurisdiction", "court_level",
        "doctrinal_issue", "target_proposition", "query_variants", "date_range",
        "date_from", "date_to", "limit", "requested_capabilities",
    }
    assert "private_case_number" not in payload
    with pytest.raises(Exception):
        ProviderSearchRequestModel.model_validate({
            **payload,
            "party_names": ["Private Person"],
        })


@pytest.mark.parametrize(
    "private_field",
    [
        "party_names",
        "private_case_number",
        "private_chronology",
        "private_source_text",
        "email_addresses",
        "addresses",
        "local_filesystem_paths",
        "matter_confidential_facts",
    ],
)
def test_request_boundary_rejects_private_fields(private_field: str) -> None:
    payload = serialize_provider_request(request())
    with pytest.raises(Exception):
        ProviderSearchRequestModel.model_validate({**payload, private_field: "PRIVATE-CANARY"})


def test_requested_capability_must_be_negotiated_by_response() -> None:
    demanding_request = request().model_copy(update={"requested_capabilities": ("opinion_retrieval",)})
    provider = CourtListenerMirrorProvider(FixtureTransport(response("response-adverse.json")))
    with pytest.raises(Exception) as exc:
        provider.search(demanding_request)
    assert exc.value.info.code == "UNSUPPORTED_PROVIDER_CAPABILITY"


def test_provider_contract_rejects_missing_snapshot_identity() -> None:
    body = response("response-empty.json").model_dump(mode="json")
    body.pop("snapshot_id")
    with pytest.raises(Exception):
        ProviderSearchResponseModel.model_validate(body)


def test_provider_contract_version_fails_closed_at_model_boundary() -> None:
    with pytest.raises(Exception):
        ProviderSearchRequestModel(
            research_id="R-004",
            jurisdiction="US-WI",
            court_level="state_appellate",
            doctrinal_issue="speedy_trial",
            target_proposition="P-004",
        )
    with pytest.raises(Exception):
        ProviderSearchRequestModel(
            provider_contract_version=2,
            research_id="R-004",
            jurisdiction="US-WI",
            court_level="state_appellate",
            doctrinal_issue="speedy_trial",
            target_proposition="P-004",
        )
    body = response("response-empty.json").model_dump(mode="json")
    body["provider_contract_version"] = 2
    with pytest.raises(Exception):
        ProviderSearchResponseModel.model_validate(body)
