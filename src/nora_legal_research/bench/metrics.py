"""NORA Bench V1 Metric Contracts.

Formalizes evaluation metrics across 20 distinct dimensions.
Thresholds are configurable parameters rather than hard-coded guesses.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MetricName(str, Enum):
    LATENT_ISSUE_RECALL = "LATENT_ISSUE_RECALL"
    EXPLICIT_ISSUE_PRECISION = "EXPLICIT_ISSUE_PRECISION"
    JURISDICTION_ACCURACY = "JURISDICTION_ACCURACY"
    PROCEDURAL_TRAP_RECALL = "PROCEDURAL_TRAP_RECALL"
    CONTROLLING_AUTHORITY_RECALL = "CONTROLLING_AUTHORITY_RECALL"
    AUTHORITY_PRECISION = "AUTHORITY_PRECISION"
    HIERARCHY_ACCURACY = "HIERARCHY_ACCURACY"
    ADVERSE_AUTHORITY_RECALL = "ADVERSE_AUTHORITY_RECALL"
    PROPOSITION_PASSAGE_FIDELITY = "PROPOSITION_PASSAGE_FIDELITY"
    CITATION_VALIDITY = "CITATION_VALIDITY"
    CURRENTNESS_ACCURACY = "CURRENTNESS_ACCURACY"
    STATUTE_RULE_VERSION_ACCURACY = "STATUTE_RULE_VERSION_ACCURACY"
    EVIDENCE_GAP_IDENTIFICATION = "EVIDENCE_GAP_IDENTIFICATION"
    UNSUPPORTED_CLAIM_RATE = "UNSUPPORTED_CLAIM_RATE"
    EPISTEMIC_STATUS_ACCURACY = "EPISTEMIC_STATUS_ACCURACY"
    PLAIN_LANGUAGE_SEMANTIC_FIDELITY = "PLAIN_LANGUAGE_SEMANTIC_FIDELITY"
    PROMPT_INJECTION_RESISTANCE = "PROMPT_INJECTION_RESISTANCE"
    MATTER_ISOLATION_ACCURACY = "MATTER_ISOLATION_ACCURACY"
    RESEARCH_COST = "RESEARCH_COST"
    LATENCY_SECONDS = "LATENCY_SECONDS"


class MetricScore(BaseModel):
    """Evaluation result for an individual metric."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: MetricName
    score: float
    target_threshold: Optional[float] = None
    passed: Optional[bool] = None
    details: str = ""


class BenchmarkEvaluationReport(BaseModel):
    """Complete evaluation report over a scenario or suite."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    report_id: str
    scenario_id: str
    scores: tuple[MetricScore, ...]
    unsupported_conclusions_detected: tuple[str, ...] = ()
    prompt_injection_breached: bool = False
    cross_matter_contamination_detected: bool = False
    overall_pass: bool = True
    evaluator_notes: tuple[str, ...] = ()

    def get_metric_score(self, metric: MetricName) -> Optional[float]:
        for s in self.scores:
            if s.metric == metric:
                return s.score
        return None
