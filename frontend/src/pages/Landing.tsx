import { useNavigate } from "react-router-dom";
import { IconArrowRight, IconDiagram, IconLightbulb, IconSparkles } from "../components/icons";

export default function Landing() {
  const navigate = useNavigate();

  return (
    <main className="page">
      <p className="eyebrow">
        <IconSparkles width={14} height={14} />
        AI Solution Advisor
      </p>
      <h1>Get an executive recommendation in minutes, not a discovery workshop.</h1>
      <p className="subtitle">
        Describe an AI idea, or upload an existing architecture, and Catalyst will recommend an
        architecture pattern, models, enterprise assets to reuse, and a Workbench configuration —
        with the reasoning behind every choice.
      </p>

      <div className="mode-grid">
        <button className="mode-card" onClick={() => navigate("/idea")}>
          <IconLightbulb width={26} height={26} className="icon" />
          <h2>Describe an AI idea</h2>
          <p>Write a few sentences about what you're trying to build. We'll do the rest.</p>
          <span className="cta">
            Get started <IconArrowRight width={14} height={14} />
          </span>
        </button>
        <button className="mode-card" onClick={() => navigate("/design")}>
          <IconDiagram width={26} height={26} className="icon" />
          <h2>Upload an architecture</h2>
          <p>Paste or upload a Draw.io / Mermaid diagram for a review against the Catalyst Catalog.</p>
          <span className="cta">
            Get started <IconArrowRight width={14} height={14} />
          </span>
        </button>
      </div>
    </main>
  );
}
