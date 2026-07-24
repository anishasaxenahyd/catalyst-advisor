import { useRef, useState, type DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useRecommendation } from "../lib/RecommendationContext";
import type { AutomationLevel, DataSensitivity, ExpectedScale } from "../types/report";
import { IconArrowRight, IconChevron, IconCheckCircle, IconDiagram, IconInfo, IconUpload } from "../components/icons";

const ACCEPTED_EXTENSIONS = [".drawio", ".xml", ".mmd", ".mermaid", ".txt"];

export default function DesignUpload() {
  const navigate = useNavigate();
  const { submit } = useRecommendation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [fileName, setFileName] = useState<string | null>(null);
  const [diagramText, setDiagramText] = useState<string>("");
  const [unsupportedType, setUnsupportedType] = useState(false);
  const [context, setContext] = useState("");
  const [industry, setIndustry] = useState("");
  const [dataSensitivity, setDataSensitivity] = useState<DataSensitivity | "">("");
  const [expectedScale, setExpectedScale] = useState<ExpectedScale | "">("");
  const [automationLevel, setAutomationLevel] = useState<AutomationLevel | "">("");
  const [isDragging, setIsDragging] = useState(false);

  function readFile(file: File) {
    const looksSupported = ACCEPTED_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));
    setUnsupportedType(!looksSupported);
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => setDiagramText(String(reader.result ?? ""));
    reader.readAsText(file);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) readFile(file);
  }

  const canSubmit = diagramText.trim().length > 0 || context.trim().length > 0;

  function handleSubmit() {
    if (!canSubmit) return;
    submit({
      mode: "design_review",
      description: context,
      diagram_text: diagramText || null,
      diagram_filename: fileName,
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
        <IconDiagram width={14} height={14} />
        Step 1 of 2 — Upload architecture
      </p>
      <h1>Share the architecture you'd like reviewed</h1>
      <p className="subtitle">
        Draw.io XML and Mermaid text are read directly. PNG/PDF diagram understanding arrives in a
        later phase — for now, paste or upload the source file.
      </p>

      <div
        className={`dropzone ${fileName ? "has-file" : ""} ${isDragging ? "dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {fileName ? (
          <p style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5em", margin: 0 }}>
            <IconCheckCircle width={18} height={18} style={{ color: "var(--good)" }} />
            <strong>{fileName}</strong> loaded — {diagramText.length.toLocaleString()} characters
          </p>
        ) : (
          <>
            <IconUpload width={22} height={22} style={{ marginBottom: "0.5rem" }} />
            <p style={{ margin: "0 0 0.75rem" }}>Drag a .drawio, .xml, or .mmd file here, or</p>
          </>
        )}
        <button className="secondary" onClick={() => fileInputRef.current?.click()} type="button">
          Browse files
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          style={{ display: "none" }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) readFile(file);
          }}
        />
      </div>

      {unsupportedType && (
        <p
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5em",
            fontSize: "0.85rem",
            color: "var(--warning)",
            marginTop: "-0.5rem",
            marginBottom: "1rem",
          }}
        >
          <IconInfo width={16} height={16} />
          That file extension isn't one we specifically parse — it'll still be sent as plain text,
          so results may be less precise than a .drawio or .mmd export.
        </p>
      )}

      <div className="field">
        <label htmlFor="context">
          Anything we should know? <span className="hint">(optional, or paste diagram text here directly)</span>
        </label>
        <textarea
          id="context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Constraints, target users, systems involved..."
        />
      </div>

      <div className="hints-grid">
        <div className="field">
          <label htmlFor="industry">
            Industry <span className="hint">(optional)</span>
          </label>
          <input id="industry" type="text" value={industry} onChange={(e) => setIndustry(e.target.value)} />
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
          Analyze diagram
          <IconArrowRight width={16} height={16} />
        </button>
      </div>
    </main>
  );
}
