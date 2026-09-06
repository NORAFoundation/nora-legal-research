from datetime import datetime, timezone

import pytest

from nora_legal_research.contracts import (
    AuthorityRecord,
    ResearchSnapshot,
    TreatmentStatus,
    VerificationStatus,
)
from nora_legal_research.normalize import normalize_provider_result
from nora_legal_research.providers import (
    AuthorityResearchRequest,
    ProviderCapabilities,
    ProviderSearchResult,
    require_capability,
)


def request() -> AuthorityResearchRequest:
    return AuthorityResearchRequest(
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
    with pytest.raises(NotImplementedError):
        require_capability(type("P", (), {"capabilities": provider.capabilities})(), "citation_graph_inbound")


def test_malformed_provider_record_is_rejected() -> None:
    result = ProviderSearchResult(
        provider="COURTLISTENER",
        capabilities=ProviderCapabilities(search=True),
        authorities=(None,),  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError):
        normalize_provider_result(request(), result)
