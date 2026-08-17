# Architecture Decision Intelligence for an Enterprise AI Solution Advisor

**A design for the reasoning mechanism — not the code, not a scoring model.**

Prepared from the perspective of a Principal Enterprise Architect who has built and operated large-scale enterprise AI platforms.

---

## Part 0 — The verdict, up front

Three things about your current thinking need to change before anything else is worth designing.

**1. Your pipeline queries the Catalog before it knows what it needs.**
`User → Advisor → Catalog MCP → find reusable capabilities → LLM generates architecture` performs capability discovery *before* the problem has been characterised architecturally. That inverts the dependency. You cannot search for capabilities until you know which capabilities are *required*, and you cannot know that until you have determined the solution class, the obligations, and the applicable patterns. As built, the Catalog becomes the framing device: whatever happens to be in it shapes the architecture. This is availability bias implemented in software, and it is the single most damaging flaw in the design.

**2. A "Knowledge & Evidence Layer" is directionally right but wrongly scoped.**
You are about to put three things with fundamentally different authority semantics into one layer: *what we know* (advisory), *what we have* (inventory), and *what we must* (binding). Policy and constraint must be split out into their own plane with deterministic evaluation. If a compliance rule lives behind a vector search, then a recall miss becomes a compliance incident. Advisory knowledge failing produces a mediocre suggestion; binding knowledge failing produces a breach. They cannot share a retrieval mechanism.

**3. The missing component is not a knowledge layer at all — it is a decision process.**
Adding knowledge to an LLM that generates architectures gives you a better-informed generator. It does not give you an architect. What separates an architect from a well-read generator is a *governed sequence of commitments*: framing, obligation resolution, option generation, elimination, tradeoff, decision, and a durable record of why. The core of this system is a **Decision Kernel** that builds a structured **Decision Record** stage by stage. The LLM is an instrument inside that kernel, not the thing that produces the answer.

There is also a framing point worth making: calling this a "recommendation engine" understates what it should do. The most valuable answers an experienced architect gives are frequently *not* an architecture:

- "This already exists — solution SOL-041 does exactly this; extend it."
- "Your problem is underspecified in a way that changes the answer; here are the three questions I need answered."
- "What you described is not an AI problem; it is a data quality problem."
- "This is buildable, but the compliance path is 14 weeks and you should know that before you start."

Design the system so these are first-class outcomes, not failure modes. A system that always returns an architecture is a system that will confidently return an architecture when it should not.

Everything below assumes those three corrections.

---

## Part 1 — Recommended architecture for the Advisor

### 1.1 The five planes

Replace `Advisor → Catalog → LLM` with a plane-separated architecture. Planes are separated by **authority semantics**: what happens when the plane is wrong, and who is accountable.

**Plane 1 — Catalog Plane ("what we have")**
Authoritative inventory of enterprise AI capability: MCP servers, skills, plugins, components, workbenches, models, APIs, deployed solutions-as-assets. Accessed live over the existing Catalog MCP. Never forked into a vector store as the source of truth — availability, support status and compliance posture change, and a stale reuse recommendation is worse than no recommendation. Failure mode: recommending something that does not exist or is being sunset.

**Plane 2 — Knowledge Plane ("what we know")**
Advisory. Contains the Pattern Library, the Precedent Store (past solutions and their outcomes), architecture decision records, lessons learned, anti-patterns, and curated external reference material. Retrieval-based and probabilistic. Failure mode: a suboptimal or unimaginative recommendation.

**Plane 3 — Policy & Constraint Plane ("what we must")**
Binding. Data classification rules, PHI/PII handling obligations, residency requirements, approved technology lists, model approval status, network boundary rules, identity and authorisation standards, mandatory controls, deployment gates. Deterministic rule evaluation over a versioned registry. No vector search, no LLM interpretation of whether a rule applies where the rule is machine-evaluable. Failure mode: a compliance breach.

**Plane 4 — Decision Plane ("how we decide")**
The Decision Kernel: the staged reasoning pipeline, the elimination gates, the sourcing precedence logic, the candidate constructor, and the Decision Record it produces. This is the actual product. Everything else is input.

**Plane 5 — Interaction Plane**
Intake, clarification dialogue, presentation, the interactive explanation surface, human architect review and override, and export into the SDLC (ADR drafts, backlog, security pre-review).

**Cross-cutting — Evidence Ledger.**
Not a plane; a property of the Decision Record. Every assertion the system makes carries typed provenance and derivation edges. Rendering the recommendation is a *projection of the ledger*, never an independent generation.

### 1.2 Why this beats the alternative

| Concern | Your pipeline | Plane-separated kernel |
|---|---|---|
| Catalog bias | Catalog frames the problem | Catalog only resolves already-derived requirements |
| Compliance | LLM-interpreted, in prose | Deterministic, versioned, testable |
| Reproducibility | None — regenerates each time | Same input + same knowledge version = same record |
| Explainability | Post-hoc rationalisation | Traversal of the record that produced the decision |
| Hallucinated assets | Likely | Structurally blocked by closed-vocabulary resolution + validator |
| Improvement | Prompt tweaking | Knowledge and rule curation, with regression tests |

### 1.3 The one rule that fixes the bias problem

> **No catalog asset may enter a candidate architecture except as the resolution of a capability requirement derived independently of the catalog.**

This single invariant is what stops the Advisor from being a recommendation engine for whatever the platform team happens to have built. It also gives you an honest gap report: capability requirements with no resolution *are* the enterprise's AI capability roadmap.

---

## Part 2 — What knowledge the Advisor actually needs, and where it lives

The organising question is not "is this useful?" but **"what is the authority of this fact, and what is its volatility?"** That pair determines both storage and access mechanism.

### 2.1 Enterprise knowledge

| Knowledge | Plane | Why |
|---|---|---|
| AI components, MCP servers, skills, plugins, workbenches, models, APIs | Catalog (live) | Authoritative + volatile. Status, version and support level change. Query live; cache only with short TTL and always revalidate before it appears in a recommendation. |
| Existing AI solutions (as deployed things) | Catalog | They are consumable assets, with owners and SLAs. |
| Existing AI solutions (as architectural precedent) | Knowledge | Same entity, different projection. The Precedent Store holds the *dossier*: problem context, decisions, outcomes, lessons. Linked by ID to the Catalog record. |
| Approved technology list | **Policy** | This is not knowledge, it is a constraint. Binding, deterministic. |
| Architecture decision records (ADRs) | Knowledge, with promotion | Most ADRs are precedent. Some are *standards* ("all retrieval must enforce caller-identity filtering"). Standards get promoted into the Policy Plane with a rule ID. The promotion step is a deliberate human act. |
| Lessons learned | Knowledge | Advisory, high value, must carry evidence class and recency. |
| Production outcomes (latency, cost band, incidents, eval results, adoption) | Knowledge, sourced from Catalog/observability APIs | This is what converts precedent from anecdote into evidence. Without it your precedent store is a folder of aspirational diagrams. |
| Failed and abandoned solutions | Knowledge (negative evidence) | Deliberately retained. Most organisations delete these, and it is the most decision-relevant knowledge they own. |

### 2.2 Architecture knowledge (RAG, agents, MCP, A2A, GraphRAG, HITL, etc.)

**This does not belong in a document store, and it must not be retrieved by similarity.**

Your pattern set is a small, closed, slowly-changing vocabulary — realistically 30 to 60 entries. Vector-retrieving a subset of 60 known items introduces recall failure with no compensating benefit. Patterns should be **structured records with machine-readable applicability contracts**, held in the Knowledge Plane and evaluated in full at every run.

Each pattern record carries:

- **Intent** — the problem it solves, in one sentence.
- **Preconditions** — what must be true of the problem for it to be viable.
- **Indications** — normalised requirement signatures that *trigger* it.
- **Contra-indications** — signatures that *disqualify* it.
- **Required capabilities** — abstract, vendor-neutral capability requirements it imposes.
- **Imposed obligations** — the operational tax: eval harness, observability, guardrails, HITL, on-call.
- **Complexity class** and **escalation triggers** — what specifically must be true to justify moving up to it.
- **Composition rules** — typed relations: `requires`, `composes-with`, `subsumes`, `conflicts-with`, `escalates-to`, `degrades-to`.
- **Failure modes** — known ways it goes wrong in production.
- **Enterprise maturity** — proven / emerging / experimental, with internal precedent count.
- **Evidence** — links to internal precedents and curated external references.

Writing these contracts is the single highest-leverage piece of work in the entire project. It is also the part that cannot be outsourced to an LLM, because it encodes your organisation's actual judgement.

### 2.3 External knowledge (Microsoft, Google, AWS, Anthropic, OpenAI, NIST, OWASP)

**Do not retrieve these at recommendation time.** Three reasons:

1. **Vendor bias.** Reference architectures from cloud providers are shaped to sell that provider's stack. Live-retrieving them makes your Advisor a channel partner. You want technology-neutral capability recommendations, then a separate mapping to your approved stack.
2. **Non-determinism and latency.** Live external retrieval destroys reproducibility, which you need for governance and regression testing.
3. **Unreviewed content becomes authoritative by accident** once it appears in a recommendation.

Instead, run a **curation pipeline**: external sources are ingested on a cadence, reviewed by a human architect, and *distilled into* the internal artefacts.

- Vendor and lab reference architectures (Microsoft, Google, AWS, Anthropic, OpenAI) → refine **pattern contracts**; cited as rationale anchors, never as the decision.
- NIST AI RMF, ISO/IEC 42001 → **control library**, mapped to obligations. Produces the compliance mapping artefact as an output.
- OWASP Top 10 for LLM Applications, OWASP ASVS → **threat-to-guardrail mapping** attached to patterns, so security-by-design is mechanical rather than remembered.
- Academic and industry results → pattern maturity ratings and failure-mode catalogues.

The one legitimate live-external use is an explicit, flagged **"horizon scan"** mode a human can invoke: *"is there an option here we don't know about?"* Its output is marked unverified and cannot enter a binding recommendation until reviewed.

### 2.4 Enterprise constraints

All of these belong in the **Policy & Constraint Plane**, but split into two classes, because they behave differently in reasoning:

**Class A — Obligations (binary, binding, eliminate options).**
Data classification and PHI/PII handling, residency, approved models and technologies, network boundary and egress rules, identity and authorisation standards, mandatory audit logging, retention, deployment gates. These are *evaluated*, not weighed. An architecture either satisfies them or it is eliminated. No numbers required, which is exactly why elimination beats scoring here.

**Class B — Objectives (directional, tradeable, order options).**
Cost envelope, latency target, availability target, scalability horizon, time-to-market, team capability, operational burden tolerance. These never eliminate; they *differentiate* among architectures that already satisfy all obligations, and they are what generate meaningful alternatives.

Confusing these two is the most common failure in enterprise architecture tooling. "Must not leave the EU" and "should be cheap" are not the same kind of statement and must not be processed by the same mechanism.

