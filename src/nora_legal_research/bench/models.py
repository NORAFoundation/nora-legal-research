"""NORA Bench V1 Scenario and Annotation Schemas.

Provides the schema for synthetic, auditable, adversarial benchmark scenarios testing:
- Narrative-to-issue compilation
- Procedural urgency detection
- Controlling vs persuasive authority separation
- Epistemic discipline (hypotheses vs conclusions)
- Prompt injection resistance
- Cross-matter isolation
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


BENCHMARK_SCENARIO_CONTRACT = "nora.legal-research/BenchmarkScenario/1.0"


class UserSophistication(str, Enum):
    LAY_UNREPRESENTED = "LAY_UNREPRESENTED"
    LAY_SEEKING_COUNSEL = "LAY_SEEKING_COUNSEL"
    EXPERIENCED_ADVOCATE = "EXPERIENCED_ADVOCATE"


class BenchmarkDocument(BaseModel):
    """Synthetic document associated with a scenario (e.g., notice, petition, text screenshot)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: str
    title: str
    document_type: str  # NOTICE, COURT_REPORT, TEXT_THREAD, PETITION, UNKNOWN
    text_content: str
    contains_adversarial_instruction: bool = False
    adversarial_payload_description: Optional[str] = None


class ExpectedCoverageRequirements(BaseModel):
    """Minimum required dimensional research coverage for a passing result."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    min_controlling_authority: float = 0.5
    min_governing_text: float = 0.5
    min_adverse_research: float = 0.5
    min_quote_verification: float = 0.5
    min_currentness: float = 0.5


class BenchmarkScenario(BaseModel):
    """Canonical NORA Bench V1 Scenario contract."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = BENCHMARK_SCENARIO_CONTRACT
    schema_version: str = "1.0"
    scenario_id: str
    category: str
    title: str
    jurisdiction: str
    domain: str = "CHILD_WELFARE"
    user_sophistication: UserSophistication
    ordinary_language_narrative: str
    documents: tuple[BenchmarkDocument, ...] = ()
    explicit_user_nominated_theory: Optional[str] = None
    hidden_or_latent_issues: tuple[str, ...] = ()
    procedural_posture: str
    urgency_or_deadline_facts: tuple[str, ...] = ()
    gold_issue_families: tuple[str, ...] = ()
    governing_source_families: tuple[str, ...] = ()
    expected_controlling_authority_characteristics: tuple[str, ...] = ()
    expected_adverse_research_requirement: tuple[str, ...] = ()
    known_traps: tuple[str, ...] = ()
    unsupported_conclusions_prohibited: tuple[str, ...] = ()
    expected_clarification_questions: tuple[str, ...] = ()
    expected_epistemic_labels: tuple[str, ...] = ()
    expected_coverage: ExpectedCoverageRequirements = Field(default_factory=ExpectedCoverageRequirements)
    substantive_gold_authority_pending: bool = True
    authority_verification_notes: tuple[str, ...] = (
        "Governing statutory and procedural rule framework verified against official primary sources; substantive case law holding qualification remains pending qualified citator integration.",
    )
    is_security_adversarial: bool = False
    adversarial_injection_prompt: Optional[str] = None
    matter_id: str = "DEFAULT-MATTER"

    @field_validator("contract")
    @classmethod
    def validate_contract(cls, v: str) -> str:
        if v != BENCHMARK_SCENARIO_CONTRACT:
            raise ValueError(f"unsupported BenchmarkScenario contract: {v}")
        return v

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        if not v.startswith("BENCH-"):
            raise ValueError(f"scenario_id must start with 'BENCH-': {v}")
        return v
