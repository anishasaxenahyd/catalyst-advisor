import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import { ApiError, optimizePrompt } from "../lib/apiClient";
import type {
  AutomationLevel,
  DataSensitivity,
  ExpectedScale,
  PromptOptimizationResult,
  QAExchange,
  StructuredHints,
} from "../types/report";
import { IconArrowRight, IconChevron, IconLightbulb, IconLoader, IconRefresh, IconSparkles } from "../components/icons";

const EXAMPLES = [
  "A copilot that drafts real-time replies to customer support tickets, integrated with Salesforce.",
  "An agent that reviews incoming vendor contracts against our approved playbook and flags deviations.",
  "A nightly pipeline that classifies and routes thousands of inbound claims documents.",
];

export default function IdeaInput() {
  const navigate = useNavigate();
  const { submit } = useRecommendation();

  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [dataSensitivity, setDataSensitivity] = useState<DataSensitivity | "">("");
  const [expectedScale, setExpectedScale] = useState<ExpectedScale | "">("");
  const [automationLevel, setAutomationLevel] = useState<AutomationLevel | "">("");

  const [optimizerResult, setOptimizerResult] = useState<PromptOptimizationResult | null>(null);
  const [optimizedText, setOptimizedText] = useState("");
  const [optimizing, setOptimizing] = useState(false);
  const [optimizerError, setOptimizerError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [dismissedFields, setDismissedFields] = useState<Set<string>>(new Set());
  const [qaHistory, setQaHistory] = useState<QAExchange[]>([]);

  const submittedText = optimizerResult ? optimizedText : description;
  const canSubmit = submittedText.trim().length > 0;
  const canOptimize = description.trim().length > 0 && !optimizing;

  function buildHints(): StructuredHints {
    return {
      industry: industry || null,
      data_sensitivity: dataSensitivity || null,
      expected_scale: expectedScale || null,
      automation_level: automationLevel || null,
    };
  }

  async function handleOptimize() {
    if (!canOptimize) return;
    setOptimizing(true);
    setOptimizerError(null);
    try {
      const result = await optimizePrompt({
        mode: "idea",
        description,
        hints: buildHints(),
        prior_answers: [],
      });
      setOptimizerResult(result);
      setOptimizedText(result.optimized_text);
      setAnswers({});
      setDismissedFields(new Set());
      setQaHistory([]);
    } catch (err) {
      setOptimizerError(err instanceof ApiError ? err.message : "Couldn't optimize the prompt right now.");
    } finally {
      setOptimizing(false);
    }
  }

  async function handleReoptimize() {
    if (!optimizerResult || optimizing) return;

    const newExchanges: QAExchange[] = optimizerResult.clarifying_questions
      .filter((q) => answers[q.field]?.trim())
      .map((q) => ({ field: q.field, question: q.question, answer: answers[q.field].trim() }));

    const merged = [...qaHistory];
    for (const exchange of newExchanges) {
      const idx = merged.findIndex((e) => e.field === exchange.field);
      if (idx >= 0) merged[idx] = exchange;
      else merged.push(exchange);
    }

    setOptimizing(true);
    setOptimizerError(null);
    try {
      const result = await optimizePrompt({
        mode: "idea",
        description: optimizedText,
        hints: buildHints(),
        prior_answers: merged,
      });
      setOptimizerResult(result);
      setOptimizedText(result.optimized_text);
      setAnswers({});
      setDismissedFields(new Set());
      setQaHistory(merged);
    } catch (err) {
      setOptimizerError(err instanceof ApiError ? err.message : "Couldn't re-optimize the prompt right now.");
    } finally {
      setOptimizing(false);
    }
  }

  function handleSkip(field: string) {
    setDismissedFields((prev) => new Set(prev).add(field));
  }

  function handleSubmit() {
    if (!canSubmit) return;
    submit({
      mode: "idea",
      description: submittedText,
      hints: buildHints(),
    });
  }

  const visibleQuestions =
    optimizerResult?.clarifying_questions.filter((q) => !dismissedFields.has(q.field)) ?? [];

  return (
    <main className="page">
      <button className="back-link" onClick={() => navigate("/")}>
        <IconChevron width={14} height={14} style={{ transform: "rotate(180deg)" }} />
        Back
      </button>
      <p className="eyebrow">
        <IconLightbulb width={14} height={14} />
        Step 1 of 2 — Describe the idea
      </p>
      <h1>What are you trying to build?</h1>
      <p className="subtitle">
        A couple of sentences is enough. The more specific you are about data, users, and systems
        involved, the sharper the recommendation.
      </p>

      <div className="field">
        <label htmlFor="description">Idea description</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            setOptimizerResult(null);
            setOptimizerError(null);
          }}
          placeholder="e.g. We want a copilot that drafts replies to customer support tickets in real time, integrated with Salesforce."
        />
      </div>

      <div className="example-row">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className="example-chip"
            onClick={() => {
              setDescription(example);
              setOptimizerResult(null);
              setOptimizerError(null);
            }}
          >
            {example.length > 56 ? `${example.slice(0, 56)}…` : example}
          </button>
        ))}
      </div>

      <div className="optimizer-panel">
        <button type="button" className="optimizer-trigger" onClick={handleOptimize} disabled={!canOptimize}>
          {optimizing ? (
            <IconLoader width={16} height={16} />
          ) : (
            <IconSparkles width={16} height={16} />
          )}
          {optimizerResult ? "Optimize again from scratch" : "Optimize prompt"}
        </button>

        {optimizerError && <p className="optimizer-error">{optimizerError}</p>}

        {optimizerResult && (
          <div className="optimizer-result">
            <div className="optimizer-result-header">
              <label htmlFor="optimized-text">Optimized prompt</label>
              <span className="token-badge">
                ~{optimizerResult.original_token_estimate} → ~{optimizerResult.optimized_token_estimate} tokens
              </span>
            </div>
            <textarea
              id="optimized-text"
              value={optimizedText}
              onChange={(e) => setOptimizedText(e.target.value)}
            />
            {optimizerResult.notes && <p className="optimizer-notes">{optimizerResult.notes}</p>}

            {visibleQuestions.length > 0 && (
              <div className="optimizer-questions">
                <p className="optimizer-questions-title">
                  A few details would sharpen the recommendation:
                </p>
                {visibleQuestions.map((q) => (
                  <div className="optimizer-question" key={q.field}>
                    <label htmlFor={`qa-${q.field}`}>{q.question}</label>
                    <div className="optimizer-question-row">
                      <input
                        id={`qa-${q.field}`}
                        type="text"
                        value={answers[q.field] ?? ""}
                        onChange={(e) => setAnswers((prev) => ({ ...prev, [q.field]: e.target.value }))}
                        placeholder="Your answer"
                      />
                      <button type="button" className="optimizer-skip" onClick={() => handleSkip(q.field)}>
                        Skip
                      </button>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  className="optimizer-reoptimize"
                  onClick={handleReoptimize}
                  disabled={optimizing}
                >
                  {optimizing ? (
                    <IconLoader width={14} height={14} />
                  ) : (
                    <IconRefresh width={14} height={14} />
                  )}
                  Re-optimize with answers
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="hints-grid">
        <div className="field">
          <label htmlFor="industry">
            Industry <span className="hint">(optional)</span>
          </label>
          <input
            id="industry"
            type="text"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="e.g. Healthcare"
          />
        </div>
        <div className="field">
          <label htmlFor="sensitivity">
            Data sensitivity <span className="hint">(optional)</span>
          </label>
          <select
            id="sensitivity"
            value={dataSensitivity}
            onChange={(e) => setDataSensitivity(e.target.value as DataSensitivity)}
          >
            <option value="">Not sure</option>
            <option value="none">None</option>
            <option value="pii">PII</option>
            <option value="phi">PHI</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="scale">
            Expected scale <span className="hint">(optional)</span>
          </label>
          <select id="scale" value={expectedScale} onChange={(e) => setExpectedScale(e.target.value as ExpectedScale)}>
            <option value="">Not sure</option>
            <option value="pilot">Pilot</option>
            <option value="department">Department</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="automation">
            Automation level <span className="hint">(optional)</span>
          </label>
          <select
            id="automation"
            value={automationLevel}
            onChange={(e) => setAutomationLevel(e.target.value as AutomationLevel)}
          >
            <option value="">Not sure</option>
            <option value="assist">Assist — suggests only</option>
            <option value="copilot">Copilot — drafts for review</option>
            <option value="autonomous">Autonomous — acts on its own</option>
          </select>
        </div>
      </div>

      <div className="actions">
        <button className="primary" onClick={handleSubmit} disabled={!canSubmit}>
          Analyze idea
          <IconArrowRight width={16} height={16} />
        </button>
      </div>
    </main>
  );
}