**Sourcing.** Obligations should not be typed in by a user. Wherever possible derive them: data classification service, IAM, the approved-technology registry, the model registry, the FinOps system. A user saying "there's no PHI in this" does not override a classification service saying the source system is PHI-bearing. The system should treat user constraint claims as *hypotheses to verify*, not facts.

---

## Part 3 — The recommendation reasoning flow

Your proposed sequence is close, but has three ordering defects:

1. **Constraints arrive too late.** They are the strongest pruning force and they shape which patterns are even admissible. Deriving them after candidate construction means you generate options you then discard — and worse, it invites the LLM to rationalise a favoured architecture against constraints it has already seen.
2. **Catalog search happens too early** (already covered).
3. **There is no sufficiency gate.** A real architect refuses to proceed on an underspecified problem, or proceeds on explicitly stated assumptions. Your flow has no place for "I need to ask you something."

Here is the sequence I would build. Fifteen stages, each producing a durable artefact appended to the Decision Record.

---

### Stage 1 — Intake & Framing

- **Input:** Free-text problem statement; optional attachments; requester identity, business unit, system context.
- **Reasoning:** Establish what kind of request this is — new build, extension of existing, evaluation of a proposal, or "does this already exist?". Detect scope: feature, application, or platform capability.
- **Knowledge:** Requester context (business unit → default policy scope, default data domains).
- **Output:** Request Frame — request type, scope level, business domain, requester context.
- **Execution:** LLM classification into a closed taxonomy + deterministic enrichment from directory/org data.

---

### Stage 2 — Problem Interpretation

- **Input:** Request Frame + raw statement.
- **Reasoning:** Separate the *job to be done* from the *solution the user has already imagined*. Users arrive with a solution ("I want a chatbot"); the architect's first move is to recover the underlying problem ("employees can't get reliable answers about their benefits, and HR handles 400 tickets a month"). Identify actors, data sources, interaction modes, decision consequences, volume, and whether the request contains a solution assumption that should be challenged.
- **Knowledge:** Business domain glossary; solution-class taxonomy.
- **Output:** Problem Statement — job to be done, actors, triggering events, current process, success definition, **and an explicit list of solution assumptions embedded in the request**.
- **Execution:** LLM, constrained to a schema. This is the stage where self-consistency (multiple independent interpretations, reconciled) pays for itself, because every downstream error inherits from here.

---

### Stage 3 — Requirement Extraction & Normalisation

- **Input:** Problem Statement.
- **Reasoning:** Convert prose into **normalised requirement signatures** — the canonical vocabulary the rest of the system reasons over. This is the mechanism that replaces keyword matching. "It needs to show where the answer came from" becomes `ATTRIBUTION_REQUIRED: response must be traceable to source document span`. "It should handle our whole policy library" becomes `CORPUS_SCALE: > context window` plus `CORPUS_VOLATILITY: monthly`.
- Requirement categories: functional, informational (data sources, freshness, corpus scale, structure), interaction (modality, latency, session), action (does it mutate systems of record? reversible?), quality (accuracy, attribution, coverage), operational (availability, scale, support model), and evolution (what is planned next).
- Anything the LLM inferred rather than read becomes an **Assumption** with an explicit flag, not a requirement.
- **Knowledge:** Requirement signature taxonomy (closed vocabulary — this is a controlled list you author).
- **Output:** Requirement Set (each with ID, category, source span, confidence), Assumption Register, Clarification Set.
- **Execution:** LLM extraction into a closed schema; deterministic validation that every signature is in the vocabulary; deterministic completeness check against a required-fields matrix per solution class.

---

### Stage 4 — Sufficiency Gate

- **Input:** Requirement Set, Assumption Register, Clarification Set.
- **Reasoning:** Determine whether the problem is specified well enough to recommend safely. Some gaps are tolerable (record an assumption and proceed). Some are **decision-critical**: if the answer to a question would change the recommended architecture, you must not guess. Data sensitivity, whether actions mutate systems of record, and corpus scale are almost always decision-critical.
- **Output:** Either `PROCEED` (with recorded assumptions), `PROCEED-WITH-QUESTIONS` (proceed and present blocking questions alongside a provisional recommendation), or `HALT-CLARIFY`.
- **Execution:** **Deterministic rules.** A rule set of the form "if requirement signature X is unknown AND X appears in the indication or contra-indication set of two or more admissible patterns, then X is decision-critical." This is computable, and it should be, because an LLM asked "do you have enough information?" will nearly always say yes.

---

### Stage 5 — Obligation Resolution

- **Input:** Requirement Set (particularly data sources, actors, domain), requester context.
- **Reasoning:** Determine the binding obligation set. Query classification services for the actual sensitivity of the named data sources. Resolve residency from data domain. Resolve approved model list, network zone, identity model, mandatory controls, and required approval gates. Map applicable control frameworks.
- **Knowledge:** Policy Plane registry; data classification service; model registry; approved-technology registry; control library (NIST/OWASP mappings).
- **Output:** Obligation Set — each obligation with a rule ID, source, scope, evaluation predicate, and required evidence at review time.
- **Execution:** **Fully deterministic.** Rule evaluation over structured facts. The LLM's only role here is to help map an unfamiliar data source name to a registry entry — and if it cannot, that is a clarification, not a guess.

**Why this stage sits here and not later:** obligations are inputs to pattern admissibility. "PHI present" does not merely constrain the deployment; it disqualifies architectures and mandates capabilities. Deriving it after you have drawn a picture means you are editing a picture instead of deriving an architecture.

---

### Stage 6 — Solution Class Determination

- **Input:** Problem Statement + Requirement Set.
- **Reasoning:** Classify into a controlled solution taxonomy — e.g. grounded knowledge assistant, document processing pipeline, decision support, conversational transaction agent, autonomous workflow, content generation, classification/extraction service, analytics copilot. The solution class determines which pattern families are even in scope and which requirement fields are mandatory.
- **Knowledge:** Solution class taxonomy with per-class required-requirement matrices.
- **Output:** Solution Class (primary + secondary), with justification and rejected classes.
- **Execution:** Hybrid — LLM proposes with justification; deterministic validation that the requirement profile is consistent with the class; mismatch triggers re-examination rather than silent acceptance.

---

### Stage 7 — Capability Requirement Derivation

- **Input:** Solution Class, Requirement Set, Obligation Set.
- **Reasoning:** Derive the **abstract, vendor-neutral capabilities** the solution needs. This is the interlingua between Knowledge and Catalog. Examples: *permission-aware document retrieval*, *span-level citation resolution*, *PHI-safe prompt logging*, *policy-based response filtering*, *identity propagation to downstream systems*, *action authorisation with approval workflow*, *evaluation harness for grounded answers*.
- Crucially, obligations generate capability requirements too. `PHI_PRESENT` generates *de-identification or PHI-approved processing boundary*, *audit logging with subject traceability*, and *retention control* — before any pattern has been chosen.
- **Knowledge:** Capability taxonomy (the shared vocabulary that both patterns and catalog assets are annotated against); obligation→capability mapping table.
- **Output:** Capability Requirement Set, each marked mandatory / conditional / deferred-to-later-increment.
- **Execution:** Primarily deterministic mapping from obligations and solution class; LLM adds problem-specific capabilities, restricted to the taxonomy.

---

### Stage 8 — Pattern Admissibility Analysis

- **Input:** Requirement Set, Obligation Set, Capability Requirement Set.
- **Reasoning:** Evaluate **every** pattern in the library against the problem — not a retrieved subset. For each, produce one of five verdicts: `REQUIRED`, `APPLICABLE`, `CONDITIONAL` (with the named condition), `UNNECESSARY` (complexity not justified by any requirement), `CONTRA-INDICATED` (a disqualifying signature is present).
- Matching is signature-to-indication, over the closed vocabulary from Stage 3. This is the answer to "not keyword matching": the semantic work happened once, at normalisation, under schema constraint, and is auditable.
- **Knowledge:** Pattern Library with applicability contracts.
- **Output:** Pattern Verdict Set — with reasons, **including reasons for every rejection**. The rejections are what make the output read like an architect rather than a generator.
- **Execution:** Rules-first over the contracts; LLM reviews only the borderline cases and cases where a contract's precondition needs interpretation. Every LLM override of a rule verdict is flagged in the record.

---

### Stage 9 — Precedent Retrieval & Analysis

- **Input:** Problem Statement, Requirement Set, Obligation Set, Solution Class.
- **Reasoning:** Find prior solutions with a similar *decision situation*, analyse what they decided, whether it worked, and whether their triggering conditions hold here. Precedents serve three distinct purposes: feasibility confirmation, decision transfer, and hazard warning.
- **Knowledge:** Precedent Store (structured dossiers + narrative + graph edges); production outcome data.
- **Output:** Precedent Findings — each with the solution ID, similarity basis, evidence class, transferable decisions with their conditions, divergences from the current problem, and recorded lessons.
- **Execution:** Hybrid retrieval (structured constraint-profile filter, then vector similarity on problem narrative, then graph expansion) + LLM comparative analysis that must explicitly state where the precedent *differs*.

---

### Stage 10 — Catalog Resolution

- **Input:** Capability Requirement Set.
- **Reasoning:** For each capability requirement, query the Catalog MCP for candidate assets and assess fit across six dimensions: functional fit, **compliance fit** (is this asset approved for this data class?), integration fit, operational fit (capacity, SLA, latency), lifecycle fit (supported, or being sunset?), and access fit (can this team actually consume it, and at what cost?).
- Note that a compliance-unfit asset is not a partial match. An unapproved retrieval component in a PHI context is a non-match, regardless of functional excellence.
- **Knowledge:** Catalog (live); asset↔capability annotations; asset lifecycle and support metadata.
- **Output:** Resolution Map — per capability: matched assets with fit assessment, or an explicit **Gap**.
- **Execution:** Deterministic retrieval and filtering; LLM only for semantic disambiguation where annotations are ambiguous, and never to invent an asset. Closed-vocabulary: the LLM may only reference asset IDs returned by the Catalog.

---

### Stage 11 — Sourcing Decisions (Reuse / Compose / Extend / Buy / Build)

- **Input:** Resolution Map, Gaps, Obligation Set, objectives (time, cost, team).
- **Reasoning:** Per capability, apply the sourcing precedence ladder (Part 8).
- **Output:** Sourcing Decision per capability, with justification and the named rejected alternative.
- **Execution:** Deterministic precedence with rule-based escalation; LLM writes the justification narrative but cannot change the precedence outcome without a recorded override reason.

---

### Stage 12 — Candidate Architecture Construction

- **Input:** Admissible patterns, sourcing decisions, precedent findings, obligations.
- **Reasoning:** Construct **two to four coherent candidates**, deliberately spanning the real tension axes rather than being cosmetic variants. Typical spread: (a) minimum sufficient architecture, (b) maximum reuse architecture, (c) fastest-to-production architecture, (d) target-state architecture with the staged increment marked.
- Each candidate must be *coherent*: patterns satisfy their composition rules, every required capability is sourced, every obligation has an owning component.
- **Knowledge:** Pattern composition rules; reference compositions; precedent architectures.
- **Output:** Candidate Set — component view, data flows, trust boundaries, pattern manifest, asset manifest, build items, and the staged increment plan with the **seams** that keep later evolution non-breaking.
- **Execution:** LLM composition constrained by deterministic composition rules; a structural validator rejects incoherent candidates before they are shown to anyone.

