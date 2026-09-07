from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nora_legal_research.contracts import (
    AuthorityRecord,
    ResearchSnapshot,
    PrecedentialStatus,
    TreatmentStatus,
    VerificationStatus,
)
from nora_legal_research.normalize import normalize_provider_result
from nora_legal_research.provider_contract import ProviderSearchResponseModel
from nora_legal_research.providers import (
    AuthorityResearchRequest,
    ProviderCapabilities,
    ProviderSearchResult,
    require_capability,
)
from nora_legal_research.errors import ProviderContractError


def request() -> AuthorityResearchRequest:
    return AuthorityResearchRequest(
        provider_contract_version=1,
        research_id="R-004",
        jurisdiction="US-WI",
        court_level="state_appellate",
        doctrinal_issue="speedy_trial",
        target_proposition="P-004",
        query_variants=("speedy trial continuance", "adverse speedy trial"),
    )


def test_research_snapshot_round_trip_preserves_provenance_and_adverse_authority() -> None:
    result = ProviderSearchResult(
        provider="COURTLISTENER",
        capabilities=ProviderCapabilities(search=True, opinion_retrieval=True),
        authorities=(
            {
                "id": "A-1",
                "case_name": "Helpful v. State",
                "citation": "2026 WI App 1",
                "court": "Wisconsin Court of Appeals",
                "dateFiled": "2026-01-15",
            },
            {
                "id": "A-2",
                "case_name": "Limiting v. State",
                "citation": "2025 WI App 9",
                "court": "Wisconsin Court of Appeals",
                "dateFiled": "2025-02-10",
                "authority_status": "LIMITING",
                "adverse_relationship": "limits target proposition",
            },
        ),
        limitations=("Currentness is incomplete.",),
    )
    snapshot = normalize_provider_result(request(), result)
    restored = ResearchSnapshot.model_validate_json(snapshot.model_dump_json())
    assert restored.schema_version == "1.0"
    assert len(restored.authorities) == 2
    assert len(restored.adverse_authorities) == 1
    assert restored.provenance[0].provider == "COURTLISTENER"
    assert restored.currentness.status == TreatmentStatus.UNKNOWN
    assert restored.authorities[0].quote_verification == VerificationStatus.NOT_AVAILABLE


def test_provider_capability_negotiation_fails_closed() -> None:
    provider = ProviderSearchResult(provider="fixture", capabilities=ProviderCapabilities(search=True))
    require_capability(type("P", (), {"capabilities": provider.capabilities})(), "search")
    with pytest.raises(Exception) as exc:
        require_capability(type("P", (), {"capabilities": provider.capabilities})(), "citation_graph_inbound")
    assert exc.value.info.code == "UNSUPPORTED_PROVIDER_CAPABILITY"


def test_malformed_provider_record_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProviderSearchResult(
            provider="COURTLISTENER",
            capabilities=ProviderCapabilities(search=True),
            authorities=(None,),  # type: ignore[arg-type]
        )


def test_snapshot_preserves_access_mode_rank_opinion_type_and_query_plan_hash() -> None:
    root = Path(__file__).parents[1]
    response = ProviderSearchResponseModel.model_validate_json(
        (root / "fixtures/provider-contract/response-multi-opinion.json").read_bytes()
    )
    from nora_legal_research.providers import CourtListenerMirrorProvider
    from nora_legal_research.transport import FixtureTransport

    result = CourtListenerMirrorProvider(FixtureTransport(response)).search(request())
    snapshot = normalize_provider_result(request(), result)
    assert snapshot.provider.access_mode == "FIXTURE"
    assert [item.opinion_type.value for item in snapshot.authorities] == ["majority", "dissent"]
    assert len(snapshot.authorities) == 2
    assert snapshot.reproducibility["query_plan_hash"] == snapshot.query_plan.query_plan_hash
    assert snapshot.currentness.checked_at is None
    assert snapshot.confidence == "UNASSESSED"
    assert all(item.quote_verification == VerificationStatus.NOT_AVAILABLE for item in snapshot.authorities)


def test_query_plan_hash_excludes_nondeterministic_time() -> None:
    from nora_legal_research.providers import query_plan_hash

    first = query_plan_hash(request())
    second = query_plan_hash(request())
    assert first == second


def test_provider_retrieval_does_not_promote_binding_or_treatment() -> None:
    result = ProviderSearchResult(
        provider="COURTLISTENER_MIRROR",
        access_mode="FIXTURE",
        research_id="R-004",
        capabilities=ProviderCapabilities(search=True),
        authorities=({
            "provider_record_id": "CL-B-1",
            "case_name": "Provider v. State",
            "citation": "2024 WI App 4",
            "court": "Wisconsin Court of Appeals",
            "decision_date": "2024-01-04",
            "binding_weight": "BINDING",
            "authority_status": "CONTROLLING",
            "opinion_type": "majority",
        },),
    )
    snapshot = normalize_provider_result(request(), result)
    authority = snapshot.authorities[0]
    assert authority.precedential_status == PrecedentialStatus.UNKNOWN
    assert authority.treatment_status == TreatmentStatus.UNKNOWN


@pytest.mark.parametrize(
    ("relationship", "is_adverse"),
    [("SUPPORTING", False), ("UNKNOWN", False), ("ADVERSE", True), ("LIMITING", True)],
)
def test_relationship_requires_explicit_adverse_semantics(relationship: str, is_adverse: bool) -> None:
    result = ProviderSearchResult(
        provider="COURTLISTENER_MIRROR",
        access_mode="FIXTURE",
        research_id="R-004",
        capabilities=ProviderCapabilities(search=True),
        authorities=({
            "provider_record_id": f"CL-{relationship}",
            "case_name": "Relationship v. State",
            "citation": "2024 WI App 5",
            "court": "Wisconsin Court of Appeals",
            "decision_date": "2024-01-05",
            "authority_status": "UNKNOWN",
            "relationship": relationship,
            "opinion_type": "majority",
        },),
    )
    snapshot = normalize_provider_result(request(), result)
    assert bool(snapshot.adverse_authorities) is is_adverse
    assert snapshot.authorities[0].provider_relationship == relationship
    assert (snapshot.authorities[0].adverse_relationship is not None) is is_adverse


def test_provider_and_consumer_snapshot_identities_cannot_be_confused() -> None:
    result = ProviderSearchResult(
        provider="COURTLISTENER_MIRROR",
        access_mode="FIXTURE",
        research_id="R-004",
        capabilities=ProviderCapabilities(search=True),
        provenance={"snapshot_id": "CL-2026-06-30", "snapshot_date": "2026-06-30"},
    )
    snapshot = normalize_provider_result(request(), result)
    assert snapshot.snapshot_id == "RESEARCH-R-004"
    assert snapshot.consumer_snapshot_id == snapshot.snapshot_id
    assert snapshot.provider.snapshot_id == "CL-2026-06-30"
    with pytest.raises(ProviderContractError):
        normalize_provider_result(request(), result, snapshot_id="CL-2026-06-30")
