"""Tests for People-to-Law and JurisdictionSourceRegistry integration into Narrative Compiler.

Verifies:
- Dual / multi-channel issue discovery (General mappings + P2L candidate hypotheses)
- Epistemic discipline (candidate hypothesis confidence 0.5, status ISSUE_HYPOTHESIS)
- Preserved epistemic boundary for user-nominated retaliation theories
- Disambiguation questions and urgency cues propagation
- Bounded jurisdiction source-registry integration (primary vs explanatory distinction)
- Circuit-specific federal overlay bounding
- Negative control narratives that do not falsely trigger child-welfare concepts
"""

from __future__ import annotations

import pytest

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

    # Urgency cues from matched concepts
    urgency = set(compiled.intent.urgency_flags)
    assert "custody_removal_possible" in urgency
    assert any("hearing" in flag or "removal" in flag for flag in urgency)

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


def test_bounded_jurisdiction_source_registry_integration() -> None:
    # Wisconsin narrative without federal claims
    wi_narrative = "In Wisconsin, social worker took my baby without warning."
    compiled_wi = compile_narrative(wi_narrative)

    assert compiled_wi.intent.jurisdiction_state.value == "US-WI"
    source_ids = {s.source_id for s in compiled_wi.intent.potential_governing_sources}

    # Wisconsin state sources present
    assert "US-WI-STATUTES-CH48" in source_ids
    assert "US-WI-CONST" in source_ids

    # Primary vs explanatory distinction verified
    wi_stat_source = next(s for s in compiled_wi.intent.potential_governing_sources if s.source_id == "US-WI-STATUTES-CH48")
    assert wi_stat_source.source_kind == "primary_authority"
    assert wi_stat_source.status == ResolutionState.INFERRED

    wi_form_source = next(s for s in compiled_wi.intent.potential_governing_sources if s.source_id == "US-WI-FORMS-JUVENILE")
    assert wi_form_source.source_kind == "explanatory_process"
    assert wi_form_source.status == ResolutionState.INFERRED

    # Federal sources NOT included when no federal claims exist
    assert "US-FED-CONST" not in source_ids


def test_federal_overlay_bounded_to_relevant_circuit_when_federal_claims_present() -> None:
    # Wisconsin narrative with Section 1983 / federal civil rights claim
    wi_fed_narrative = (
        "In Wisconsin, the county took my daughter and I want to bring a Section 1983 civil rights lawsuit."
    )
    compiled = compile_narrative(wi_fed_narrative)

    source_ids = {s.source_id for s in compiled.intent.potential_governing_sources}
    assert "US-FED-CONST" in source_ids
    assert "US-FED-USC-CIVIL-RIGHTS-CHILD-WELFARE" in source_ids

    # 7th Circuit (governing WI) included; 8th Circuit (governing MN) excluded
    assert "US-FED-CA7-OFFICIAL" in source_ids
    assert "US-FED-CA8-OFFICIAL" not in source_ids


def test_negative_control_narrative_does_not_falsely_trigger_child_welfare() -> None:
    narrative = (
        "In Wisconsin, I signed a contract to lease farm equipment. "
        "The vendor was two months late delivering the tractor."
    )
    compiled = compile_narrative(narrative)

    p2l_issues = [i for i in compiled.intent.issue_hypotheses if i.issue_id.startswith("p2l_")]
    assert len(p2l_issues) == 0, f"Unexpected P2L matches on commercial lease narrative: {p2l_issues}"