---

### Stage 13 — Elimination

- **Input:** Candidate Set, Obligation Set, hard feasibility constraints.
- **Reasoning:** Apply hard gates. A candidate is eliminated if it violates any obligation, leaves any mandatory capability unsourced, requires an unapproved technology with no exception path, exceeds a hard budget or timeline boundary, or requires operational capability the organisation demonstrably lacks (with precedent evidence).
- **Output:** Surviving candidates + Elimination Record (candidate, gate, rule ID, evidence). The eliminations are shown to the user.
- **Execution:** **Fully deterministic.** No LLM. This is the stage where determinism matters most, because it is the stage most susceptible to plausible-sounding rationalisation.

---

### Stage 14 — Differentiation & Selection

- **Input:** Surviving candidates, Class B objectives, declared priority, precedent evidence.
- **Reasoning:** Compare survivors along the axes where they *actually differ*, then select under the declared priority ordering. If no priority has been declared, the default is: **satisfy all obligations, then minimise complexity, then maximise reuse, then minimise time-to-first-production-value.** Declare that default explicitly in the output so it can be challenged.
- Apply the **complexity budget**: any pattern present in the recommended candidate but absent from the minimum sufficient candidate must be justified by a named requirement. Unjustifiable additions are stripped.
- **Output:** Recommended architecture, ordered alternatives with their governing priority, and an explicit tradeoff analysis.
- **Execution:** LLM reasoning over structured comparison, constrained by rule-defined priority ordering. The LLM articulates the tradeoff; the priority ordering decides the winner.

---

### Stage 15 — Evidence Validation & Assembly

- **Input:** Complete Decision Record.
- **Reasoning:** Verify before rendering. Every referenced asset ID exists in the Catalog and is currently supported. Every policy ID exists in the registry at the stated version. Every pattern and precedent ID resolves. Every load-bearing claim has provenance other than "model inference," or is reclassified as a stated Assumption. No obligation is unaddressed. No capability is unsourced.
- **Output:** Validated Decision Record; the rendered recommendation is a projection of it.
- **Execution:** **Fully deterministic.** Unresolvable reference is a hard failure, not a warning. This validator is the reason the LLM cannot invent capabilities, solutions, policies or sources — it is not a matter of prompting.

---

### 3.1 The through-line

Notice the shape: **LLM at the edges, determinism in the middle.** Language understanding at the front, narrative synthesis at the back, and in between a governed sequence where the load-bearing decisions are made by rules over structured knowledge. That is the difference between an architect and a very well-read generator.

---

## Part 4 — Elimination-based reasoning, formalised

You are right that this is the correct mode, and right to reject scoring. Weighted scores over architecture options are false precision: the weights are invented, the sub-scores are invented, and the resulting number launders an unjustified judgement into an authoritative-looking figure. Worse, it is unarguable — a reviewer cannot dispute a 7.4.

But pure elimination is not sufficient either. Elimination alone tends to leave several survivors and no way to choose. The correct model has **three forces plus a tie-breaker**:

**Force 1 — Obligations eliminate.** Binary, binding, rule-evaluated. "PHI present and this component is not PHI-approved" removes the option. No weighting.

**Force 2 — Sufficiency eliminates.** If a candidate does not satisfy a mandatory requirement, it is out. "No citation mechanism" removes it when attribution is required.

**Force 3 — Parsimony orders.** Among sufficient, compliant options, prefer the one with the fewest moving parts. Formalised as the **complexity budget**: the baseline is the simplest architecture that satisfies all obligations and mandatory requirements, and every increment above that baseline must be justified by a named requirement signature. **Burden of proof sits on complexity, always.**

**Tie-breaker — Precedent.** Where options remain genuinely comparable, prefer the one with production precedent in this organisation, under similar obligations. Not because it is theoretically superior, but because the organisation has already paid the learning cost and the operational risk is measured rather than estimated.

Then: **residual differences become alternatives**, not a scoring exercise.

### 4.1 Escalation ladders — the anti-over-engineering mechanism

Encode complexity as ladders with explicit triggers. A rung is `CONTRA-INDICATED` unless its trigger is present in the Requirement Set. This is what makes point 8 of your worked example ("full multi-agent is unnecessary initially") mechanical rather than a matter of taste.

**Retrieval ladder**
1. *No retrieval* — model knowledge sufficient. Trigger to escalate: `ENTERPRISE_PRIVATE_DATA` or `FRESHNESS_REQUIRED`.
2. *Direct context injection* — corpus fits in context, static, no per-user filtering. Trigger: `CORPUS_SCALE > context` OR `PER_USER_AUTHORISATION` OR `CORPUS_VOLATILITY: high`.
3. *Single-pass RAG (hybrid retrieval + rerank)* — the default enterprise baseline. Trigger to escalate: `MULTI_HOP_QUERIES` OR `QUERY_AMBIGUITY_HIGH` OR `SOURCE_FEDERATION > 3 heterogeneous stores`.
4. *Agentic RAG (query planning, iterative retrieval, self-checking)*. Trigger: `RELATIONSHIP_TRAVERSAL_REQUIRED` OR `ENTITY_RESOLUTION_ACROSS_SOURCES`.
5. *GraphRAG*. Requires an entity model and a maintained graph — a standing data-engineering obligation, not a retrieval tweak.

**Agency ladder**
1. *Fixed prompt / no tools.* Trigger: `EXTERNAL_DATA_ACCESS` or `ACTION_REQUIRED`.
2. *Constrained tool calling* (fixed tool set, bounded loop). Trigger: `TASK_DECOMPOSITION_REQUIRED` or `VARIABLE_STEP_COUNT`.
3. *Single agent with planning.* Trigger: `PARALLEL_INDEPENDENT_SUBTASKS` or `DISTINCT_PERMISSION_BOUNDARIES` or `SEPARATELY_OWNED_DOMAINS`.
4. *Orchestrated multi-agent.* Trigger: `CROSS_ORGANISATIONAL_AGENTS` or `INDEPENDENT_DEPLOYMENT_LIFECYCLES` (this is where A2A earns its place).

**Customisation ladder**
1. *Prompting.* → 2. *Retrieval grounding.* → 3. *Structured output constraint.* → 4. *Fine-tuning* — trigger: `STYLE_OR_FORMAT_CONSISTENCY_UNACHIEVABLE_BY_PROMPTING` or `DOMAIN_VOCABULARY_GAP` or `LATENCY_COST_AT_SCALE`. Explicitly **not** triggered by "the model doesn't know our data" — that is a retrieval requirement, and this is the single most common architectural error in enterprise AI. The pattern contract should state that contra-indication in terms.

**Human oversight ladder**
1. *No review* — informational output, reversible, low consequence. → 2. *Post-hoc sampling review.* → 3. *Human approval before action* — trigger: `IRREVERSIBLE_ACTION` or `FINANCIAL_MATERIALITY` or `REGULATED_DECISION`. → 4. *Human-in-the-loop on every interaction* — trigger: `SAFETY_CRITICAL` or `LEGAL_DETERMINATION`.

Note that these ladders also work in reverse, which is valuable: when a user arrives asking for a multi-agent system, the Advisor can walk *down* the ladder and report which triggers are absent. That is a genuinely useful thing to be told, and no chatbot will tell you.

### 4.2 Assessment of your worked reasoning chain

Your nine-step example is sound reasoning, but it is a *narrative* of reasoning, not a *mechanism*. Three upgrades convert it:

- Steps 1–3 are obligation and requirement derivation — they should be deterministic rule outputs with IDs, not inferences.
- Steps 4–6 are catalog resolution and precedent transfer — they need explicit fit assessment and condition-matching, not "similar requirements → reuse."
- Steps 7–8 are the escalation ladder, made explicit with named triggers and a defined seam for later evolution.

The conclusion is right. The point is to make it *derivable and repeatable*, not merely well-argued once.

---

## Part 5 — How existing solutions should influence recommendations

Yes, uploaded and deployed solutions should become knowledge. This is the asset no external tool can replicate, and it is what makes the Advisor *yours*. But it has to be done carefully, because precedent is the easiest thing in the system to misuse.

### 5.1 What to extract — the Solution Dossier

Extraction must capture the **decision situation**, not just the architecture. An architecture without its conditions is uninterpretable.

**Identity & lifecycle:** ID, owner, business unit, dates, current status, catalog linkage.

**Problem context:** business domain, job to be done, user population and size, interaction modality, data sources and their classification, volumes, criticality tier.

**Obligation profile:** which obligations governed it — data class, residency, regulatory scope, network zone, identity model. *This is the most important retrieval key and the least obvious one.*

**Requirements satisfied:** normalised into the same signature vocabulary used at Stage 3. Without shared vocabulary, precedent matching degrades to topic similarity.

**Architecture:** patterns used (linked to Pattern Library IDs), components, data flows, trust boundaries, models, integration points, catalog assets consumed (linked by asset ID).

**Decisions made:** the ADR set — each with the decision, the alternatives considered, the rationale, and **the conditions that made it correct**. The conditions are what make a decision transferable.

**Deviation record:** where it departed from enterprise standards and why; whether an exception was granted and whether it expired.

**Evidence class:** see 5.4.

**Operational record:** users, request volume, latency profile, cost band, incident history, eval results, availability, support burden. Sourced from observability and FinOps systems, not self-reported.

**Lessons:** what worked, what failed, what they would do differently, what surprised them. Free text, and the most valuable field in the record.

**Outcome:** did it achieve the business objective? Adopted, partially adopted, abandoned, superseded?

### 5.2 How to represent them

Hybrid, and the split matters:

- **Structured relational record** — everything above that is enumerable. This carries the retrieval filters and the decision-relevant facts. The majority of the value lives here.
- **Narrative chunks + embeddings** — problem description, lessons, decision rationale. Used only for fuzzy "have we faced something like this?" matching.
- **Graph edges** — `Solution → uses → Pattern`, `Solution → consumes → Asset`, `Solution → governed-by → Obligation`, `Solution → supersedes → Solution`, `Decision → rejected → Alternative`, `Team → owns → Solution`. Reuse and impact questions are traversal questions, not similarity questions: *"what else consumes MCP-014 and under what data class?"* is a join, not a search.

### 5.3 How to find similar solutions

Similarity must be **multi-dimensional and weighted toward obligations**, in this order:

1. **Obligation profile match** — same data class, residency, regulatory scope. A benefits assistant and a claims assistant are architecturally closer to each other than either is to a marketing content generator, despite topical distance, because they inherit the same PHI-driven constraints. Topic-only similarity search gets this exactly backwards.
2. **Requirement signature overlap** — same normalised requirements (attribution required, per-user authorisation, corpus scale class).
3. **Solution class match.**
4. **Interaction and action profile** — read-only versus mutating, synchronous versus batch.
5. **Narrative similarity** — vector search, used last, as a recall net for things the structured filters missed.

