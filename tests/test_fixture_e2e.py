from __future__ import annotations

import json
from pathlib import Path

from nora_legal_research.contracts import RetrievalStatus, TreatmentStatus, VerificationStatus
from nora_legal_research.normalize import normalize_provider_result
from nora_legal_research.provider_contract import AuthorityResearchRequest, ProviderSearchResponseModel
from nora_legal_research.providers import CourtListenerMirrorProvider
from nora_legal_research.transport import FixtureTransport


ROOT = Path(__file__).parents[1]


def test_generic_fixture_request_to_research_snapshot_e2e() -> None:
    request = AuthorityResearchRequest.model_validate_json(
        (ROOT / "fixtures/provider-contract/request-basic.json").read_bytes()
    )
    response = ProviderSearchResponseModel.model_validate_json(
        (ROOT / "fixtures/provider-contract/response-supporting.json").read_bytes()
    )
    result = CourtListenerMirrorProvider(FixtureTransport(response)).search(request)
    snapshot = normalize_provider_result(request, result)
    serialized = snapshot.model_dump(mode="json")

    assert snapshot.research_id == "R-004"
    assert snapshot.jurisdiction.code == "US-WI"
    assert snapshot.retrieval_status == RetrievalStatus.COMPLETE
    assert snapshot.provider.provider_name == "COURTLISTENER_MIRROR"
    assert snapshot.provider.access_mode == "FIXTURE"
    assert snapshot.provider.snapshot_id == "CL-2026-06-30"
    assert snapshot.currentness.status == TreatmentStatus.UNKNOWN
    assert snapshot.authorities[0].quote_verification == VerificationStatus.NOT_AVAILABLE
    assert snapshot.authorities[0].provider_record_id == "CL-A-1"
    assert "raw" not in json.dumps(serialized)
    assert "/Users/" not in json.dumps(serialized)
