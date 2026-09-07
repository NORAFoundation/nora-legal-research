from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .contracts import (
    AuthorityRecord,
    CurrentnessAssessment,
    Jurisdiction,
    OpinionType,
    ProviderMetadata,
    Provenance,
    QueryPlanReference,
    ResearchSnapshot,
    TreatmentStatus,
    VerificationStatus,
)
from .courtlistener import CourtListenerNormalizer
from .errors import ProviderContractError, ProviderPartialResult
from .provider_contract import COURTLISTENER_MIRROR, ProviderAuthorityCandidate
from .providers import AuthorityResearchRequest, ProviderSearchResult, query_plan_hash


EXPLICIT_ADVERSE_RELATIONSHIPS = {
    "ADVERSE",
    "LIMITING",
    "DISTINGUISHING",
    "NEGATIVE_TREATMENT",
}


def normalize_provider_result(
    request: AuthorityResearchRequest,
    result: ProviderSearchResult,
    *,
    snapshot_id: str | None = None,
    allow_partial: bool = False,
) -> ResearchSnapshot:
    """Normalize a validated provider result without asserting legal effect."""

    request = AuthorityResearchRequest.model_validate(request)
    result = ProviderSearchResult.model_validate(result)
    if result.research_id is not None and result.research_id != request.research_id:
        raise ProviderContractError("provider research_id does not match request")
    if result.partial or result.truncated:
        if not allow_partial:
            raise ProviderPartialResult("provider reported a partial or truncated result", access_mode=result.access_mode)

    stable_query_hash = query_plan_hash(request)
    provider_query_hash = result.provenance.get("query_plan_hash")
    if provider_query_hash is not None and provider_query_hash != stable_query_hash:
        raise ProviderContractError("provider query-plan identity does not match request")

    authorities: list[AuthorityRecord] = []
    adverse: list[AuthorityRecord] = []
    seen: set[tuple[str, ...]] = set()
    normalizer = CourtListenerNormalizer() if result.provider in {"COURTLISTENER", COURTLISTENER_MIRROR} else None
    for index, payload in enumerate(result.authorities):
        if not isinstance(payload, Mapping):
            raise ProviderContractError("provider authority record must be an object")
        record = _normalize_authority(
            request,
            result,
            payload,
            index=index,
            normalizer=normalizer,
        )
        identity = _authority_identity(record, payload, index=index)
        if identity in seen:
            continue
        seen.add(identity)
        authorities.append(record)
        if _is_explicitly_adverse(payload, record):
            adverse.append(record)

    provider_snapshot_id = result.provenance.get("snapshot_id")
    if snapshot_id and provider_snapshot_id and snapshot_id == provider_snapshot_id:
        raise ProviderContractError("consumer snapshot_id must not reuse provider snapshot identity")
    effective_snapshot_id = snapshot_id or f"RESEARCH-{request.research_id}"
    limitations = list(result.limitations)
    warnings = [
        "Retrieval does not establish currentness, treatment, binding effect, or good law.",
        "Quote verification is not available from provider retrieval alone.",
    ]
    if result.retrieval_status.value == "empty":
        warnings.append("Completed retrieval returned zero authorities; this is not a no-law conclusion.")
    if result.partial or result.truncated:
        warnings.append("Provider result is partial or truncated and is not complete retrieval evidence.")
    if provider_snapshot_id is None:
        limitations.append("Provider snapshot identity was not supplied; reproducibility is reduced.")
        warnings.append("Consumer snapshot identity is a correlation identifier, not a provider snapshot claim.")
    if result.provenance.get("mirror_git_sha") is None:
        limitations.append("Mirror Git SHA was not supplied; provider build reproducibility is reduced.")
    if provider_query_hash is None:
        limitations.append("Provider did not attest the query-plan hash; consumer hash is retained for replay.")

    provider_retrieved_at = _parse_datetime(result.provenance.get("retrieved_at"))
    provenance = Provenance(
        provider=result.provider,
        source_kind="public_authority_provider",
        source_record_id=str(provider_snapshot_id) if provider_snapshot_id else None,
        retrieved_at=provider_retrieved_at,
        snapshot_id=str(provider_snapshot_id) if provider_snapshot_id else None,
        snapshot_date=_optional_text(result.provenance.get("snapshot_date")),
        service_version=_optional_text(result.provenance.get("service_version")),
        mirror_git_sha=_optional_text(result.provenance.get("mirror_git_sha")),
        provider_contract_version=result.provenance.get("provider_contract_version"),
        query_plan_hash=provider_query_hash,
        limitations=limitations,
    )
    plan = QueryPlanReference(
        query_id=request.research_id,
        variants=list(request.query_variants),
        jurisdiction=request.jurisdiction,
        court_level=request.court_level,
        date_range=request.date_range,
        date_from=request.date_from,
        date_to=request.date_to,
        limit=request.limit,
        capabilities_requested=list(request.requested_capabilities),
        query_plan_hash=stable_query_hash,
        filters={"date_range": request.date_range},
    )
    return ResearchSnapshot(
        schema_version="1.0",
        snapshot_id=effective_snapshot_id,
        consumer_snapshot_id=effective_snapshot_id,
        research_id=request.research_id,
        query=" OR ".join(request.query_variants) or request.doctrinal_issue,
        jurisdiction=Jurisdiction(code=request.jurisdiction, level=request.court_level, name=request.jurisdiction),
        court_hierarchy_scope=request.court_level,
        doctrinal_issue=request.doctrinal_issue,
        target_proposition=request.target_proposition,
        query_plan=plan,
        authorities=authorities,
        adverse_authorities=adverse,
        provider=ProviderMetadata(
            provider_name=result.provider,
            access_mode=result.access_mode,
            capabilities_used=[name for name, enabled in result.capabilities.model_dump().items() if enabled is True],
            capabilities_unavailable=list(result.capabilities.unsupported),
            snapshot_id=str(provider_snapshot_id) if provider_snapshot_id else None,
            snapshot_date=_optional_text(result.provenance.get("snapshot_date")),
            service_version=_optional_text(result.provenance.get("service_version")),
            mirror_git_sha=_optional_text(result.provenance.get("mirror_git_sha")),
            provider_contract_version=result.provider_contract_version,
            query_plan_hash=stable_query_hash,
        ),
        retrieval_status=result.retrieval_status,
        currentness=CurrentnessAssessment(status=TreatmentStatus.UNKNOWN),
        unresolved_treatment_questions=["Treatment and currentness require separate verification."],
        missing_verification=["currentness", "treatment", "quote_verification"],
        limitations=limitations,
        status_warnings=warnings,
        provenance=[provenance],
        confidence="UNASSESSED",
        reproducibility={
            "query_plan_hash": stable_query_hash,
            "query_plan": plan.model_dump(mode="json"),
            "provider_snapshot_id": provider_snapshot_id,
            "provider_query_plan_hash": provider_query_hash,
            "mirror_git_sha": result.provenance.get("mirror_git_sha"),
        },
    )