Retrieve broadly, then let the analysis stage *explain the divergences*. A precedent that differs in an important way is often more useful than a close match, because it marks a boundary.

### 5.4 Distinguishing production from POC

Do not trust self-declared status. Derive an **evidence class** from observable signals:

| Class | Signals required |
|---|---|
| **Proven-in-production** | Named owner; real user population over 90+ days; monitoring in place; eval suite present; security review passed; incident history exists (even if empty); listed as supported in Catalog |
| **Production-limited** | Deployed to production but narrow population, or missing eval/monitoring |
| **Pilot** | Real users, time-boxed, no support commitment |
| **Prototype/POC** | No real users, or no security review, or no owner |
| **Abandoned** | Was deployed, no longer in use — **retained deliberately** |
| **Superseded** | Replaced by a named successor |

Rules that follow:

- Only `Proven-in-production` precedents may be cited as **transferable decision evidence**.
- `Pilot` and `POC` may be cited as **feasibility evidence** only, explicitly labelled — "we have tried this; it has not been operated at scale."
- `Abandoned` and `Superseded` are cited as **hazard evidence**, and are among the highest-value records in the store. "Three teams have attempted a GraphRAG approach here; two were abandoned for maintenance cost" is exactly the kind of institutional memory that justifies the whole system.
- **Recency decay:** a production precedent from four years ago is weaker evidence than one from last year, and must be flagged as potentially predating current platform capability.

### 5.5 Preventing blind copying

Five mechanisms, all necessary:

1. **Condition matching.** A precedent decision is transferable *only if the conditions recorded in its ADR hold in the current problem*. The record must state which conditions held, which did not, and what follows. If conditions are not recorded, the decision is not transferable — only the fact of feasibility is.
2. **Precedent is evidence, never a template.** Architecturally, precedent enters at Stage 9, *after* pattern admissibility (Stage 8) — so patterns are selected on their own merits and precedent then confirms, warns, or informs. A precedent may not introduce a pattern that Stage 8 ruled contra-indicated; it can only prompt a flagged re-examination.
3. **Mandatory divergence statement.** Every precedent finding must record where the current problem *differs*. An LLM that cannot articulate a difference has not analysed the precedent.
4. **Staleness check.** If a precedent's architecture depends on assets that are now deprecated, or predates a platform capability that would change the decision, flag it. Copying a 2023 architecture forward is how organisations calcify.
5. **Outcome weighting.** A precedent that was architecturally elegant but abandoned for operational cost is *negative* evidence. The store must be able to say "this pattern was used successfully" and "this pattern was used and it went badly" with equal fluency.

### 5.6 Ingestion

Two paths, and both must exist:

- **Automated extraction** from uploaded documents, repositories, and catalog metadata → produces a *draft* dossier. LLM extraction into the schema, with every field carrying a confidence and a source reference.
- **Human confirmation** before a dossier reaches `Proven-in-production` evidence class. The owning architect confirms the decisions, conditions and lessons. Unconfirmed dossiers are usable at lower evidence class only.

This is not bureaucratic friction for its own sake; the thing that destroys precedent-based systems is silent quality decay in the precedent store.

---

## Part 6 — Pattern applicability reasoning

### 6.1 The mechanism

Pattern selection runs as **contract evaluation over normalised requirement signatures**, not semantic matching over prose. The semantic work happens once, in Stage 3, under schema constraint and with source spans recorded. After that, everything is symbolic and auditable.

For each pattern, the evaluation asks four questions in order:

1. **Are the preconditions satisfiable?** If a pattern requires a maintained entity graph and none exists and none is planned, it is conditional at best.
2. **Is any contra-indication present?** Contra-indications are checked before indications, because disqualification is cheaper and safer than qualification. If `FRESHNESS_REQUIRED: hourly` is present, fine-tuning-as-knowledge-injection is contra-indicated regardless of how many indications also match.
3. **Are indications present?** Which specific requirement signatures trigger it, and are they mandatory or optional requirements?
4. **Is the complexity justified?** Consult the escalation ladder. Is the trigger for this rung present? If not, `UNNECESSARY`.

The output is a verdict *per pattern* with named evidence. The library is small enough that you evaluate all of it — no retrieval, no recall risk.

### 6.2 Which patterns can be combined

Composition is governed by typed relations in the pattern records:

- `requires` — hard dependency. Agentic RAG requires retrieval and tool invocation.
- `subsumes` — the superior pattern already provides the inferior. Agentic RAG subsumes single-pass RAG; listing both is a modelling error and looks amateurish in output.
- `composes-with` — independent and complementary. Guardrails compose with everything. HITL composes with any action pattern.
- `conflicts-with` — genuinely incompatible in the same flow.
- `redundant-with` — both address the same requirement; choosing both is waste, not defence. Fine-tuning for domain knowledge alongside RAG for the same corpus, for instance.
- `escalates-to` / `degrades-to` — ladder relations, which also define the **evolution seams**.

A structural validator applies these before any candidate is presented. A candidate containing both a pattern and something it subsumes, or two `conflicts-with` patterns, is rejected as incoherent — this is a deterministic check, not a matter of the LLM being careful.

### 6.3 Which patterns are cross-cutting and near-always required

Distinguish **solution patterns** (RAG, agents, event-driven, multi-agent) from **assurance patterns**. Assurance patterns are not optional design choices in an enterprise context; they are obligations that patterns *impose*:

- **Guardrails** — input/output filtering, injection defence, PII redaction. Required whenever untrusted input meets a model, which is essentially always. Threat mapping drawn from the OWASP LLM Top 10 curation.
- **Evaluation** — required for any pattern whose output quality is not deterministically verifiable. If you cannot measure whether it is getting worse, you cannot operate it.
- **Observability** — trace, cost, latency, token, tool-call and retrieval logging, with the PHI-safe logging obligation applied.
- **Authorisation propagation** — required whenever retrieval or actions touch permissioned data. Not a feature; a structural property of the retrieval layer.
- **Human oversight** — per the oversight ladder.

Treating these as patterns to be *considered* is a mistake. They should appear as `REQUIRED` verdicts derived from obligations, so security-by-design is mechanical rather than dependent on someone remembering. This is a large part of what makes the output feel like enterprise architecture rather than a blog post.

### 6.4 Enterprise-production appropriateness

Each pattern carries a maturity rating, and the rating gates what the Advisor may recommend without qualification:

- **Proven** — multiple internal production precedents; recommendable directly.
- **Emerging** — external evidence, limited internal precedent; recommendable with a named pilot scope, an exit criterion, and a fallback.
- **Experimental** — recommendable only as an explicitly labelled exploration track, never on the critical path of a production commitment.

Maturity is *organisation-specific* and updates from the Precedent Store. A pattern that is industry-standard but has failed twice internally is not "proven" here, and saying so is precisely the value the system adds over a general-purpose model.

---

## Part 7 — The Catalog ↔ Knowledge relationship

### 7.1 The bridge is the capability requirement

The two planes must not know about each other. They are coupled only through a shared **capability taxonomy** — a controlled vocabulary of abstract, vendor-neutral capabilities.

- **Pattern records** declare the capabilities they *require*.
- **Catalog assets** are annotated with the capabilities they *provide*.
- **Obligations** map to capabilities they *mandate*.
- The Decision Kernel derives a Capability Requirement Set from patterns and obligations, then asks the Catalog to resolve it.

Neither side needs to change when the other does. Add a new MCP server: annotate it, and it becomes discoverable for every relevant future recommendation without touching the reasoning. Add a new pattern: declare its capability needs, and it resolves against the existing catalog automatically.

**This taxonomy is the most important data modelling decision in the project.** Get it wrong and everything else degrades into string matching. Keep it abstract — `permission-aware document retrieval`, not `Azure AI Search integration`. The vendor-neutrality of your recommendations is a direct consequence of the abstraction level of this vocabulary.

### 7.2 The interaction, concretely

Your example is the right one. Made mechanical:

1. **Knowledge:** requirement signatures `ENTERPRISE_PRIVATE_DATA` + `ATTRIBUTION_REQUIRED` + `PER_USER_AUTHORISATION` → Pattern `RAG-GROUNDED-QA` verdict `REQUIRED`.
2. **Derivation:** the pattern declares required capabilities `CAP-RETRIEVAL-PERMISSION-AWARE`, `CAP-CITATION-SPAN`, `CAP-CHUNK-INDEX`; obligations add `CAP-AUDIT-SUBJECT-TRACE`, `CAP-PHI-SAFE-LOGGING`.
3. **Catalog resolution:** `CAP-RETRIEVAL-PERMISSION-AWARE` → asset `COMP-RAG-07` (approved, supported, PHI-approved, functional fit high, integration fit high). `CAP-CHUNK-INDEX` over the HR document store → `MCP-HR-DOCS-03` (provides authenticated access with identity propagation).
4. **Sourcing:** both resolve at `Reuse`. `CAP-CITATION-SPAN` resolves partially — `COMP-RAG-07` returns document-level references, not span-level. Sourcing outcome: `Extend`, with the delta as a named build item.
5. **Record:** the recommendation now states *use COMP-RAG-07 and MCP-HR-DOCS-03, extend COMP-RAG-07 for span-level citation*, and every element of that sentence traces to a specific derivation.

### 7.3 Directionality and the anti-bias rule

Information flows **Knowledge → capability requirements → Catalog**. It flows back only as *resolution results*, never as pattern suggestions. The invariant from Part 1 applies: an asset may only enter an architecture as the resolution of an independently derived capability requirement.

There is one legitimate feedback edge: if a mandatory capability has no resolution, no viable buy option and no feasible build within the constraint envelope, that fact can render a pattern `CONDITIONAL` or eliminate a candidate at Stage 13. That is availability affecting *feasibility*, which is legitimate. It is not availability affecting *desirability*, which is the bias you must prevent.

### 7.4 What the Catalog must expose

For the Advisor to reason properly, "we have a RAG component" is not enough. The Catalog MCP should expose, per asset: capability annotations, lifecycle status (supported / deprecated / sunset date), support model and owning team, **compliance posture per data class**, deployment topology and network zone, consumption model and cost basis, capacity and SLA, current consumers, dependency graph, and integration surface.

Where the Catalog cannot yet provide these, the Advisor should say so and lower its confidence — not fill the gaps with plausible assumptions. Missing catalog metadata is itself an actionable finding, and the Advisor is a very effective forcing function for improving catalog quality.

---

## Part 8 — Build / Reuse / Buy / Compose reasoning

### 8.1 The precedence ladder

Evaluated per capability requirement. **Burden of proof increases as you descend** — the further down you go, the more explicit justification is required, and the justification must name the rejected higher option.

**1. Reuse** — an existing asset satisfies the capability across all six fit dimensions.
*Requires:* functional fit, compliance fit for this data class, integration feasibility, operational capacity, healthy lifecycle status, consumable access.
*Blockers:* deprecated or sunsetting asset; not approved for this data class; owning team has no capacity; SLA below requirement.

