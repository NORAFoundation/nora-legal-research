from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AuthorityType(str, Enum):
    CONSTITUTIONAL = "constitutional"
    STATUTE = "statute"
    REGULATION = "regulation"
    PRECEDENT_BINDING = "precedent_binding"
    PRECEDENT_PERSUASIVE = "precedent_persuasive"
    SECONDARY = "secondary"

class PrecedentialStatus(str, Enum):
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    OVERRULED = "overruled"
    QUESTIONED = "questioned"
    SUPERSEDED_BY_STATUTE = "superseded_by_statute"

class Jurisdiction(BaseModel):
    code: str  # e.g. US, US-WI, US-MN, US-8th-Cir
    level: str  # federal_supreme, federal_appellate, state_supreme, state_appellate, trial
    name: str

class Citation(BaseModel):
    citation_text: str
    volume: Optional[int] = None
    reporter: Optional[str] = None
    page: Optional[int] = None
    year: Optional[int] = None
    jurisdiction_code: str
    normalized_cite: str

class QuoteSpan(BaseModel):
    span_id: str
    citation_text: str
    exact_quote: str
    pinpoint_page: Optional[int] = None
    verified: bool = False

class ResearchSnapshot(BaseModel):
    snapshot_id: str
    query: str
    jurisdiction: Jurisdiction
    authorities: List[Citation] = Field(default_factory=list)
    quote_spans: List[QuoteSpan] = Field(default_factory=list)
    status_warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
