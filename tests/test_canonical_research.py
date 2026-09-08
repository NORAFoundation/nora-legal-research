"""Tests for canonical research contracts, state machine transitions, and authority firewall."""

import pytest
from pydantic import ValidationError

from nora_legal_research.canonical_research import (
    AuthorityFirewallClassification,
    AuthorityQualificationLifecycle,
    AuthorityQualificationState,
    CurrentnessReceipt,
    LegalProposition,
    LegalTheory,
    LegalTheoryState,
    MatterScope,
    ProceduralAlert,
    ResearchCoverage,
    ResearchPackage,
    WarGameResult,
)


def test_legal_theory_cannot_leap_from_user_proposed_to_strong():
    """Invariant: User theories are hypotheses, not instant strong conclusions."""
    theory = LegalTheory(
        theory_id="LT-001",
        statement="Social worker retaliated in violation of First Amendment",
        issue_id="RETALIATION",
        state=LegalTheoryState.USER_PROPOSED,
    )

    # Illegal leap to STRONG
    with pytest.raises(ValueError, match="cannot leap directly to STRONG"):
        theory.advance(LegalTheoryState.STRONG)

    # Illegal leap to RELIED_UPON
    with pytest.raises(ValueError, match="cannot leap directly to RELIED_UPON"):
        theory.advance(LegalTheoryState.RELIED_UPON)

    # Valid step-by-step graduation
    t1 = theory.advance(LegalTheoryState.HYPOTHESIS, rationale="Framed as testable issue")
    t2 = t1.advance(LegalTheoryState.RESEARCH_SUPPORTED, evidence_ids=("EVID-1",), rationale="Found 7th Cir. precedent")
    t3 = t2.advance(LegalTheoryState.ADVERSELY_TESTED, evidence_ids=("EVID-ADVERSE-1",), rationale="Found qualified immunity defense")
    t4 = t3.advance(LegalTheoryState.STRONG, rationale="Overcame immunity defense via clearly established timeline")
    t5 = t4.advance(LegalTheoryState.RELIED_UPON, rationale="Formally relied upon in research package")
    assert t5.state == LegalTheoryState.RELIED_UPON
    assert len(t5.supporting_evidence_ids) >= 1
    assert len(t5.adverse_testing_ids) >= 1


def test_authority_qualification_state_machine_and_firewall():
    """Invariant: Sequential qualification and firewall isolation."""
    # 1. Firewall: USER_EVIDENCE cannot be RELIED_UPON as controlling authority
    user_evidence_auth = AuthorityQualificationLifecycle(
        authority_id="AUTH-PRIVATE-LOG",
        citation_text="Parent Personal Visitation Log",
        classification=AuthorityFirewallClassification.USER_EVIDENCE,
        state=AuthorityQualificationState.DISCOVERED,
    )
    with pytest.raises(ValueError, match="Firewall violation: USER_EVIDENCE cannot be RELIED_UPON"):
        AuthorityQualificationLifecycle(
            authority_id="AUTH-PRIVATE-LOG",
            citation_text="Parent Personal Visitation Log",
            classification=AuthorityFirewallClassification.USER_EVIDENCE,
            state=AuthorityQualificationState.RELIED_UPON,
            pinpoint_passage="Page 4 entry",
            currentness_checked=True,
        )

    # 2. Sequential graduation of primary authority
    auth = AuthorityQualificationLifecycle(
        authority_id="AUTH-SANTOSKY",
        citation_text="455 U.S. 745",
        classification=AuthorityFirewallClassification.PRIMARY_AUTHORITY,
        state=AuthorityQualificationState.DISCOVERED,
    )

    # Cannot skip steps (e.g. DISCOVERED -> RELIED_UPON)
    with pytest.raises(ValueError, match="Illegal authority lifecycle transition from DISCOVERED to RELIED_UPON"):
        auth.advance(AuthorityQualificationState.RELIED_UPON)

    # Walk through proper lifecycle
    c1 = auth.advance(AuthorityQualificationState.CANDIDATE)
    c2 = c1.advance(AuthorityQualificationState.IDENTITY_VERIFIED)
    c3 = c2.advance(AuthorityQualificationState.JURISDICTION_QUALIFIED)
    c4 = c3.advance(AuthorityQualificationState.HIERARCHY_QUALIFIED)
    c5 = c4.advance(AuthorityQualificationState.PASSAGE_VERIFIED, pinpoint_passage="455 U.S. at 753: 'clear and convincing evidence'")
    c6 = c5.advance(AuthorityQualificationState.CURRENTNESS_CHECKED, currentness_checked=True)
    c7 = c6.advance(AuthorityQualificationState.TREATMENT_ASSESSED, negative_treatment="Followed consistently")
    c8 = c7.advance(AuthorityQualificationState.RELIED_UPON)
    assert c8.state == AuthorityQualificationState.RELIED_UPON


