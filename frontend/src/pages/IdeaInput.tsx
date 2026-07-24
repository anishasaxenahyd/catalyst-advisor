import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import type { AutomationLevel, DataSensitivity, ExpectedScale } from "../types/report";
import { IconArrowRight, IconChevron, IconLightbulb } from "../components/icons";

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

  const canSubmit = description.trim().length > 0;

  function handleSubmit() {
    if (!canSubmit) return;
    submit({
      mode: "idea",
      description,
      hints: {
        industry: industry || null,
        data_sensitivity: dataSensitivity || null,
        expected_scale: expectedScale || null,
        automation_level: automationLevel || null,
      },
    });
  }

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
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. We want a copilot that drafts replies to customer support tickets in real time, integrated with Salesforce."
        />
      </div>

      <div className="example-row">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className="example-chip"
            onClick={() => setDescription(example)}
          >
            {example.length > 56 ? `${example.slice(0, 56)}…` : example}
          </button>
        ))}
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