**2. Compose** — no single asset fits, but a combination does, with only integration work between them.
*Requires:* interfaces are compatible; the composition does not create an unowned seam; combined operational profile meets requirement. Record the integration cost honestly — composition is frequently sold as free and is not.

**3. Extend** — an existing asset covers most of the capability; the delta is additive and does not fork the asset.
*Requires:* the owning team accepts the contribution, or the extension is genuinely external (plugin, adapter, configuration). **Blocker:** if the extension would fork the asset, this is not Extend — it is Build, and must be honestly labelled as such.

**4. Buy** — no internal asset; the capability is commodity, non-differentiating, and a mature market exists.
*Requires:* a data-handling posture compatible with the obligation set (this eliminates many vendors outright in PHI contexts); acceptable exit cost and portability; procurement lead time compatible with the timeline; total cost of ownership including integration, not licence price.
*Note:* buying is frequently the right answer for guardrails, evaluation tooling, observability and model serving — the assurance layer — and is under-recommended because these feel like plumbing.

**5. Build** — no fit, or the capability is genuinely differentiating.
*Requires:* an explicit statement of why each higher option was rejected; an assessment of who will operate it; and a decision on whether it should become a catalog asset for others.

**6. Defer** — the capability is not required in the current increment. A legitimate and under-used outcome. Must record the seam that keeps it addable later.

### 8.2 Reuse is not free — say so

The most common failure of enterprise reuse mandates is treating reuse as costless. The Advisor should surface the real costs alongside the recommendation:

- **Coupling and roadmap dependency** — you inherit another team's priorities and release cadence.
- **Blast radius** — a change to a shared asset affects every consumer, including you.
- **Fit compromise** — accepting an 80% fit means designing around the missing 20% forever.
- **Capacity contention** — shared assets have shared limits.

Reuse should still be the default. But an Advisor that presents reuse as obviously correct in all cases will lose credibility with senior engineers the first time it recommends reusing something painful. Naming the cost is what makes the recommendation trustworthy.

### 8.3 When Build is justified despite an existing capability

The Advisor should accept, and require evidence for, these justifications:

- The existing asset is deprecated or has a published sunset date.
- The existing asset is not approved for the required data class and approval is not on its roadmap.
- The capability is genuinely differentiating to the business.
- Latency, scale or availability requirements demonstrably exceed the asset's SLA (with the SLA cited).
- The owning team cannot support additional consumers within the timeline (with that statement attributed).

It should reject, and say so plainly, these justifications:

- Preference for a different technology stack.
- "It would be faster to write it ourselves" without a comparison of the integration effort.
- Unfamiliarity with the existing asset.
- Aesthetic disagreement with the existing design.

An Advisor willing to push back on a team that wants to build something that already exists is more valuable than one that generates architectures. That is the behaviour that saves real money, and it is where the portfolio-level ROI of the whole platform sits.

---

## Part 9 — Alternatives

### 9.1 The rule for generating them

**An alternative is legitimate only when it represents a different resolution of a genuine tension in the problem.** Not a different vendor, not a different topology, not variety for its own sake.

A tension exists when two Class B objectives cannot both be maximised and the problem does not declare which wins. The real axes:

- **Time-to-market vs. completeness** — ship a narrower scope sooner, or the full capability later.
- **Cost vs. latency/quality** — smaller model with heavier retrieval, or larger model with simpler retrieval.
- **Reuse vs. autonomy** — depend on a shared asset and its roadmap, or own it and pay for it.
- **Control vs. operational burden** — self-hosted versus managed.
- **Incremental vs. target** — the seam-preserving first step, or building for the known end state now.
- **Build vs. buy** — where both are genuinely viable.

The generation test: *would a competent architect, given a different priority ordering, reasonably choose the other option?* If no, it is not an alternative.

### 9.2 When NOT to generate alternatives

Suppress alternatives when:

- **Obligations eliminated everything else.** Compliance is not a preference. If PHI handling leaves one viable topology, presenting alternatives manufactures a false choice and invites someone to pick the non-compliant one.
- **One option dominates** on every axis that differs.
- **The difference is below the decision threshold** — it would not change what the team does next week.
- **The difference is implementation detail**, correctly deferred to the delivery team. The Advisor should not pick your vector store when three approved options are equivalent for this problem; it should say that and hand the choice down.
- **The problem is underspecified** in the axis that would distinguish them. Then the right output is a question, not two architectures.

Cap at three total (one recommended, two alternatives). More than that is not thoroughness; it is an abdication of the advisory role.

### 9.3 What each alternative must state

1. **The governing priority** — "choose this if time-to-market dominates."
2. **What is given up** — concretely, not hedged.
3. **The switching cost** — what it costs to move from this to the recommended option later, which is often the decisive fact.
4. **The revisit trigger** — the observable condition under which this choice should be reconsidered.

### 9.4 Rejected options are a separate, mandatory section

Distinct from alternatives. This is the list of things considered and *eliminated*, with the eliminating rule and evidence. GraphRAG rejected — no relationship-traversal requirement. Multi-agent rejected — single permission boundary, single domain. Fine-tuning rejected — contra-indicated by freshness and attribution requirements.

Architects judge advice by what it declined to recommend. Showing the eliminations is also the strongest defence against the reasonable suspicion that the system simply pattern-matched to whatever is fashionable.

---

## Part 10 — Evidence and explainability

### 10.1 The Decision Graph

The Decision Record is a typed graph, built incrementally, one stage at a time. Node types:

`Utterance` · `Requirement` · `Assumption` · `Obligation` · `SolutionClass` · `CapabilityRequirement` · `PatternVerdict` · `PrecedentFinding` · `AssetResolution` · `Gap` · `SourcingDecision` · `Candidate` · `Elimination` · `Tradeoff` · `Decision` · `Risk` · `OpenQuestion`

Edge types:

`derived-from` · `supports` · `contradicts` · `eliminates` · `mandates` · `resolves` · `satisfies` · `precedent-for` · `assumes` · `overrides`

Every node carries: ID, statement, type, **provenance**, confidence class, stage of creation, and the knowledge-version snapshot it was created under.

### 10.2 Provenance types and the load-bearing rule

Provenance is typed, and the type determines what the claim may be used for:

| Type | Example | May support a decision? |
|---|---|---|
| `USER_STATED` | span from the request | Yes |
| `POLICY_RULE` | rule ID + version | Yes, binding |
| `CATALOG_FACT` | asset ID + query timestamp | Yes |
| `PRECEDENT` | solution ID + evidence class | Yes, weighted by class |
| `PATTERN_CONTRACT` | pattern ID + version | Yes |
| `EXTERNAL_REFERENCE` | curated source + review date | Supporting rationale only |
| `SERVICE_DERIVED` | classification service response | Yes, binding |
| `MODEL_INFERENCE` | LLM judgement | **Only if converted to a stated Assumption** |

**The load-bearing rule:** if removing a claim would change the recommendation, and its provenance is `MODEL_INFERENCE`, it must be surfaced as an explicit Assumption in the output — visible, challengeable, and listed among the open questions. It may not silently support a decision.

This is the mechanism that prevents the LLM inventing catalog capabilities, existing solutions, policies, patterns or sources. Not prompt instructions — **structure**. Combined with closed-vocabulary generation (the LLM may only reference IDs supplied to it) and the Stage 15 validator (unresolvable ID is a hard failure), invention is structurally blocked rather than discouraged.

### 10.3 Explanation is projection, never regeneration

"Why did you recommend this?" is answered by **traversing the graph**, not by asking the model to explain itself. A model asked to justify a prior output will produce a plausible justification whether or not it reflects the actual derivation. That is post-hoc rationalisation, and it is the failure mode that destroys trust in these systems the first time someone checks.

The explanation chain you described falls out naturally:

```
Utterance span
  → Requirement REQ-04 (attribution required)
    → PatternVerdict PAT-RAG = REQUIRED
      → CapabilityRequirement CAP-CITATION-SPAN
        → AssetResolution COMP-RAG-07 (partial fit: document-level only)
          → SourcingDecision: EXTEND
            → Decision DEC-03 (build span-level citation extension)
              ← supported by PrecedentFinding SOL-041 (did the same, 6 weeks)
              ← constrained by Obligation OBL-PHI-02
```

The LLM's role is to render that traversal as readable prose. It does not decide the content.

### 10.4 Counterfactual explanation

The highest-value explainability feature, and one almost nobody builds: **"what would change this recommendation?"**

Computed by traversal — identify the claims with the highest out-degree into decisions, then report what a different value would produce:

- "If the corpus were under 200 pages and static, the retrieval layer would be unnecessary."
- "If PHI were not present, three additional model options and two managed services become viable, and the compliance path shortens by an estimated 6–8 weeks."
- "If actions were read-only, the human approval gate and the action gateway would not be required."

This transforms the Advisor from an oracle into a thinking tool. It is also how you convert a sceptical senior architect into a user, because it lets them interrogate the boundaries of the advice rather than accept or reject it wholesale.

### 10.5 Confidence, expressed honestly

No composite scores. Use categorical confidence with a stated basis:

- **Established** — obligation-driven or precedent-backed with production evidence.
- **Reasoned** — derived from pattern contracts, no direct internal precedent.
- **Provisional** — depends on a stated assumption that has not been confirmed.
- **Uncertain** — insufficient information; a question is attached.

Each element of the recommendation carries one. A recommendation whose core is `Provisional` should say so at the top, not bury it.

---

## Part 11 — Role of the LLM versus the system

### 11.1 The division

**The LLM is responsible for language and judgement under supervision:**

- Interpreting natural language into normalised schemas
- Recovering the job to be done from a solution-shaped request
- Detecting ambiguity and generating clarifying questions
- Proposing capability requirements beyond the deterministic mappings
- Analogical reasoning over precedents, including articulating divergence
- Composing candidate architectures within structural rules
- Articulating tradeoffs
- Rendering the Decision Record as readable prose and diagrams
- Adversarial critique of the draft recommendation

**The system is responsible for facts, rules and record:**

- All retrieval — catalog, precedent, pattern, policy
- Obligation evaluation
- Capability derivation from obligations
- Asset existence, lifecycle status and compliance-posture validation
- Structural coherence checking of candidates
- All elimination gates
- Sourcing precedence
- Priority ordering and selection rules
- Evidence ledger maintenance
- Grounding validation
- Versioning, reproducibility and audit

### 11.2 Five boundary principles

1. **The LLM may propose; it may never assert a fact about the enterprise.** Every enterprise fact comes from a system of record. The LLM's statements about what exists are hypotheses to be resolved.
2. **Every LLM call has a schema contract.** No free prose at a decision point. Prose is permitted only in the final rendering, over already-decided content.
3. **Elimination is deterministic; differentiation is reasoned.** The LLM never removes an option. It explains why the surviving options differ.
4. **Many small supervised calls beat one large one.** Each stage is a separate call with its own input, schema, and validation. This is testable, debuggable, and individually improvable — a single mega-prompt is none of those things.
5. **Anything the enterprise can be held accountable for is system-owned.** Compliance, availability commitments, cost claims, asset existence. If it could appear in an audit, a rule owns it.

