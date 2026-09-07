from __future__ import annotations

import json
from pathlib import Path

import pytest

from nora_legal_research.narrative_compiler import (
    EvidenceCategory,
    IssueStatus,
    QualityGateStatus,
    QueryClass,
    ResolutionState,
    compile_narrative,
    extract_narrative_intake,
)


ROOT = Path(__file__).parents[1]


def fixture(name: str) -> str:
    return json.loads((ROOT / "fixtures/research-quality" / name).read_text())["narrative"]


def test_unknown_jurisdiction_requires_high_value_clarification_and_does_not_guess_state() -> None:
    compiled = compile_narrative(fixture("unknown-jurisdiction.json"))

    assert compiled.intent.jurisdiction_state.state == ResolutionState.UNKNOWN
    assert compiled.intent.jurisdiction_state.value is None
    assert compiled.intent.clarifications_needed[0].question == "Which state is the case in?"
    assert any(issue.issue_id == "self_help_lockout" for issue in compiled.intent.issue_hypotheses)
    assert compiled.provider_requests() == ()


def test_wrong_legal_label_becomes_interpretation_and_candidate_issues() -> None:
    compiled = compile_narrative(fixture("wrong-legal-label.json"))
    issue_ids = {issue.issue_id for issue in compiled.intent.issue_hypotheses}

    assert compiled.intake.user_interpretations
    assert "HIPAA" in compiled.intake.user_interpretations[0]
    assert {"health_information_evidence", "due_process"}.issubset(issue_ids)
    assert all(issue.status in {IssueStatus.ISSUE_HYPOTHESIS, IssueStatus.UNRESOLVED_ISSUE} for issue in compiled.intent.issue_hypotheses)
    assert all("HIPAA" not in query_text for query in compiled.plan.queries for query_text in query.query_variants)


def test_buried_procedural_fact_is_recovered_and_date_is_retained_for_research() -> None:
    compiled = compile_narrative(fixture("buried-procedural-fact.json"))

    assert any(event.event_type == "notice" for event in compiled.intake.procedural_events)
    assert any(event.event_type == "hearing" for event in compiled.intake.procedural_events)
    assert any(date.normalized_date == "2026-05-04" and date.legally_material for date in compiled.intent.important_dates)
    assert any(issue.issue_id == "notice_service" for issue in compiled.intent.issue_hypotheses)
    assert any(issue.issue_id == "evidence_ruling" for issue in compiled.intent.issue_hypotheses)


def test_mixed_matters_are_separate_issue_hypotheses_and_query_families() -> None:
    compiled = compile_narrative(fixture("mixed-matters.json"))
    issue_ids = {issue.issue_id for issue in compiled.intent.issue_hypotheses}

    assert compiled.intent.matter_type.value == "mixed"
    assert {"probation_violation", "emergency_removal", "self_help_lockout"}.issubset(issue_ids)
    assert all(query.issue_id in issue_ids for query in compiled.plan.queries)
    assert all("criminal" not in query.query_variants[0] or query.issue_id == "probation_violation" for query in compiled.plan.queries)


def test_adverse_user_fact_is_preserved_as_reported_not_promoted_to_proof() -> None:
    compiled = compile_narrative(fixture("adverse-facts.json"))
    adverse = [fact for fact in compiled.intent.known_facts if fact.adverse_signal]

    assert adverse
    assert adverse[0].category == EvidenceCategory.USER_ASSERTED_FACT
    assert adverse[0].state == ResolutionState.KNOWN
    assert "independently verified" in " ".join(compiled.explanation.transparency_notes)
    assert any(query.query_class == QueryClass.ADVERSE_AUTHORITY_QUERY for query in compiled.plan.queries)
    assert any(query.query_class == QueryClass.LIMITING_AUTHORITY_QUERY for query in compiled.plan.queries)


def test_what_do_i_do_still_generates_research_questions() -> None:
    compiled = compile_narrative(fixture("what-do-i-do.json"))

    assert compiled.intake.user_questions == ("What do I do?",)
    assert compiled.intent.research_questions
    assert any(issue.issue_id == "probation_violation" for issue in compiled.intent.issue_hypotheses)


