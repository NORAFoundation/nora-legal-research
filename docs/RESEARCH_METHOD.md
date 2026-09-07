# Research Method

## Retrieval funnel

```text
user narrative
  → fact/event extraction
  → jurisdiction and posture resolution
  → issue hypotheses
  → broad legal concept discovery
  → research questions
  → query families
  → broad authority discovery
  → hierarchy/jurisdiction filtering
  → controlling search
  → adverse/limiting search
  → authority verification
  → currentness/treatment
  → rule synthesis and fact-labeled application
```

The compiler makes each transition inspectable.  It does not turn a whole
narrative into a single vector query or treat semantic similarity as legal
importance.

## Discovery and qualification

Discovery retrieval is recall-oriented and may return extra candidates.
Qualification is progressively strict about jurisdiction, court hierarchy,
precedential status, opinion voice, procedural fit, currentness, and treatment.
The two modes share the same provider contract and source records.

## Iterative orchestration

The deep-research consumer may repeatedly plan, search, inspect results, refine
queries, follow citation edges, locate governing text, search adverse authority,
and verify.  Each pass remains bounded and records its query class and reason.

Research stops when the applicable completeness conditions are met: controlling
authority or an explicit block is recorded, governing text is identified,
adverse/limiting searches are complete or blocked, hierarchy is checked,
quotes are verified or marked unavailable, currentness is checked or blocked,
and material conflicts are surfaced.

If retrieval is empty, controlled expansions may use synonyms, broader doctrine,
jurisdiction terminology, statute references, older terminology, and citation
graph neighbors.  Exhaustion yields `UNKNOWN`, `PARTIAL`, or `BLOCKED` for the
research dimension, never `NO LAW`.
