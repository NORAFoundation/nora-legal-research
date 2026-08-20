from __future__ import annotations
from typing import Tuple
from nora_legal_research.contracts import QuoteSpan

class QuoteVerifier:
    """
    Verifies exact quote spans against underlying authority text.
    """
    def verify_quote(self, span: QuoteSpan, authority_text: str) -> Tuple[bool, QuoteSpan]:
        clean_quote = span.exact_quote.strip().lower()
        clean_authority = authority_text.strip().lower()
        
        if clean_quote in clean_authority:
            span.verified = True
            return True, span
        else:
            span.verified = False
            return False, span
