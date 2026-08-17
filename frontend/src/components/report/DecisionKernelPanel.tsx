import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import type {
  Alternative,
  Candidate,
  EliminationEntry,
  KernelReport,
  PatternVerdict,
  PatternVerdictEntry,
  PrecedentFinding,
  SourcingDecision,
  SourcingOutcome,
} from "../../types/report";

function Section({ title, defaultOpen = false, children }: { title: string; defaultOpen?: boolean; children: ReactNode }) {
  return (
    <details className="rpt-trace-section" open={defaultOpen}>
      <summary>
        {title}
        <ChevronRight className="chevron" width={14} height={14} />
      </summary>
      <div className="rpt-trace-section-body">{children}</div>
    </details>
  );
}

const VERDICT_BADGE: Record<PatternVerdict, string> = {
  REQUIRED: "good",
  CONDITIONAL: "accent",
  APPLICABLE: "neutral",
  UNNECESSARY: "warning",
  CONTRA_INDICATED: "critical",
};

const VERDICT_LABEL: Record<PatternVerdict, string> = {
  REQUIRED: "Required",
  CONDITIONAL: "Conditional",
  APPLICABLE: "Applicable (subsumed)",
  UNNECESSARY: "Unnecessary",
  CONTRA_INDICATED: "Contra-indicated",
};

const SOURCING_BADGE: Record<SourcingOutcome, string> = {
  reuse: "good",
  extend: "accent",
  compose: "accent",
  buy: "neutral",
  build: "warning",
  defer: "neutral",
};

function PatternRow({ entry }: { entry: PatternVerdictEntry }) {
  return (
    <li>
      <span className={`rpt-badge ${VERDICT_BADGE[entry.verdict]}`} style={{ marginRight: "0.5rem" }}>
        {VERDICT_LABEL[entry.verdict]}
      </span>
      <strong>{entry.pattern_name}</strong>
      <span style={{ color: "var(--rpt-ink-soft)" }}> — {entry.reason}</span>
    </li>
  );
}

function SourcingRow({ decision }: { decision: SourcingDecision }) {
  return (
    <li>
      <span className={`rpt-badge ${SOURCING_BADGE[decision.decision]}`} style={{ marginRight: "0.5rem" }}>
        {decision.decision}
      </span>
      <strong>{decision.capability_name}</strong>
      {decision.asset_ref && <span style={{ color: "var(--rpt-ink-soft)" }}> via {decision.asset_ref}</span>}
      <div style={{ fontSize: "0.85rem", color: "var(--rpt-ink-soft)", marginTop: "0.15rem" }}>{decision.justification}</div>
      {decision.rejected_alternatives.length > 0 && (
        <div style={{ fontSize: "0.8rem", color: "var(--rpt-ink-muted)", marginTop: "0.15rem" }}>
          Rejected: {decision.rejected_alternatives.join("; ")}
        </div>
      )}
    </li>
  );
}

function EliminationRow({ entry, candidates }: { entry: EliminationEntry; candidates: Candidate[] }) {
  const candidate = candidates.find((c) => c.id === entry.candidate_id);
  return (
    <li>
      <strong>{entry.candidate_label}</strong>
      <span className="rpt-badge critical" style={{ marginLeft: "0.5rem" }}>
        eliminated — {entry.rule_id}
      </span>
      <div style={{ fontSize: "0.85rem", color: "var(--rpt-ink-soft)", marginTop: "0.15rem" }}>{entry.evidence}</div>
      {candidate && (
        <div style={{ fontSize: "0.8rem", color: "var(--rpt-ink-muted)", marginTop: "0.15rem" }}>{candidate.description}</div>
      )}
    </li>
  );
}

function AlternativeRow({ alt, narrative }: { alt: Alternative; narrative?: string }) {
  return (
    <li>
      <strong>{alt.label}</strong>
      <ul style={{ marginTop: "0.35rem" }}>
        <li>
          <em>Choose this if:</em> {alt.governing_priority}
        </li>
        <li>
          <em>You give up:</em> {alt.what_is_given_up}
        </li>
        <li>
          <em>Switching cost:</em> {alt.switching_cost}
        </li>
        <li>
          <em>Revisit trigger:</em> {alt.revisit_trigger}
        </li>
      </ul>
      {narrative && <p style={{ fontSize: "0.85rem", color: "var(--rpt-ink-soft)", marginTop: "0.35rem" }}>{narrative}</p>}
    </li>
  );
}

const EVIDENCE_BADGE: Record<string, string> = {
  transferable_decision_evidence: "good",
  feasibility_evidence: "accent",
  hazard_evidence: "critical",
};

const EVIDENCE_LABEL: Record<string, string> = {
  transferable_decision_evidence: "Transferable decision evidence",
  feasibility_evidence: "Feasibility evidence only",
  hazard_evidence: "Hazard evidence",
};