def test_authority_cannot_be_relied_upon_if_overruled():
    """Invariant: Overruled authority cannot be relied upon."""
    with pytest.raises(ValueError, match="Overruled authority cannot be RELIED_UPON"):
        AuthorityQualificationLifecycle(
            authority_id="AUTH-OLD-CASE",
            citation_text="100 Wis. 2d 1",
            classification=AuthorityFirewallClassification.PRIMARY_AUTHORITY,
            state=AuthorityQualificationState.RELIED_UPON,
            pinpoint_passage="Quote on page 5",
            currentness_checked=True,
            negative_treatment="Overruled by Supreme Court",
        )


def test_proposition_requires_supporting_passage():
    """Invariant: A real citation alone does not prove a proposition without supporting passage."""
    with pytest.raises(ValueError, match="at least one supporting passage is required"):
        LegalProposition(
            proposition_id="PROP-001",
            exact_proposition="Due process requires clear and convincing evidence before terminating parental rights",
            supporting_authorities=("455 U.S. 745",),
            supporting_passages=(),  # Missing!
        )


def test_research_coverage_dimensional_not_win_probability():
    """Invariant: Coverage is dimensional, and completeness requires adverse research."""
    coverage = ResearchCoverage(
        jurisdiction=1.0,
        governing_text=1.0,
        controlling_authority=1.0,
        fact_analogies=0.8,
        procedure=1.0,
        adverse_research=0.1,  # Inadequate adverse research!
        local_rules=0.5,
        currentness=1.0,
        treatment=1.0,
        quote_verification=1.0,
        evidence_application=0.8,
    )
    assert not coverage.is_complete_research()

    # Now with adequate adverse research
    complete_coverage = ResearchCoverage(
        jurisdiction=1.0,
        governing_text=1.0,
        controlling_authority=1.0,
        fact_analogies=0.8,
        procedure=1.0,
        adverse_research=0.8,
        local_rules=0.5,
        currentness=1.0,
        treatment=1.0,
        quote_verification=1.0,
        evidence_application=0.8,
    )
    assert complete_coverage.is_complete_research()


def test_wargame_result_requires_opposition_analysis():
    """Invariant: War Game cannot be one-sided critique theater."""
    with pytest.raises(ValidationError, match="WarGameResult must assess opposition arguments"):
        WarGameResult(
            wargame_id="WG-001",
            target_objective="Reunification motion",
            advocate_arguments=("Parent completed parenting class",),
            opposition_arguments=(),  # One-sided!
            conflicts=(),
            rebuttals=(),
        )


def test_matter_scope_prevents_cross_matter_contamination():
    """Invariant: Separate matters cannot be merged."""
    scope_a = MatterScope(user_scope_id="U-1", matter_scope_id="M-101", source_scope_id="S-1")
    scope_b = MatterScope(user_scope_id="U-1", matter_scope_id="M-102", source_scope_id="S-2")
    with pytest.raises(ValueError, match="Cross-matter contamination detected"):
        scope_a.assert_same_matter(scope_b)


def test_research_package_creation():
    scope = MatterScope(user_scope_id="U-1", matter_scope_id="M-101", source_scope_id="S-1")
    receipt = CurrentnessReceipt(
        receipt_id="CR-001",
        checked_through_date="2026-09-08",
        sources_checked=("Wisconsin Supreme Court slip feed", "CourtListener mirror"),
    )
    wargame = WarGameResult(
        wargame_id="WG-001",
        target_objective="Challenge emergency removal",
        advocate_arguments=("No imminent harm existed at time of warrantless removal",),
        opposition_arguments=("Agency argues parent was non-responsive to safety assessment",),
        conflicts=("Whether lack of communication constituted imminent physical threat",),
        rebuttals=("Parent was at work during caseworker unannounced drop-in",),
    )
    coverage = ResearchCoverage(
        jurisdiction=1.0,
        governing_text=1.0,
        controlling_authority=1.0,
        fact_analogies=0.9,
        procedure=1.0,
        adverse_research=0.8,
        local_rules=0.7,
        currentness=1.0,
        treatment=1.0,
        quote_verification=1.0,
        evidence_application=0.9,
    )
    prop = LegalProposition(
        proposition_id="PROP-001",
        exact_proposition="Warrantless removal of child requires exigent circumstances showing imminent bodily danger.",
        supporting_authorities=("Wis. Stat. § 48.19",),
        supporting_passages=("Wis. Stat. § 48.19(1)(d): showing of immediate danger to health or safety required.",),
    )

    pkg = ResearchPackage(
        package_id="PKG-001",
        matter_scope=scope,
        question_or_objective="Warrantless removal defense",
        jurisdiction_and_posture="US-WI Circuit Court CHIPS temporary custody",
        verified_propositions=(prop,),
        relied_upon_authorities=("Wis. Stat. § 48.19",),
        adverse_authorities=("State v. P.G., 200 Wis. 2d 100",),
        currentness_receipt=receipt,
        wargame_result=wargame,
        coverage=coverage,
        provenance=("Canonical research run",),
    )
    assert pkg.package_id == "PKG-001"
