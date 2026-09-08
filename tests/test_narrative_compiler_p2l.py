"""Tests for People-to-Law and JurisdictionSourceRegistry integration into Narrative Compiler.

Verifies:
- Dual / multi-channel issue discovery (General mappings + P2L candidate hypotheses)
- Epistemic discipline (candidate hypothesis confidence 0.5, status ISSUE_HYPOTHESIS)
- Urgency cues and procedural triage derived from structured concept metadata (subdomain/cues)
- Preserved epistemic boundary for user-nominated retaliation theories
- Bounded jurisdiction source-registry integration preserving official_status, authority_level, currentness_capability
- Circuit-specific federal overlay bounding:
    WI + federal -> nationwide federal + Seventh Circuit (NO Eighth Circuit)
    MN + federal -> nationwide federal + Eighth Circuit (NO Seventh Circuit)
- Invariance under source ID renaming (metadata-driven resolution, not string-coupled)
- Negative control narratives that do not falsely trigger child-welfare concepts
"""

from __future__ import annotations

import pytest

from nora_legal_research.jurisdiction_data import build_canonical_registry
from nora_legal_research.jurisdiction_registry import (
    AuthorityFamily,
    AuthorityLevel,
    CurrentnessCapability,
    GeographicScope,
    JurisdictionSourceRegistry,
    OfficialStatus,
)
from nora_legal_research.narrative_compiler import (
    EvidenceCategory,
    IssueStatus,
    ResolutionState,
    compile_narrative,
)
from nora_legal_research.people_to_law import PEOPLE_TO_LAW_CONTRACT


def test_p2l_child_welfare_intake_populates_candidate_hypotheses_and_urgency() -> None:
    narrative = (
        "In Wisconsin, the social worker took my baby yesterday. "
        "They won't tell me what i have to do to get my child back."
    )
    compiled = compile_narrative(narrative)

    issue_ids = {issue.issue_id for issue in compiled.intent.issue_hypotheses}
    assert "p2l_cw_001_they_took_my_child" in issue_ids
    assert "p2l_cw_002_wont_tell_what_to_do" in issue_ids

    # Epistemic discipline check: candidate status and bounded confidence
    for issue in compiled.intent.issue_hypotheses:
        if issue.issue_id.startswith("p2l_"):
            assert issue.status == IssueStatus.ISSUE_HYPOTHESIS
            assert issue.confidence == 0.5
            assert issue.ontology_source == PEOPLE_TO_LAW_CONTRACT

    # Urgency cues derived from structured concept metadata
    urgency = set(compiled.intent.urgency_flags)
    assert "custody_removal_possible" in urgency
    assert "recent_removal" in urgency
    assert "hours_to_statutory_hearing" in urgency

    # Disambiguation questions present in clarifications_needed
    clarification_texts = [c.question for c in compiled.intent.clarifications_needed]
    assert any("prior signed court order" in q or "warrant" in q for q in clarification_texts)


def test_retaliation_theory_nomination_preserves_epistemic_boundary() -> None:
    narrative = (
        "I live in Wisconsin. Social worker punished me for speaking up and "
        "they retaliated after i complained to the state board."
    )
    compiled = compile_narrative(narrative)

    retaliation_issues = [i for i in compiled.intent.issue_hypotheses if "retaliation" in i.issue_id]
    assert retaliation_issues, "Expected retaliation hypothesis from P2L concept"
    retaliation = retaliation_issues[0]

    # Must remain an unverified hypothesis, not an established conclusion
    assert retaliation.status == IssueStatus.ISSUE_HYPOTHESIS
    assert retaliation.confidence == 0.5
    assert any("USER_NOMINATED_RETALIATION_THEORY" in term for term in retaliation.legal_terms)


def test_dual_discovery_handles_mixed_lay_and_p2l_issues() -> None:
    narrative = (
        "My landlord changed the locks on my apartment, and social worker took my baby. "
        "I need help."
    )
    compiled = compile_narrative(narrative)

    issue_ids = {issue.issue_id for issue in compiled.intent.issue_hypotheses}
    # General lay mapping: self_help_lockout
    assert "self_help_lockout" in issue_ids
    # P2L lived problem: p2l_cw_001_they_took_my_child
    assert "p2l_cw_001_they_took_my_child" in issue_ids

    # Both issues generate query sets in research plan
    plan_issues = {q.issue_id for q in compiled.plan.queries}
    assert "self_help_lockout" in plan_issues
    assert "p2l_cw_001_they_took_my_child" in plan_issues


