# Derived Search Layer Recommendations

These recommendations are for the separately owned mirror agent.  They do not
authorize changes to the mirror repository or its database/import systems.

## Source-fidelity rule

Layer A remains the complete, source-faithful CourtListener canon.  Layer B
indexes are disposable, versioned, and rebuildable from source record IDs and
snapshot provenance.  Layer C (`nora-legal-research`) owns narrative
compilation, research intent, query planning, qualification, and
`ResearchSnapshot` semantics.

## Recommendations

| Structure | Classification | Benefit | Source/rebuild/provenance | Cost and risk |
| --- | --- | --- | --- | --- |
| PostgreSQL FTS (`tsvector` + GIN) over opinion text and metadata | `RECOMMENDED_NOW` | Fast broad discovery and controlled lexical expansion | Build from immutable opinion/cluster IDs; record source snapshot, tokenizer, and index version | Moderate storage/build cost; tokenizer recall risk |
| Normalized citation extraction and citation lookup | `RECOMMENDED_NOW` | Exact authority lookup and citation-following | Parse source text/metadata; retain raw span, parser version, source ID, and confidence | Moderate; parser false positives |
| Court-hierarchy lookup | `RECOMMENDED_NOW` | Qualification filters and controlling-authority ranking | Derive from source court records plus versioned court metadata; retain effective dates | Low/moderate; hierarchy changes need review |
| Citation adjacency tables | `RECOMMENDED_NOW` | Follow authorities and find contrary/limiting candidates | Build edges from source citations; retain edge evidence and extraction version | Moderate; incomplete citation extraction |
| Opinion-section segmentation | `RECOMMENDED_LATER` | Separate majority, concurrence, dissent, syllabus, and disposition | Deterministic segmentation from source text; retain offsets and algorithm version | Moderate/high; segmentation errors can misattribute holdings |
| Statute/rule reference extraction | `RECOMMENDED_LATER` | Connect fact-pattern searches to governing text | Parse source text; retain exact reference span and parser version | Moderate; jurisdiction syntax varies |
| Case-name aliases and normalized party/citation forms | `RECOMMENDED_LATER` | Recall across citation/name variants | Derived only from source IDs; retain normalization rules and collisions | Low/moderate; over-merging risk |
| Materialized metadata search views | `RECOMMENDED_LATER` | Stable bounded query plans and predictable latency | Rebuild from source and Layer B records; include view/index versions | Moderate operational complexity |
| Hybrid lexical + metadata + graph candidate union | `RECOMMENDED_LATER` | Better recall and explainable qualification than one ranker | Preserve component scores, query plan, source IDs, and dedup decisions | Higher orchestration complexity; score calibration |
| Embeddings/semantic vectors | `RESEARCH_REQUIRED` | Finds conceptually similar language for discovery | Version model, chunking, source snapshot, and vector build; retain source IDs | High cost and drift; similarity is not legal importance |
| Legal concept tags and lay-language expansion dictionary | `RESEARCH_REQUIRED` | Improves issue discovery for non-lawyers | Version cartridge, jurisdiction applicability, evidence, and rebuild inputs | High false-positive and jurisdiction-transfer risk |
| Derived ranking features | `RESEARCH_REQUIRED` | Can prioritize likely useful candidates | Explain each feature and preserve source evidence; evaluate separately | Risk of hidden authority bias and ranking overreach |
| Replacing source text with embeddings or AI tags | `NOT_NEEDED` | None that justifies loss of source fidelity | Prohibited as the sole representation | Irrecoverable provenance and recall failure |
| Vector similarity alone determining legal importance | `NOT_NEEDED` | None | Must not be the qualification rule | Legal hierarchy, treatment, and posture are absent |

## Rebuild invariant

The mirror should support:

```text
drop Layer B indexes
  → Layer A remains complete and queryable for rebuild
  → rebuild deterministically from source IDs and snapshot
  → compare counts, hashes, and provenance receipts
```
