from __future__ import annotations
from typing import Any, Dict, Optional
from nora_legal_research.contracts import Citation

class CourtListenerNormalizer:
    """
    Normalizes CourtListener bulk API payload objects into canonical Citations
    and authority records (derived from legal-research-scaffold).
    """
    def normalize_opinion(self, payload: Dict[str, Any]) -> Citation:
        case_name = payload.get("case_name", "Unknown Case")
        cite_str = payload.get("citation", "Unknown Citation")
        vol = payload.get("volume")
        rep = payload.get("reporter")
        pg = payload.get("page")
        yr = payload.get("year")
        jur = payload.get("jurisdiction", "US")

        return Citation(
            citation_text=f"{case_name}, {cite_str}",
            volume=vol,
            reporter=rep,
            page=pg,
            year=yr,
            jurisdiction_code=jur,
            normalized_cite=cite_str
        )