function PrecedentRow({ finding }: { finding: PrecedentFinding }) {
  return (
    <li>
      <span className={`rpt-badge ${EVIDENCE_BADGE[finding.usage] ?? "neutral"}`} style={{ marginRight: "0.5rem" }}>
        {EVIDENCE_LABEL[finding.usage] ?? finding.usage}
      </span>
      <strong>{finding.title}</strong>
      <span style={{ color: "var(--rpt-ink-soft)" }}> ({finding.evidence_class.replace(/_/g, " ")})</span>
      {finding.lesson_summary && (
        <div style={{ fontSize: "0.85rem", color: "var(--rpt-ink-soft)", marginTop: "0.15rem", fontStyle: "italic" }}>
          Lesson: {finding.lesson_summary}
        </div>
      )}
      {finding.divergences.length > 0 && (
        <div style={{ fontSize: "0.8rem", color: "var(--rpt-ink-muted)", marginTop: "0.15rem" }}>
          Divergence: {finding.divergences.join(" ")}
        </div>
      )}
    </li>
  );
}

// The Decision Kernel's staged trail, rendered as a projection of the
// kernel's own output — every line here traces to a stage in
// backend/app/kernel/, never regenerated for display (Part 10.3 of the
// architecture redesign: explanation is projection, never regeneration).
export default function DecisionKernelPanel({ kernel }: { kernel: KernelReport }) {
  const rejected = kernel.pattern_verdicts.filter((v) => v.verdict === "UNNECESSARY" || v.verdict === "CONTRA_INDICATED");
  const admissible = kernel.pattern_verdicts.filter((v) => v.verdict !== "UNNECESSARY" && v.verdict !== "CONTRA_INDICATED");
  const narrativeById = Object.fromEntries(kernel.narrative_extras.alternatives_narrative.map((n) => [n.candidate_id, n.narrative]));

  return (
    <details className="rpt-trace-block" open>
      <summary>
        How this was decided
        <ChevronRight className="chevron" width={16} height={16} />
      </summary>

      <div className="rpt-trace-body">
        <div className="rpt-chip-row" style={{ marginBottom: "0.75rem" }}>
          <span className="rpt-badge accent">Solution class: {kernel.solution_class_name}</span>
        </div>

        <Section title={`Pattern admissibility (${admissible.length} admissible, ${rejected.length} rejected)`} defaultOpen>
          <ul className="rpt-bullet-list">
            {admissible.map((v) => (
              <PatternRow key={v.pattern_id} entry={v} />
            ))}
          </ul>
        </Section>

        <Section title={`Rejected options (${rejected.length})`}>
          {kernel.narrative_extras.rejected_options_narrative && (
            <p style={{ margin: "0 0 0.6rem", color: "var(--rpt-ink-soft)" }}>{kernel.narrative_extras.rejected_options_narrative}</p>
          )}
          <ul className="rpt-bullet-list">
            {rejected.map((v) => (
              <PatternRow key={v.pattern_id} entry={v} />
            ))}
          </ul>
        </Section>

        <Section title={`Sourcing decisions (${kernel.sourcing_decisions.length})`}>
          {kernel.narrative_extras.sourcing_narrative && (
            <p style={{ margin: "0 0 0.6rem", color: "var(--rpt-ink-soft)" }}>{kernel.narrative_extras.sourcing_narrative}</p>
          )}
          <ul className="rpt-bullet-list">
            {kernel.sourcing_decisions.map((d) => (
              <SourcingRow key={d.capability_id} decision={d} />
            ))}
          </ul>
        </Section>

        {kernel.elimination_record.length > 0 && (
          <Section title={`Elimination record (${kernel.elimination_record.length})`}>
            <ul className="rpt-bullet-list">
              {kernel.elimination_record.map((e) => (
                <EliminationRow key={e.candidate_id} entry={e} candidates={kernel.candidates} />
              ))}
            </ul>
          </Section>
        )}

        {kernel.alternatives.length > 0 && (
          <Section title={`Alternatives (${kernel.alternatives.length})`}>
            <ul className="rpt-bullet-list">
              {kernel.alternatives.map((a) => (
                <AlternativeRow key={a.candidate_id} alt={a} narrative={narrativeById[a.candidate_id]} />
              ))}
            </ul>
          </Section>
        )}

        {kernel.precedent_findings.length > 0 && (
          <Section title={`Precedent findings (${kernel.precedent_findings.length})`}>
            <ul className="rpt-bullet-list">
              {kernel.precedent_findings.map((f) => (
                <PrecedentRow key={f.solution_id} finding={f} />
              ))}
            </ul>
          </Section>
        )}

        {kernel.counterfactuals.length > 0 && (
          <Section title="What would change this recommendation">
            <ul className="rpt-bullet-list">
              {kernel.counterfactuals.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </Section>
        )}
      </div>
    </details>
  );
}
