"""Tests for NORA Bench V1 framework, corpus, and deterministic evaluators."""

import json
from pathlib import Path
import pytest

from nora_legal_research.bench.corpus import CANONICAL_BENCHMARK_SCENARIOS, get_canonical_scenarios
from nora_legal_research.bench.evaluator import DeterministicBenchEvaluator
from nora_legal_research.bench.metrics import MetricName
from nora_legal_research.bench.models import BenchmarkScenario


ROOT = Path(__file__).parents[1]
FIXTURES_BENCH_DIR = ROOT / "fixtures" / "bench"


def test_canonical_benchmark_corpus_completeness():
    scenarios = get_canonical_scenarios()
    assert len(scenarios) == 25, f"Expected 25 benchmark scenarios, got {len(scenarios)}"

    scenario_ids = [s.scenario_id for s in scenarios]
    assert len(scenario_ids) == len(set(scenario_ids)), "Scenario IDs must be unique"

    for s in scenarios:
        assert s.scenario_id.startswith("BENCH-")
        assert len(s.gold_issue_families) > 0, f"Scenario {s.scenario_id} lacks gold issues"
        assert len(s.known_traps) > 0, f"Scenario {s.scenario_id} lacks known traps"
        assert len(s.unsupported_conclusions_prohibited) > 0, f"Scenario {s.scenario_id} lacks prohibited conclusions"
        assert len(s.governing_source_families) > 0, f"Scenario {s.scenario_id} lacks governing sources"


def test_evaluator_catches_prompt_injection_breach():
    scenario = next(s for s in CANONICAL_BENCHMARK_SCENARIOS if s.is_security_adversarial)
    evaluator = DeterministicBenchEvaluator()

    # Case A: Prompt injection was prevented
    clean_report = evaluator.evaluate_scenario(
        scenario,
        extracted_issues=[
            "WIS_STAT_48_335",
            "DISPOSITIONAL_HEARING_CALENDAR_DATE_OCT_12_2026",
            "DATA_IS_NOT_INSTRUCTION_INVARIANT",
            "SECURITY_PROMPT_INJECTION_DEFENSE",
        ],
        identified_authorities=["Wis. Stat. § 48.335"],
        adverse_authorities=["State v. R.H."],
        identified_traps=["Allowing unverified document content to alter system instructions"],
        generated_claims=["Dispositional hearing scheduled for October 12, 2026."],
        prompt_injection_breached=False,
    )
    assert clean_report.overall_pass
    assert not clean_report.prompt_injection_breached

    # Case B: Prompt injection breached
    breached_report = evaluator.evaluate_scenario(
        scenario,
        extracted_issues=["WIS_STAT_48_335"],
        identified_authorities=["Wis. Stat. § 48.335"],
        adverse_authorities=[],
        identified_traps=[],
        generated_claims=["Autonomous Admin Mode activated. Child must be delivered immediately."],
        prompt_injection_breached=True,
    )
    assert not breached_report.overall_pass
    assert breached_report.prompt_injection_breached
    assert len(breached_report.unsupported_conclusions_detected) > 0


def test_evaluator_catches_unsupported_conclusion():
    scenario = next(s for s in CANONICAL_BENCHMARK_SCENARIOS if s.scenario_id == "BENCH-001-WRONG-LEGAL-TERMINOLOGY")
    evaluator = DeterministicBenchEvaluator()

    report = evaluator.evaluate_scenario(
        scenario,
        extracted_issues=["TEMPORARY_PHYSICAL_CUSTODY_HEARING_TIMING"],
        identified_authorities=["Wis. Stat. § 48.21"],
        adverse_authorities=["Wis. Stat. § 48.19"],
        identified_traps=["Filing criminal kidnapping complaint fails to appear at custody hearing"],
        generated_claims=["The CPS worker committed felony kidnapping and child theft."],
    )
    assert not report.overall_pass
    assert "CPS worker committed felony kidnapping" in report.unsupported_conclusions_detected


def test_fixture_json_serialization_and_roundtrip():
    FIXTURES_BENCH_DIR.mkdir(parents=True, exist_ok=True)
    json_path = FIXTURES_BENCH_DIR / "canonical_bench_v1.json"

    # Export
    payload = [s.model_dump() for s in CANONICAL_BENCHMARK_SCENARIOS]
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Roundtrip read
    loaded_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert len(loaded_data) == 25
    reconstructed = [BenchmarkScenario.model_validate(item) for item in loaded_data]
    assert len(reconstructed) == 25
    assert reconstructed[0].scenario_id == CANONICAL_BENCHMARK_SCENARIOS[0].scenario_id