### 11.3 Two LLM roles worth adding

**The Critic.** A separate pass, with no stake in the draft, given the recommendation and the Decision Record and asked: what is wrong with this? What did it miss? What would a sceptical principal architect attack? Critic findings become explicit risks and open questions. This is cheap and disproportionately effective — self-critique in a separate call with a separate framing catches things the generating call will not.

**The Interpreter, run redundantly.** Stage 2 and Stage 3 errors propagate through everything downstream. Run interpretation independently more than once and reconcile; disagreement between runs is a reliable signal of genuine ambiguity in the request, and should be routed into the Clarification Set rather than averaged away.

---

## Part 12 — Knowledge architecture

The rule: **authority and volatility determine storage.** Not fashion.

### 12.1 Relational / structured — the backbone

This carries the majority of the system, and it is worth stating plainly that **most of this is a data modelling problem, not a retrieval problem.**

Holds: capability taxonomy; pattern registry and applicability contracts; requirement signature vocabulary; solution class taxonomy; solution dossiers (structured fields); obligation→capability mappings; sourcing decision history; evidence ledger; recommendation history; catalog asset annotations (as a linkage table, not a copy of the truth).

Why: everything above must be enumerable, queryable exactly, versioned, and diffable. Recommendations must be reproducible against a knowledge snapshot. You cannot get that from a vector index.

### 12.2 Documents

Holds: pattern rationale, ADR narratives, lessons-learned text, curated external reference excerpts, design documents.

Purpose: human authorship and reading, and the raw material for retrieval. These are read *by people* to validate the structured records, which is important — the structured contracts must be traceable to a human-written justification or they become unmaintainable folklore.

### 12.3 Vector search — narrowly

Use only where the query is genuinely fuzzy natural language over an open set:

- Precedent narrative similarity (as the *last* filter, after structured obligation and requirement filtering)
- Lessons-learned retrieval
- ADR search
- Document retrieval during dossier ingestion

**Do not use for:** patterns (small closed set — enumerate them), policy (never — recall failure equals compliance failure), catalog (structured query against a live system of record), capability taxonomy (closed vocabulary).

The instinct to embed everything is the most expensive mistake available here, because it converts precise, auditable lookups into approximate ones and calls it intelligence.

### 12.4 Knowledge graph — earn it, don't assume it

A graph *is* justified eventually, because the highest-value queries are traversals: impact analysis ("what breaks if MCP-014 is deprecated?"), reuse discovery ("what else solves this under PHI?"), drift detection, duplicate-effort detection across the portfolio, pattern co-occurrence analysis.

But: **start with relational join tables expressing the same relations.** The relations are what matter, not the storage engine. Promote to a graph database only when you observe real queries needing variable-depth traversal or path-finding and the SQL becomes unmanageable. That is a real threshold and you will know when you cross it — probably somewhere north of 100 solutions with dense asset linkage.

Adopting a graph database on day one, before you have the relations populated or the queries identified, is the classic way to spend six months on infrastructure and ship nothing.

### 12.5 Rules engine

Holds: policy evaluation, obligation derivation, admissibility gates, elimination gates, sourcing precedence, sufficiency-gate criticality rules.

Requirements: versioned, individually testable, human-readable, with each rule traceable to an owning policy or standard. If your architects cannot read a rule and confirm it is correct, they will not trust the eliminations, and the eliminations are the product.

### 12.6 APIs and MCP

Live integration, never mirrored as truth: the AI Catalog MCP; data classification service; IAM/identity; model registry and approval status; approved technology registry; FinOps/cost; observability and eval results; ticketing/ADR repository.

The principle: **never fork a system of record.** Cache with short TTL for performance, but revalidate before any fact appears in a recommendation. A stale reuse recommendation pointing at a decommissioned asset is the fastest way to lose an architecture team's trust permanently.

### 12.7 Summary

| Storage | Carries | Do not use for |
|---|---|---|
| Relational | Taxonomies, contracts, dossiers, ledger, decisions | Fuzzy problem matching |
| Documents | Human rationale, narratives, references | Anything decision-binding without structured extraction |
| Vector | Precedent narrative, lessons, ADR search | Patterns, policy, catalog |
| Graph (later) | Traversal and impact queries | Anything relational already answers |
| Rules | Obligations, gates, precedence | Anything requiring interpretation of intent |
| API/MCP | Live authoritative facts | Anything needing reproducibility without snapshotting |

---

## Part 13 — Complete worked example

**Request:** *"Build an AI assistant that answers employee health benefits questions using private enterprise data, provides citations, protects PHI/PII, reuses existing enterprise capabilities, and eventually supports actions through tools."*

All IDs below are illustrative.

### Stage 1 — Framing
Request type: `NEW_BUILD`. Scope: `APPLICATION`. Domain: `HR / Benefits`. Requester: HR Technology. Default policy scope inherited: `HR-EMPLOYEE-DATA`.

### Stage 2 — Problem interpretation
Job to be done: employees cannot reliably self-serve answers about health benefits; HR fields repetitive enquiries; answers must be trustworthy because employees make financial and medical decisions from them.
Actors: all employees (self), HR support (escalation).
**Solution assumptions detected in the request:** "assistant" presumes conversational modality; "tools" presumes agentic action. Both flagged for later challenge — neither is a requirement, both are proposed solutions.

### Stage 3 — Requirement extraction

| ID | Signature | Source |
|---|---|---|
| REQ-01 | `ENTERPRISE_PRIVATE_DATA` | "using private enterprise data" |
| REQ-02 | `ATTRIBUTION_REQUIRED: span-level` | "provides citations" |
| REQ-03 | `SENSITIVE_DATA: PHI, PII` | "protects PHI/PII" |
| REQ-04 | `REUSE_PREFERENCE: strong` | "reuses existing enterprise capabilities" |
| REQ-05 | `ACTION_REQUIRED: deferred` | "eventually supports actions" |
| REQ-06 | `INTERACTION: conversational, synchronous` | "assistant" |
| REQ-07 | `USER_POPULATION: all employees` | inferred — **Assumption** |
| REQ-08 | `PER_USER_AUTHORISATION` | derived from REQ-03 + benefits data being individually scoped |

**Assumption Register:** ASM-01 population is enterprise-wide; ASM-02 corpus is benefits plan documents plus policy documents; ASM-03 answers are informational, not benefits determinations.

**Clarification Set:** corpus size and update cadence; whether answers may reference an individual's own enrolment data (materially changes the architecture); what the eventual actions are; expected query volume.

### Stage 4 — Sufficiency gate
**Decision-critical gap identified:** *does the assistant answer from an individual's personal enrolment record, or only from general plan documents?* This appears in the indication set of three patterns and changes the PHI boundary entirely. Rule fires: `HALT-CLARIFY` on this one question, `PROCEED-WITH-QUESTIONS` on the rest.

*This is a stage your original design would have skipped, and it is the question that most changes the answer.* Proceeding on the general-plan-documents reading, with personal-data access marked as a defined evolution step.

### Stage 5 — Obligation resolution (deterministic)

| ID | Obligation | Source |
|---|---|---|
| OBL-01 | PHI-approved processing boundary required | Classification service: benefits corpus contains PHI-adjacent plan data |
| OBL-02 | No PHI in prompt/response logs; PHI-safe telemetry | POL-DATA-014 |
| OBL-03 | Data residency: in-region processing | POL-RES-002 |
| OBL-04 | Approved model list only | POL-AI-007 |
| OBL-05 | Caller identity propagated to all data access; no service-account-wide retrieval | POL-SEC-021 |
| OBL-06 | Audit log with subject traceability, 7-year retention | POL-AUD-003 |
| OBL-07 | Human review gate for any benefits-affecting action | POL-HR-011 |
| OBL-08 | AI system registration + pre-deployment eval evidence | POL-AI-001 |
| OBL-09 | Prompt-injection and output-filtering controls | OWASP-LLM-01/02 via control library |

Control framework mapping generated automatically as an output artefact.

### Stage 6 — Solution class
`GROUNDED_KNOWLEDGE_ASSISTANT` (primary), with `TRANSACTIONAL_AGENT` as a declared future class.
Rejected: `DECISION_SUPPORT` (no determination being made — per ASM-03); `DOCUMENT_PROCESSING_PIPELINE` (interactive, not batch).

### Stage 7 — Capability requirements

| ID | Capability | Derived from | Status |
|---|---|---|---|
| CAP-01 | Permission-aware document retrieval | REQ-01, REQ-08, OBL-05 | Mandatory |
| CAP-02 | Span-level citation resolution | REQ-02 | Mandatory |
| CAP-03 | Document ingestion & chunk indexing | REQ-01 | Mandatory |
| CAP-04 | PHI-safe logging & telemetry | OBL-02 | Mandatory |
| CAP-05 | Audit logging with subject trace | OBL-06 | Mandatory |
| CAP-06 | Input/output guardrails, injection defence | OBL-09 | Mandatory |
| CAP-07 | Grounded-answer evaluation harness | OBL-08 | Mandatory |
| CAP-08 | Approved model serving, in-region | OBL-03, OBL-04 | Mandatory |
| CAP-09 | Conversational session management | REQ-06 | Mandatory |
| CAP-10 | Action authorisation with approval workflow | REQ-05, OBL-07 | **Deferred** |
| CAP-11 | Tool invocation gateway | REQ-05 | **Deferred — seam required** |

### Stage 8 — Pattern verdicts

| Pattern | Verdict | Reason |
|---|---|---|
| Grounded RAG (hybrid retrieval + rerank) | `REQUIRED` | REQ-01 + REQ-02 + corpus exceeds context; ladder rung 3 trigger present |
| Guardrails | `REQUIRED` | OBL-09 |
| Evaluation harness | `REQUIRED` | OBL-08 |
| Observability (PHI-safe) | `REQUIRED` | OBL-02, OBL-06 |
| Authorisation propagation | `REQUIRED` | OBL-05 |
| Human-in-the-loop | `CONDITIONAL` | Not required for informational Q&A; **required** at the action increment per OBL-07 |
| Constrained tool calling | `CONDITIONAL` | Triggered only at the action increment (REQ-05) |
| Agentic RAG | `UNNECESSARY` | No `MULTI_HOP_QUERIES` or `QUERY_AMBIGUITY_HIGH` signature present. Revisit trigger recorded: if eval shows single-pass retrieval failing on comparative plan questions |
| GraphRAG | `CONTRA-INDICATED` | No `RELATIONSHIP_TRAVERSAL_REQUIRED`; imposes a standing entity-graph maintenance obligation with no triggering requirement |
| Multi-agent | `CONTRA-INDICATED` | Single domain, single permission boundary, single owning team. No `SEPARATELY_OWNED_DOMAINS` or `INDEPENDENT_DEPLOYMENT_LIFECYCLES` |
| Fine-tuning (knowledge injection) | `CONTRA-INDICATED` | Contra-indicated by `ATTRIBUTION_REQUIRED` and corpus volatility; does not provide grounding or citation |
| Event-driven architecture | `UNNECESSARY` for query path; `APPLICABLE` for the ingestion pipeline (document change → reindex) |
| Model routing | `UNNECESSARY` | No evidence of cost or latency pressure at projected volume; revisit at scale |
| A2A | `CONTRA-INDICATED` | No cross-organisational agent interaction |

