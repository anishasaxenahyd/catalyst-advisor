import { useEffect, useId, useState } from "react";
import { IconInfo } from "./icons";

let initPromise: Promise<typeof import("mermaid")["default"]> | null = null;

/** Mermaid is a large, multi-diagram-type library — dynamically imported
 * so its cost is paid only when a report with a diagram is actually
 * viewed, not on every page load (Landing, forms, etc. never touch it). */
function loadMermaid() {
  if (!initPromise) {
    initPromise = import("mermaid").then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        theme: "neutral",
        securityLevel: "strict",
        fontFamily: "Segoe UI, ui-sans-serif, sans-serif",
        themeVariables: {
          primaryColor: "#f0dcc7",
          primaryBorderColor: "#c1651f",
          primaryTextColor: "#14181c",
          lineColor: "#4b535b",
          fontSize: "14px",
        },
      });
      return mermaid;
    });
  }
  return initPromise;
}

/** Renders a Mermaid diagram client-side; falls back to the raw source in
 * a code block if rendering throws (malformed template, unsupported
 * syntax, load failure, etc.) — never lets a bad diagram break the report. */
export default function MermaidDiagram({ source }: { source: string }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    loadMermaid()
      .then((mermaid) => mermaid.render(`mermaid-${id}`, source))
      .then((result) => {
        if (!cancelled) setSvg(result.svg);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
    };
  }, [id, source]);

  if (failed) {
    return (
      <div>
        <pre className="mermaid-source">{source}</pre>
        <p className="mermaid-fallback-note">
          <IconInfo width={14} height={14} />
          Diagram couldn't be rendered — showing the source instead.
        </p>
      </div>
    );
  }

  if (!svg) {
    return <div className="mermaid-panel" aria-busy="true" style={{ minHeight: 80 }} />;
  }

  // svg comes from mermaid's own renderer against a `strict` security
  // level (no script execution, no foreignObject) — safe to inject.
  return <div className="mermaid-panel" dangerouslySetInnerHTML={{ __html: svg }} />;
}