def test_bounded_jurisdiction_source_registry_integration_state_separation() -> None:
    # 1. Wisconsin state matter -> WI sources only
    wi_narrative = "In Wisconsin, social worker took my baby without warning."
    compiled_wi = compile_narrative(wi_narrative)

    assert compiled_wi.intent.jurisdiction_state.value == "US-WI"
    wi_source_ids = {s.source_id for s in compiled_wi.intent.potential_governing_sources}
    assert "US-WI-STATUTES-CH48" in wi_source_ids
    assert "US-WI-CONST" in wi_source_ids
    assert "US-MN-STATUTES-260C" not in wi_source_ids
    assert "US-FED-CONST" not in wi_source_ids

    # Preserves metadata dimensions separately
    wi_stat = next(s for s in compiled_wi.intent.potential_governing_sources if s.source_id == "US-WI-STATUTES-CH48")
    assert wi_stat.status == ResolutionState.INFERRED
    assert wi_stat.source_kind == "statute"
    assert wi_stat.authority_level == "PRIMARY_CONTROLLING"
    assert wi_stat.official_status == "OFFICIAL"
    assert wi_stat.currentness_capability == "OFFICIAL_BULLETIN"

    wi_forms = next(s for s in compiled_wi.intent.potential_governing_sources if s.source_id == "US-WI-FORMS-JUVENILE")
    assert wi_forms.status == ResolutionState.INFERRED
    assert wi_forms.source_kind == "forms_guidance"
    assert wi_forms.authority_level == "PROCESS"

    # 2. Minnesota state matter -> MN sources only
    mn_narrative = "In Minnesota, the child welfare agency filed a petition regarding custody."
    compiled_mn = compile_narrative(mn_narrative)

    assert compiled_mn.intent.jurisdiction_state.value == "US-MN"
    mn_source_ids = {s.source_id for s in compiled_mn.intent.potential_governing_sources}
    assert "US-MN-STATUTES-CH260C" in mn_source_ids
    assert "US-MN-CONST" in mn_source_ids
    assert "US-WI-STATUTES-CH48" not in mn_source_ids
    assert "US-FED-CONST" not in mn_source_ids


def test_circuit_specific_federal_overlay_bounding() -> None:
    # Case A: WI + federal civil-rights issue -> nationwide federal + Seventh Circuit (NO Eighth Circuit)
    wi_fed = compile_narrative(
        "In Wisconsin, the county took my daughter and I want to bring a Section 1983 civil rights lawsuit."
    )
    wi_fed_sources = {s.source_id for s in wi_fed.intent.potential_governing_sources}
    assert "US-FED-CONST" in wi_fed_sources
    assert "US-FED-USC-CIVIL-RIGHTS-CHILD-WELFARE" in wi_fed_sources
    assert "US-FED-CA7-OFFICIAL" in wi_fed_sources
    assert "US-FED-CA8-OFFICIAL" not in wi_fed_sources

    # Case B: MN + federal civil-rights issue -> nationwide federal + Eighth Circuit (NO Seventh Circuit)
    mn_fed = compile_narrative(
        "In Minnesota, the county took my daughter and I want to bring a Section 1983 civil rights lawsuit."
    )
    mn_fed_sources = {s.source_id for s in mn_fed.intent.potential_governing_sources}
    assert "US-FED-CONST" in mn_fed_sources
    assert "US-FED-USC-CIVIL-RIGHTS-CHILD-WELFARE" in mn_fed_sources
    assert "US-FED-CA8-OFFICIAL" in mn_fed_sources
    assert "US-FED-CA7-OFFICIAL" not in mn_fed_sources


def test_source_selection_works_when_source_ids_are_renamed() -> None:
    """Proves that source resolution operates strictly on structured metadata (jurisdiction, geographic_scope),
    NOT on source_id string naming conventions.
    """
    canonical_reg = build_canonical_registry()
    renamed_sources = []
    for idx, s in enumerate(canonical_reg.sources, start=1):
        renamed_sources.append(s.model_copy(update={"source_id": f"OPAQUE-SRC-{idx:04d}"}))

    synthetic_reg = JurisdictionSourceRegistry(
        registry_id="synthetic-opaque-registry-v1",
        sources=tuple(renamed_sources),
    )

    # Resolve for Wisconsin with federal overlay using synthetic opaque registry
    resolved_wi_fed = synthetic_reg.resolve_candidate_sources("US-WI", include_federal_overlay=True)

    # Verify structured scopes
    wi_count = sum(1 for s in resolved_wi_fed if s.jurisdiction == "US-WI")
    nat_count = sum(1 for s in resolved_wi_fed if s.geographic_scope == GeographicScope.NATIONAL)
    ca7_count = sum(1 for s in resolved_wi_fed if s.geographic_scope == GeographicScope.CIRCUIT_7)
    ca8_count = sum(1 for s in resolved_wi_fed if s.geographic_scope == GeographicScope.CIRCUIT_8)

    assert wi_count == 9
    assert nat_count == 8
    assert ca7_count == 1
    assert ca8_count == 0, "Eighth Circuit must be excluded for Wisconsin even with opaque source IDs"


def test_negative_control_narrative_does_not_falsely_trigger_child_welfare() -> None:
    narrative = (
        "In Wisconsin, I signed a contract to lease farm equipment. "
        "The vendor was two months late delivering the tractor."
    )
    compiled = compile_narrative(narrative)

    p2l_issues = [i for i in compiled.intent.issue_hypotheses if i.issue_id.startswith("p2l_")]
    assert len(p2l_issues) == 0, f"Unexpected P2L matches on commercial lease narrative: {p2l_issues}"