### Stage 9 — Precedent findings

**SOL-041 — Employee Policy Assistant.** Evidence class: `Proven-in-production` (14 months, 8,000 users). Obligation profile match: high (same residency, same identity model, PII but not PHI — **divergence noted**).
Transferable decisions: hybrid retrieval with reranking over HR document corpus; identity propagation via MCP rather than service account; document-level citation proved insufficient — they retrofitted span-level extraction at significant cost.
**Lesson (highest value in the finding):** *retrofitting span-level citation was six weeks of unplanned work; design it in from the start.* This directly justifies the Extend decision at Stage 11 rather than accepting document-level citation initially.
Divergence: SOL-041 did not handle PHI; its logging configuration is not sufficient here.

**SOL-019 — Claims Query Prototype.** Evidence class: `Abandoned`. Attempted GraphRAG over benefits and claims entities. Abandoned after 5 months — graph maintenance cost exceeded retrieval benefit; entity resolution across source systems was unreliable.
**Used as hazard evidence supporting the GraphRAG contra-indication.** Without this record, GraphRAG looks superficially attractive for a benefits domain with plan/coverage/dependant relationships.

**SOL-063 — HR Service Desk Agent.** Evidence class: `Production-limited`. Relevant to the deferred action increment: their action gateway design and approval workflow are reusable, and their lesson on scoping tool permissions per action type transfers.

### Stage 10 — Catalog resolution

| Capability | Resolution | Fit |
|---|---|---|
| CAP-01 | `COMP-RAG-07` (Enterprise Retrieval Component) | Functional: high. Compliance: **PHI-approved**. Lifecycle: supported. Integration: high. **Reuse** |
| CAP-02 | `COMP-RAG-07` | Partial — document-level references only. **Extend** |
| CAP-03 | `MCP-HR-DOCS-03` (HR document store MCP, identity-propagating) | High across all dimensions. **Reuse** |
| CAP-04 | `PLAT-OBS-02` with PHI-safe profile | High. **Reuse (configuration)** |
| CAP-05 | `PLAT-AUDIT-01` | High. **Reuse** |
| CAP-06 | `COMP-GUARD-04` | Functional: high. Note: injection ruleset last updated 9 months ago — **flagged risk** |
| CAP-07 | **GAP** — no approved grounded-answer eval harness in catalog | — |
| CAP-08 | `PLAT-MODEL-GW` (in-region, approved model list) | High. **Reuse** |
| CAP-09 | `COMP-CHAT-02` | High. **Reuse** |
| CAP-10/11 | Deferred; `SOL-063` action gateway noted as future reuse candidate | — |

### Stage 11 — Sourcing decisions

- CAP-01, 03, 04, 05, 08, 09 → **Reuse.**
- CAP-02 → **Extend** `COMP-RAG-07` with span-level citation. Justification: precedent SOL-041 shows retrofit costs six weeks; the extension is additive and the owning platform team has accepted contributions previously. Rejected alternatives named: Reuse-as-is (fails REQ-02), Build new retrieval (rejected — duplicates a PHI-approved asset).
- CAP-06 → **Reuse with remediation task** (ruleset refresh) — recorded as a risk with an owner.
- CAP-07 → **Buy or Build**, flagged as a decision requiring input. Commodity, non-differentiating, mature market exists → **Buy recommended**, subject to vendor data-handling review against OBL-01/03. If procurement lead time exceeds the timeline, Build a minimal harness and record technical debt.
- CAP-10, CAP-11 → **Defer**, with a mandatory seam.

### Stage 12 — Candidates

**Candidate A — Minimum sufficient, reuse-maximal.**
`COMP-CHAT-02` → orchestration → `COMP-GUARD-04` → `COMP-RAG-07` (extended for span citation) → `MCP-HR-DOCS-03` (identity-propagated) → `PLAT-MODEL-GW`. Cross-cutting: `PLAT-OBS-02` (PHI-safe), `PLAT-AUDIT-01`, eval harness (bought). **Action Gateway defined as an interface contract and stubbed** — the seam.

**Candidate B — Agentic RAG from the start.** Adds query planning and iterative retrieval.

**Candidate C — Full target state now.** Adds the action layer, tool gateway, approval workflow and HITL in the first release.

**Candidate D — Build a dedicated retrieval layer.** Independent of `COMP-RAG-07`.

### Stage 13 — Elimination (deterministic)

- **D eliminated.** Gate: sourcing precedence violation. A PHI-approved, supported asset satisfies CAP-01 with high fit; no accepted build justification present. Rule `SRC-PRECEDENCE-01`.
- **B eliminated.** Gate: complexity budget. Agentic RAG's escalation triggers are absent from the Requirement Set; adds cost, latency and eval surface with no requirement justification. Rule `CPX-BUDGET-01`.
- **C eliminated.** Gate: requirement scope. REQ-05 is explicitly deferred (`ACTION_REQUIRED: deferred`); building the action layer now brings OBL-07 approval workflows and expanded PHI exposure into scope with no current requirement. Rule `SCOPE-01`.
- **A survives.**

### Stage 14 — Selection and alternatives

**Recommended: Candidate A.** Grounded enterprise RAG on existing approved components, with identity-propagated retrieval, span-level citation extension, mandated assurance layer, and a defined action seam.

Selection basis: all obligations satisfied; all mandatory requirements sourced; minimum complexity consistent with requirements; maximum reuse; production precedent under a comparable obligation profile.

**Alternative 1 — if time-to-market dominates.** Ship with document-level citation from `COMP-RAG-07` as-is; add span-level in release two. Gives up: citation precision, which SOL-041's lesson says employees will complain about. Switching cost: low if the citation interface is designed for it now. Revisit trigger: if the launch date moves by more than three weeks, take the recommended path instead.

**Alternative 2 — if the action capability is needed within two quarters.** Bring the action gateway and approval workflow forward, reusing SOL-063's design. Gives up: 6–8 weeks on the initial launch and a broader compliance review scope. Revisit trigger: a committed business date for benefits transactions.

*No alternative offered on the retrieval topology* — obligations and requirements leave one viable shape, and manufacturing a choice there would be misleading.

**Rejected options presented:** GraphRAG (contra-indicated, plus SOL-019 hazard evidence), multi-agent (no trigger), fine-tuning (contra-indicated by attribution and freshness), build-own-retrieval (precedence violation), agentic RAG now (complexity budget — with the recorded revisit trigger).

### Stage 15 — Assembly

**Open questions carried forward:** personal enrolment data access (decision-critical, deferred by explicit scope); corpus size and update cadence; eval harness buy-versus-build under procurement timeline; guardrail ruleset currency.

**Risks:** `COMP-GUARD-04` ruleset staleness (owner assigned); `COMP-RAG-07` extension depends on platform team acceptance; PHI classification of the benefits corpus should be confirmed by the data owner before build start.

**Evidence chain, sample:**
```
"Extend COMP-RAG-07 for span-level citation"
  ← REQ-02 (USER_STATED: "provides citations")
  ← CAP-02 (derived: pattern PAT-RAG requires citation resolution)
  ← AssetResolution COMP-RAG-07 partial (CATALOG_FACT, queried 2026-08-17)
  ← SourcingDecision EXTEND (rule SRC-PRECEDENCE-03)
  ← PrecedentFinding SOL-041 (PRECEDENT, Proven-in-production):
      retrofit cost 6 weeks
```

**Counterfactuals offered:**
- If the corpus were static and under context size → retrieval layer unnecessary; direct context injection viable.
- If PHI were confirmed absent → two managed services become viable and the compliance path shortens by an estimated 6–8 weeks.
- If personal enrolment data were in scope → per-record authorisation, a distinct PHI boundary, and a re-run of obligation resolution.

---

## Part 14 — What would make this world-class

Everything above makes the Advisor *correct*. The following make it something an architecture team depends on rather than consults. The distinction matters: a tool that is consulted is used when someone remembers; a tool that is depended upon is in the path of work.

### 14.1 The closed loop — the single biggest differentiator

Almost no organisation does this. **Track what was recommended, what was actually built, and what happened.**

- Link the recommendation to the delivery artefact and then to the deployed solution in the Catalog.
- Record **adherence**: was the recommendation followed, partially followed, or ignored? Where it diverged, why?
- Record **outcome**: did it work? Cost, latency, incidents, adoption, eval results.
- Feed the outcome back into the Precedent Store as evidence, and into pattern maturity ratings.

This creates the flywheel. After two years, the Advisor is not reasoning from vendor reference architectures; it is reasoning from *what has actually worked in this organisation, under these constraints, with these teams*. That is knowledge no external model can have, and it compounds. It is also the honest answer to "why not just use ChatGPT" — because ChatGPT does not know that your last two GraphRAG attempts were abandoned.

Divergence data is especially valuable: when teams consistently ignore a recommendation, either the recommendation is wrong or the knowledge is stale. Both are actionable, and neither is visible without the loop.

### 14.2 Portfolio intelligence

The same data supports questions no single-request advisor can answer, and this is where the financial return actually sits:

- **Duplicate effort detection** — three teams independently building permission-aware retrieval this quarter. Surface it while it is preventable.
- **Reuse candidate promotion** — a component built for one solution that four subsequent requests would have used. Recommend promoting it to a catalog asset, with the demand evidence attached.
- **Capability gap roadmap** — the aggregate of unresolved capability requirements across all recommendations *is* the platform team's backlog, ranked by real demand rather than by advocacy.
- **Pattern adoption and failure trends** — where the organisation is succeeding and where it repeatedly struggles.
- **Constraint friction analysis** — which policies most often eliminate otherwise-good architectures. Sometimes the right response is to change the policy, and this is the only way to see it.

Build the request-level advisor first, but design the data model so this falls out. It will be what justifies the investment to leadership.

### 14.3 Policy-aware, compliant-by-construction output

Ship the compliance artefact *with* the architecture: the obligation set, the control mapping (NIST AI RMF, ISO 42001, OWASP LLM Top 10), the component that owns each control, and the evidence required at review. Pre-fill the security review submission.

When architecture recommendations arrive with the security review 70% complete, adoption becomes self-propelling — teams use it because it saves them the part they hate. This is the most reliable adoption mechanism available to you.

### 14.4 Architecture drift detection

Compare the deployed reality (from Catalog, observability and IaC) against the recommended and approved architecture. Flag divergence: undeclared components, unapproved models, retrieval bypassing authorisation, guardrails disabled, an eval harness that stopped running.

Architecture as a document decays. Architecture as a continuously reconciled model does not. This is what makes it a *governance* capability rather than an advisory one, and it is what gets it funded.

### 14.5 Cost and time as evidenced ranges

