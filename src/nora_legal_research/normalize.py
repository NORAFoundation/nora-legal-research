from __future__ import annotations

from datetime import datetime, timezone

from .contracts import (
    AuthorityRecord,
    CurrentnessAssessment,
    Jurisdiction,
    ProviderMetadata,
    Provenance,
    QueryPlanReference,
    ResearchSnapshot,
    TreatmentStatus,
)
from .courtlistener import CourtListenerNormalizer
from .providers import AuthorityResearchRequest, ProviderSearchResult


def normalize_provider_result(
    request: AuthorityResearchRequest,
    result: ProviderSearchResult,
    *,
    snapshot_id: str | None = None,
) -> ResearchSnapshot:
    """Normalize provider records without asserting treatment or legal effect."""
    normalizer = CourtListenerNormalizer() if result.provider in {"COURTLISTENER", "COURTLISTENER_MIRROR"} else None
    authorities: list[AuthorityRecord] = []
    adverse: list[AuthorityRecord] = []
    for index, payload in enumerate(result.authorities):
        if not isinstance(payload, dict):
            raise ValueError("provider authority record must be an object")
        if normalizer is not None:
            record = normalizer.normalize_authority(payload, provider_record_id=str(payload.get("id", index)))
        else:
            record = AuthorityRecord.model_validate(payload)
        authorities.append(record)
        status = str(payload.get("authority_status", "")).upper()
        if status in {"ADVERSE", "LIMITING"} or record.adverse_relationship:
            adverse.append(record)
    now = datetime.now(timezone.utc)
    return ResearchSnapshot(
        schema_version="1.0",
        snapshot_id=snapshot_id or request.research_id,
        research_id=request.research_id,
        query=" OR ".join(request.query_variants),
        jurisdiction=Jurisdiction(code=request.jurisdiction, level=request.court_level, name=request.jurisdiction),
        court_hierarchy_scope=request.court_level,
        doctrinal_issue=request.doctrinal_issue,
        target_proposition=request.target_proposition,
        query_plan=QueryPlanReference(query_id=request.research_id, variants=list(request.query_variants)),
        authorities=authorities,
        adverse_authorities=adverse,
        provider=ProviderMetadata(
            provider_name=result.provider,
            access_mode=result.provider,
            capabilities_used=[name for name, enabled in vars(result.capabilities).items() if enabled is True],
            capabilities_unavailable=list(result.capabilities.unsupported),
            snapshot_id=str(result.provenance.get("snapshot_id")) if result.provenance.get("snapshot_id") else None,
            snapshot_date=str(result.provenance.get("snapshot_date")) if result.provenance.get("snapshot_date") else None,
            service_version=str(result.provenance.get("service_version")) if result.provenance.get("service_version") else None,
        ),
        currentness=CurrentnessAssessment(status=TreatmentStatus.UNKNOWN, checked_at=now),
        unresolved_treatment_questions=["Treatment and currentness require separate verification."],
        limitations=list(result.limitations),
        provenance=[Provenance(
            provider=result.provider,
            source_kind="public_authority_provider",
            source_record_id=str(result.provenance.get("snapshot_id")) if result.provenance.get("snapshot_id") else None,
            retrieved_at=now,
            limitations=list(result.limitations),
        )],
        checked_at=now,
        confidence="UNASSESSED",
        reproducibility={"provider": result.provider, "research_id": request.research_id},
    )
