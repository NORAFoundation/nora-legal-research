from __future__ import annotations
import re
from typing import List, Optional
from nora_legal_research.contracts import Citation

REPORTER_PATTERN = re.compile(
    r"(?P<volume>\d+)\s+(?P<reporter>[A-Za-z0-9\.\s]+?)\s+(?P<page>\d+)(?:\s*\((?P<year>\d{4})\))?"
)

class CitationGuard:
    """
    Parses and validates legal citation patterns derived from lawllama-assurance.
    """
    def parse_citation(self, text: str, default_jurisdiction: str = "US") -> Optional[Citation]:
        match = REPORTER_PATTERN.search(text.strip())
        if not match:
            return None
        
        vol = int(match.group("volume"))
        rep = match.group("reporter").strip()
        pg = int(match.group("page"))
        yr = int(match.group("year")) if match.group("year") else None
        
        norm = f"{vol} {rep} {pg}" + (f" ({yr})" if yr else "")
        return Citation(
            citation_text=text.strip(),
            volume=vol,
            reporter=rep,
            page=pg,
            year=yr,
            jurisdiction_code=default_jurisdiction,
            normalized_cite=norm
        )