def _normalize_authority(
    request: AuthorityResearchRequest,
    result: ProviderSearchResult,
    payload: Mapping[str, Any],
    *,
    index: int,
    normalizer: CourtListenerNormalizer | None,
) -> AuthorityRecord:
    if result.provider == COURTLISTENER_MIRROR:
        candidate = ProviderAuthorityCandidate.model_validate(payload)
        opinion_type = candidate.opinion_type
        relationship = candidate.relationship
        limitations = ["Provider retrieval does not establish treatment or currentness."]
        if opinion_type != OpinionType.MAJORITY:
            limitations.append(f"Provider supplied opinion type {opinion_type.value}; do not treat it as a majority holding.")
        return AuthorityRecord(
            citation_text=f"{candidate.case_name}, {candidate.citation}",
            jurisdiction_code=request.jurisdiction,
            normalized_cite=candidate.citation,
            authority_id=candidate.provider_record_id,
            case_name=candidate.case_name,
            court=candidate.court,
            decision_date=candidate.decision_date,
            exact_proposition=candidate.exact_proposition,
            provider_relationship=relationship,
            adverse_relationship=relationship if _candidate_is_adverse(candidate) else None,
            opinion_type=opinion_type,
            provider=result.provider,
            provider_record_id=candidate.provider_record_id,
            provider_cluster_id=candidate.provider_cluster_id,
            opinion_id=candidate.opinion_id,
            provider_rank=candidate.provider_rank,
            quote_verification=VerificationStatus.NOT_AVAILABLE,
            treatment_status=TreatmentStatus.UNKNOWN,
            retrieved_at=_parse_datetime(result.provenance.get("retrieved_at")),
            limitations=limitations,
        )
    if normalizer is not None:
        return normalizer.normalize_authority(payload, provider_record_id=str(payload.get("id", index)))
    return AuthorityRecord.model_validate(payload)


def _candidate_is_adverse(candidate: ProviderAuthorityCandidate) -> bool:
    return (
        candidate.authority_status.upper() in EXPLICIT_ADVERSE_RELATIONSHIPS
        or (candidate.relationship or "").upper() in EXPLICIT_ADVERSE_RELATIONSHIPS
    )


def _is_explicitly_adverse(payload: Mapping[str, Any], record: AuthorityRecord) -> bool:
    status = str(payload.get("authority_status", "")).upper()
    relationship = str(payload.get("relationship", "")).upper()
    return status in EXPLICIT_ADVERSE_RELATIONSHIPS or relationship in EXPLICIT_ADVERSE_RELATIONSHIPS


def _authority_identity(record: AuthorityRecord, payload: Mapping[str, Any], *, index: int) -> tuple[str, ...]:
    if record.provider_record_id:
        return ("provider_record_id", record.provider or "", record.provider_record_id)
    if record.provider_cluster_id and record.opinion_id:
        return ("cluster_opinion", record.provider_cluster_id, record.opinion_id, record.opinion_type.value)
    if record.opinion_id:
        return ("opinion", record.opinion_id, record.opinion_type.value)
    if record.normalized_cite:
        return (
            "conservative_citation",
            record.normalized_cite,
            record.case_name or "",
            record.court or "",
            record.decision_date or "",
            record.opinion_type.value,
        )
    return ("position", str(index))


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProviderContractError("provider retrieved_at is invalid") from exc
    raise ProviderContractError("provider retrieved_at is invalid")


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) else None
