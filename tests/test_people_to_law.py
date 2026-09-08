"""Tests for People-to-Law ontology and concept mapping invariants."""

import pytest
from pydantic import ValidationError

from nora_legal_research.people_to_law import (
    CANONICAL_CHILD_WELFARE_CONCEPTS,
    PeopleToLawConcept,
    PeopleToLawOntology,
    build_canonical_ontology,
)


def test_canonical_ontology_builds_and_validates():
    ontology = build_canonical_ontology()
    assert len(ontology.concepts) == 25
    ids = [c.concept_id for c in ontology.concepts]
    assert len(ids) == len(set(ids))


def test_retaliation_concept_safety_invariant():
    """Invariant: Retaliation concepts must map to a USER_NOMINATED_* theory, not an established conclusion."""
    ontology = build_canonical_ontology()
    retaliation = ontology.get_concept("P2L-CW-015-RETALIATION")
    assert retaliation is not None
    assert retaliation.user_theory_nomination == "USER_NOMINATED_RETALIATION_THEORY"

    # Attempting to create a retaliation concept without USER_NOMINATED theory must fail
    with pytest.raises(ValidationError, match="Retaliation concepts must designate a USER_NOMINATED_\\* hypothesis"):
        PeopleToLawConcept(
            concept_id="P2L-CW-TEST-RETALIATION",
            preferred_label="Retaliation by worker",
            ordinary_language_aliases=("retaliation",),
            subdomain="CIVIL_RIGHTS_OVERLAY",
            procedure_or_substance="SUBSTANCE",
            candidate_legal_issues=("RETALIATION",),
            procedural_significance="test",
            urgency_cues=("test",),
            factual_predicates=("test",),
            disambiguation_questions=("test",),
            neighboring_concept_ids=(),
            governing_source_families=(),
            false_friend_terms=(),
            user_theory_nomination=None,  # Missing!
        )


def test_narrative_matching_discovers_hypotheses():
    ontology = build_canonical_ontology()

    # Lay phrase matches
    matches1 = ontology.match_narrative("The police and cps took my kids yesterday without any warning.")
    assert any(c.concept_id == "P2L-CW-001-THEY-TOOK-MY-CHILD" for c in matches1)

    matches2 = ontology.match_narrative("The caseworker said they stopped my visits because I was argumentative.")
    assert any(c.concept_id == "P2L-CW-004-STOPPED-VISITS" for c in matches2)

    matches3 = ontology.match_narrative("I was clean and the instant cup drug test is wrong.")
    assert any(c.concept_id == "P2L-CW-011-DRUG-TEST-WRONG" for c in matches3)

    matches4 = ontology.match_narrative("I have texts proving it and the caseworker is making things up.")
    matched_ids = [c.concept_id for c in matches4]
    assert "P2L-CW-023-CASEWORKER-MAKING-THINGS-UP" in matched_ids
    assert "P2L-CW-024-TEXTS-RECORDINGS-PROOF" in matched_ids


def test_all_concepts_have_false_friends_and_disambiguation():
    ontology = build_canonical_ontology()
    for c in ontology.concepts:
        assert len(c.false_friend_terms) > 0, f"Concept {c.concept_id} lacks false friend terms"
        assert len(c.disambiguation_questions) > 0, f"Concept {c.concept_id} lacks disambiguation questions"
        assert len(c.candidate_legal_issues) > 0, f"Concept {c.concept_id} lacks candidate legal issues"
        assert len(c.governing_source_families) > 0, f"Concept {c.concept_id} lacks governing sources"