def test_noisy_private_narrative_is_abstracted_before_provider_serialization() -> None:
    compiled = compile_narrative(fixture("noisy-private-canaries.json"))
    requests = compiled.provider_requests()
    serialized = json.dumps([request.model_dump(mode="json") for request in requests])

    assert compiled.intake.people_or_entities
    assert compiled.intake.locations
    assert requests
    for canary in ("PRIVATE_PERSON_XYZ", "PRIVATE_CASE_123", "private@example.test", "123 Private Street"):
        assert canary not in serialized
    assert fixture("noisy-private-canaries.json") not in serialized
    assert all("landlord" in request.query_variants[0] or "lockout" in request.query_variants[0] or "notice" in request.query_variants[0] for request in requests)


def test_known_jurisdiction_emits_discovery_requests_but_posture_blocks_qualification() -> None:
    compiled = compile_narrative("This happened in Wisconsin. My landlord changed the locks. What can I do?")
    requests = compiled.provider_requests()

    assert compiled.intent.jurisdiction_state == compiled.intent.jurisdiction.state
    assert compiled.intent.jurisdiction_state.state == ResolutionState.KNOWN
    assert requests
    assert all(request.jurisdiction == "US-WI" for request in requests)
    assert all(request.research_id.startswith("LAY-RESEARCH-") for request in requests)
    assert all(request.query_variants for request in requests)
    assert all(request.requested_capabilities for request in requests)
    assert all(request.target_proposition != "" for request in requests)
    assert {query.query_class for query in compiled.plan.queries} == set(QueryClass)
    assert all(query.retrieval_mode.value == "DISCOVERY" for query in compiled.plan.queries if query.query_id in {f"Q-01-{index:02d}" for index in range(1, 11)} and query.query_class in {
        QueryClass.DOCTRINAL_QUERY, QueryClass.STATUTE_RULE_QUERY, QueryClass.FACT_PATTERN_QUERY,
        QueryClass.PROCEDURAL_POSTURE_QUERY, QueryClass.DEFINITION_TERMINOLOGY_QUERY,
    })


def test_conflicting_jurisdiction_evidence_is_explicit_and_not_silently_resolved() -> None:
    compiled = compile_narrative("This happened in Wisconsin, but the case was filed in Minnesota. My landlord changed the locks.")

    assert compiled.intent.jurisdiction_state.state == ResolutionState.CONFLICTING
    assert set(compiled.intent.jurisdiction_state.alternatives) == {"US-WI", "US-MN"}
    assert any(item.question_id == "CLARIFY-JURISDICTION" for item in compiled.intent.clarifications_needed)
    assert compiled.provider_requests() == ()


def test_compiler_artifacts_are_versioned_and_deterministic() -> None:
    first = compile_narrative(fixture("buried-procedural-fact.json"))
    second = compile_narrative(fixture("buried-procedural-fact.json"))

    assert first.intake.contract.endswith("/1.0")
    assert first.intent.contract.endswith("/1.0")
    assert first.plan.contract.endswith("/1.0")
    assert first.quality.contract.endswith("/1.0")
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_quality_assessment_separates_fixture_evidence_from_live_provider_gate() -> None:
    quality = compile_narrative(fixture("what-do-i-do.json")).quality
    statuses = {gate.gate: gate.status for gate in quality.gates}

    assert statuses["LAY_NARRATIVE_INGESTION"] == QualityGateStatus.PASS_FIXTURE_ONLY
    assert statuses["PRIVATE_TO_PUBLIC_QUERY_ABSTRACTION"] == QualityGateStatus.PASS_FIXTURE_ONLY
    assert statuses["LAY_LANGUAGE_RETRIEVAL_RECALL"] == QualityGateStatus.BLOCKED_DEPENDENCY
    assert not any(gate.live_source_qualified for gate in quality.gates)


@pytest.mark.parametrize("model_name", ["NarrativeResearchIntake", "ResearchIntent", "ResearchPlan"])
def test_compiler_artifact_rejects_future_version(model_name: str) -> None:
    compiled = compile_narrative(fixture("what-do-i-do.json"))
    model = getattr(compiled, {"NarrativeResearchIntake": "intake", "ResearchIntent": "intent", "ResearchPlan": "plan"}[model_name])
    payload = model.model_dump()
    payload["schema_version"] = "2.0"
    with pytest.raises(ValueError):
        model.__class__.model_validate(payload)
