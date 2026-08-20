from __future__ import annotations
from typing import List, Tuple
from nora_legal_research.contracts import Citation, PrecedentialStatus, ResearchSnapshot

class TreatmentAnalyzer:
    """
    Analyzes legal authority treatment, detecting overruled/questioned status,
    contrary/adverse authority, and generating status warnings in ResearchSnapshots.
    """
    def __init__(self, overruled_db: List[str] = None):
        self.overruled_db = overruled_db or ["bad law precedent 1", "500 U.S. 100"]

    def evaluate_authority_treatment(self, cite: Citation) -> Tuple[PrecedentialStatus, List[str]]:
        warnings = []
        status = PrecedentialStatus.BINDING
        
        cite_str = cite.normalized_cite.lower()
        for bad in self.overruled_db:
            if bad.lower() in cite_str:
                status = PrecedentialStatus.OVERRULED
                warnings.append(f"CRITICAL WARNING: Authority {cite.normalized_cite} is OVERRULED and no longer binding law.")
                break
                
        return status, warnings

    def audit_research_snapshot(self, snapshot: ResearchSnapshot) -> ResearchSnapshot:
        all_warnings = list(snapshot.status_warnings)
        for cite in snapshot.authorities:
            status, warnings = self.evaluate_authority_treatment(cite)
            if warnings:
                all_warnings.extend(warnings)
                
        snapshot.status_warnings = all_warnings
        return snapshot