Never LLM-guessed. Derive from actual precedent: *"comparable solutions with this pattern set and obligation profile took 11–16 weeks and run at £X–£Y per month at this volume, based on SOL-041 and SOL-052."* With the sample size stated, because a range from two projects is not the same as a range from twenty and pretending otherwise is exactly the false precision you are right to avoid.

### 14.6 The Advisor held to its own standard

If you are recommending eval harnesses, observability and human oversight, the Advisor must have them. This is not symbolism — it is the credibility precondition for the entire product.

- **Golden set regression testing.** Curate 30–50 past problems with architect-validated answers. Every knowledge, rule or prompt change runs against them. Nothing else keeps a system like this from drifting silently as it grows.
- **Architect review workflow.** Recommendations are reviewed, approved, or overridden by a human architect. Overrides are captured with reasons, and recurring overrides become candidates for new rules or corrected pattern contracts. This is the Advisor's own human-in-the-loop, and it is also its primary learning channel.
- **Knowledge versioning and snapshot reproducibility.** Any past recommendation can be re-derived exactly as it was made, and re-run against current knowledge to see what changed.
- **Full observability** of its own reasoning: stage timings, rule firings, LLM call traces, retrieval results.

### 14.7 Explainability as an interactive surface

Not a report. An interrogable model:

- Click any element of the architecture to see its derivation chain.
- Toggle a constraint off and watch the recommendation change.
- Change the priority ordering and see the alternative promoted.
- Challenge an assumption and re-run from that stage.

This converts sceptical senior architects into users faster than any accuracy improvement, because it lets them do their own reasoning with the system rather than accept its conclusion.

### 14.8 Integration into the delivery path

Emit artefacts that become work: ADR drafts for each significant decision, backlog seeds for build items, catalog reuse requests routed to owning teams, security review pre-fill, and a reference to the approved deployment template. A recommendation that ends as a document gets read once. A recommendation that ends as tickets gets built.

### 14.9 Technology-neutral core with a mapping layer

Keep the reasoning in abstract capabilities and patterns; apply the vendor mapping last, from the approved-technology registry. Three benefits: recommendations survive a platform migration; the same engine serves multiple business units with different approved stacks; and the product becomes commercially portable, since the reasoning core is organisation-independent and only the knowledge is not.

### 14.10 Honest negative capability

The rarest and most trust-building behaviour: the Advisor should be able to say

- "This already exists — use SOL-041; here is the gap analysis."
- "I cannot recommend safely without knowing X."
- "This is not an AI problem. Your issue is that the benefits documents contradict each other."
- "This is technically viable but the compliance path is 14 weeks; plan accordingly."
- "Two prior attempts at this failed for the same reason; here is what they hit."

A system that always produces an architecture will produce one when it should not. Build the refusals in deliberately, and evaluate them in the golden set — otherwise they will be optimised away as failures.

### 14.11 What this is *not*, versus "ChatGPT generates an architecture"

| A general model | This system |
|---|---|
| Plausible generic architecture | Architecture grounded in what you actually own |
| Invents capabilities | Structurally cannot reference a non-existent asset |
| No institutional memory | Learns from every solution, including the failures |
| Compliance as prose caveat | Compliance as binding, deterministic elimination |
| Post-hoc rationalisation | Traceable derivation, reproducible |
| Recommends the fashionable | Complexity requires a named trigger |
| No follow-through | Drift detection and outcome feedback |
| Advice | Governance |

---

## Part 15 — Consolidated deliverable

### 15.1 Recommended architecture for the Recommendation Engine
Five planes — Catalog (live inventory, via MCP), Knowledge (patterns, precedents, curated external, advisory), **Policy & Constraint (binding, deterministic — split out from your proposed knowledge layer)**, Decision Kernel (staged pipeline producing a Decision Record), and Interaction. Evidence Ledger is a cross-cutting property of the Decision Record, not a separate store. Governing invariant: *no catalog asset enters an architecture except as the resolution of an independently derived capability requirement.*

### 15.2 Complete reasoning flow
Fifteen stages: Framing → Problem Interpretation → Requirement Normalisation → **Sufficiency Gate** → **Obligation Resolution (moved early)** → Solution Class → Capability Derivation → Pattern Admissibility → Precedent Analysis → **Catalog Resolution (moved late)** → Sourcing Decisions → Candidate Construction → Elimination → Differentiation & Selection → Evidence Validation & Assembly. LLM at the edges, determinism in the middle.

### 15.3 Knowledge architecture
Relational backbone for taxonomies, pattern contracts, dossiers, ledger and decisions. Documents for human rationale. Vector search only for precedent narrative and lessons. Graph relations modelled from day one but stored relationally until traversal demands otherwise. Rules engine for obligations, gates and precedence. Live APIs/MCP for systems of record, never forked.

### 15.4 Role of the AI Catalog MCP
Authoritative live inventory. Answers *"what exists, in what state, approved for what?"* Resolves capability requirements into concrete assets with six-dimension fit. Never initiates pattern selection. Must expose lifecycle, compliance posture, support model, SLA and consumers — existence alone is not decision-grade.

### 15.5 Role of the Knowledge Layer
Advisory. Pattern applicability contracts, precedent dossiers with outcomes, curated external reference material, anti-patterns and lessons. Produces *capability requirements and pattern verdicts*, never asset choices. Its failure mode is a weaker recommendation, which is why it must be kept separate from policy, whose failure mode is a breach.

### 15.6 Role of the LLM
Interpretation, normalisation to schema, ambiguity detection, hypothesis and candidate generation, precedent analogy, tradeoff articulation, narrative rendering, adversarial critique. It proposes; it never asserts an enterprise fact, never eliminates an option, and never decides. Every call is schema-bound and individually testable.

### 15.7 Role of deterministic logic
Obligation evaluation, capability derivation from obligations, sufficiency criticality, pattern contract evaluation, structural coherence validation, all elimination gates, sourcing precedence, priority ordering, grounding validation, versioning and reproducibility. Anything auditable is rule-owned.

### 15.8 Build / Reuse / Buy / Compose
Precedence ladder with rising burden of proof: Reuse → Compose → Extend → Buy → Build → Defer. Six fit dimensions, with compliance fit as a hard filter rather than a partial match. Build requires a named rejected alternative and an accepted justification class. Reuse costs (coupling, blast radius, fit compromise, capacity contention) are stated rather than hidden.

### 15.9 Pattern reasoning
Applicability contracts evaluated over normalised requirement signatures across the entire library — no retrieval, no keyword matching. Five verdicts including explicit rejections. Typed composition relations enforced by a structural validator. Escalation ladders with named triggers as the anti-over-engineering mechanism. Assurance patterns derived from obligations, not chosen.

### 15.10 Existing-solution reasoning
Solution Dossiers capturing the decision situation, not just the architecture. Similarity matched on obligation profile first, narrative last. Evidence classes derived from observable signals, with abandoned solutions retained as hazard evidence. Precedent enters *after* pattern admissibility, transfers only where recorded conditions hold, and must state its divergences.

### 15.11 Alternative reasoning
Generated only where a genuine tension exists and a different priority ordering would flip the choice. Maximum three. Each states its governing priority, what is given up, the switching cost, and the revisit trigger. Suppressed when obligations decide, when one option dominates, or when the difference is implementation detail. "Rejected options" is a separate mandatory section.

### 15.12 Evidence and explainability
Typed Decision Graph with provenance classes. The load-bearing rule: any `MODEL_INFERENCE` claim that supports a decision must surface as a stated Assumption. Closed-vocabulary generation plus a hard-failing grounding validator makes invention structurally impossible. Explanation is graph projection, never regeneration. Counterfactual explanation is the highest-value feature.

### 15.13 Feedback and learning
Recommendation → adherence → deployment → outcome → precedent. Architect override capture as the primary correction channel. Pattern maturity updated from internal production evidence. Golden-set regression testing on every knowledge change. Knowledge versioned and snapshotted for reproducibility. **Learning happens through curated knowledge and rules, not model fine-tuning** — the knowledge must remain human-auditable, and this is a governance system.

### 15.14 Worked example
Part 13, end to end.

### 15.15 MVP recommendation logic

Build in this order. **The data model and the pattern contracts are the product** — resist the pull toward the pipeline plumbing.

**Phase 0 — Vocabulary (the foundation).**
- Capability taxonomy: ~30 abstract capabilities.
- Requirement signature vocabulary: ~40 signatures.
- Solution class taxonomy: ~8 classes.
*Nothing else works if this is wrong. Spend real architect time here.*

**Phase 1 — Knowledge seed.**
- 12–15 pattern records with full applicability contracts, hand-authored by your architects.
- 15–20 hard policy rules, machine-evaluable.
- 10–20 solution dossiers, manual entry acceptable, with evidence class assigned.
- Catalog assets annotated against the capability taxonomy — this requires platform team cooperation and is often the schedule risk.

**Phase 2 — Kernel.**
- All 15 stages, but with simplifications: candidate construction from templated pattern compositions rather than free composition; precedent retrieval structured-filter-only, no vector search yet; alternatives limited to the incremental-versus-target axis.
- **Evidence ledger and grounding validator are in the MVP, not deferred.** They are the differentiator, and retrofitting provenance into a system that did not have it is close to a rewrite.
- Full elimination gates from day one. This is what makes it feel like an architect.

**Phase 3 — Interaction.**
- Clarification dialogue, recommendation presentation with rejected options, derivation chain view, architect review and override capture.

**Explicitly defer:** graph database, live external retrieval, cost and time modelling, drift detection, portfolio analytics, automated dossier extraction, multi-tenancy, counterfactual UI.

**MVP success criterion:** for ten real past problems, three senior architects agree the recommendation is *defensible* — not necessarily what they would have chosen, but something they would not have to correct. Defensibility is the right bar. Optimality is not achievable and chasing it will mislead you.

### 15.16 What to add later for world-class / commercial

**Next (6–12 months):** closed outcome loop; automated dossier extraction with human confirmation; vector-based precedent narrative retrieval; evidenced cost and time ranges; counterfactual explanation; ADR and backlog emission; compliance artefact generation.

**Then:** graph-backed traversal and impact analysis; portfolio intelligence (duplicate detection, reuse promotion, capability gap roadmap); architecture drift detection; constraint friction analysis; curated external knowledge refresh pipeline.

**Commercial:** technology-neutral core with pluggable approved-stack mapping; multi-tenant knowledge isolation with optional anonymised cross-tenant pattern learning; policy pack templates per regulatory regime (HIPAA, GDPR, DORA, EU AI Act); customer-authorable pattern libraries; benchmark reporting against anonymised peer data.

---

## Closing note

The instinct that led you to add a Knowledge & Evidence Layer is correct — but the layer is not the point. **The point is that architecture recommendation is a governed decision process, and the LLM is one instrument inside it.**

If you build only the reasoning kernel with good pattern contracts and a small precedent store, you will have something valuable. If you build a sophisticated knowledge layer feeding an LLM that generates architectures, you will have a well-read chatbot with a larger context window — and your architects will use it twice.

The order matters: vocabulary, then contracts, then kernel, then knowledge volume. Most teams do this in reverse and wonder why the output reads like a blog post.
