# Lay Narrative → Research Compiler

## Decision

NORA treats a self-represented user's narrative as evidence about a problem,
not as a legal query.  The compiler creates separate, versioned derived
artifacts:

```text
NarrativeResearchIntake
    → ResearchIntent
    → IssueHypothesis[]
    → ResearchPlan
    → AuthorityResearchRequest[]
```

These artifacts do not change `ResearchSnapshot/1.0`.  A `ResearchSnapshot`
records provider retrieval and verification state; it is not the container for
raw narratives, issue discovery, or user-facing explanation.

## Evidence and inference

`NarrativeResearchIntake` retains the raw narrative and separates reported
facts, questions, user interpretations, ambiguous facts, dates, entities,
locations, documents, courts/agencies, and recognizable procedural events.
Reported facts remain user assertions, not independently proven facts.

`ResearchIntent` records a user goal, an abstract problem summary, known,
inferred, unknown, and disputed facts, candidate governing sources, research
questions, urgency/deadline flags, and clarifications.  Every issue begins as
`ISSUE_HYPOTHESIS` (or `UNRESOLVED_ISSUE`); the compiler does not silently
promote an inference to a legal conclusion.  Trigger fact IDs and the
ontology source/version explain why an issue was raised.

## Jurisdiction and clarification

Country, state, county, court/system, matter type, posture, and relevant dates
are independently resolved as `KNOWN`, `INFERRED`, `UNKNOWN`, or
`CONFLICTING`.  A materially missing state produces a high-value question such
as “Which state is the case in?” and no provider request is emitted.  A known
state may permit broad discovery with explicit assumptions; qualification
queries wait for material posture information.  No state law is silently
assumed.

The compiler asks only questions expected to change jurisdiction, deadlines,
remedies, governing sources, hierarchy, standing, or standards.  Where safe,
it proceeds provisionally and records the assumption.

## Lay-language ontology

The initial ontology is intentionally small and extensible.  A general
lay-language cartridge maps ordinary descriptions to candidate concepts such as
lockout/eviction, notice/service, health-information evidence, emergency
removal, probation procedure, evidence preservation, and speedy trial.  Each
mapping carries source, version, confidence, and jurisdiction applicability.

Future mappings are composed as:

```text
general lay-language cartridge
    + jurisdiction cartridge
    + domain cartridge
    + procedural context
```

No one state's terminology is treated as universal, and mappings are research
navigation metadata rather than legal truth.

## Query-plan compiler

Each issue receives bounded query families rather than one narrative embedding:

`DOCTRINAL_QUERY`, `CONTROLLING_AUTHORITY_QUERY`, `STATUTE_RULE_QUERY`,
`FACT_PATTERN_QUERY`, `PROCEDURAL_POSTURE_QUERY`, `ADVERSE_AUTHORITY_QUERY`,
`LIMITING_AUTHORITY_QUERY`, `CURRENTNESS_TREATMENT_QUERY`,
`CITATION_GRAPH_QUERY`, and `DEFINITION_TERMINOLOGY_QUERY`.

Discovery queries favor recall and use abstract legal concepts.  Qualification
queries tighten jurisdiction, hierarchy, procedural fit, opinion voice,
currentness, and treatment.  The query class, rationale, constraints, dates,
capabilities, and variants are retained for expert inspection.

The compiler supports iterative research: plan, search, inspect, refine,
follow citations, search contrary authority, verify, and synthesize.  A plan
stops only when its completeness conditions are satisfied or a dimension is
explicitly `UNKNOWN`, `PARTIAL`, or `BLOCKED`.

## Privacy abstraction

The raw narrative never goes to a public authority provider.  Names,
addresses, emails, private case numbers, document text, private chronology,
and matter-specific facts remain inside intake/intent evidence.  Provider
requests contain only the reviewed `AuthorityResearchRequest` allowlist:
abstract issue identifiers, public legal terms, jurisdiction state when
resolved, minimum necessary date bounds, bounded limits, and capabilities.

Legally material dates are retained only as minimum necessary date constraints;
identity-sensitive dates are excluded.  The provider boundary remains the
canonical privacy control and is tested with synthetic private canaries.

## Transparency

`GuidedResearchExplanation` can tell the user what was translated, which facts
are being treated as user-reported, which assumptions were made, and why a
clarification is needed.  Professional and lay interactions use the same
source corpus, authority hierarchy, verification rules, and `ResearchSnapshot`
semantics; only interaction and explanation differ.

The downstream `ProfessionalResearchRecord` carries fact/source epistemology,
authority qualification dimensions, and a multidimensional completeness
assessment. `NonLawyerGuidedExplanation` exposes those results in plain
language using separate reported, verified, and unresolved sections. It is a
presentation boundary, not a lower evidentiary standard.

## Qualification status

The deterministic compiler and synthetic vectors qualify issue discovery,
privacy abstraction, query-family compilation, and explanation behavior for
the fixture lane.  They do not qualify live CourtListener retrieval.  The
mirror remains a separate source-faithful system, and live gates remain blocked
until its provider is requalified.
