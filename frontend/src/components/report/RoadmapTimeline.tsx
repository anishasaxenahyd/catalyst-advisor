import type { RoadmapPhase } from "../../types/report";

export default function RoadmapTimeline({ phases }: { phases: RoadmapPhase[] }) {
  return (
    <div className="rpt-roadmap">
      {phases.map((phase, idx) => (
        <div className="rpt-roadmap-step" key={phase.name}>
          <div className="marker-col">
            <span className="marker">{idx + 1}</span>
            {idx < phases.length - 1 && <span className="connector" />}
          </div>
          <div className="content">
            <div className="content-inner">
              <div className="title-row">
                <h3>{phase.name}</h3>
                <span className="rpt-badge neutral">{phase.duration}</span>
              </div>
              <div className="rpt-roadmap-columns">
                <div>
                  <p className="col-label">Deliverables</p>
                  <ul>
                    {phase.deliverables.map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                  </ul>
                </div>
                <div className="risks-col">
                  <p className="col-label">Risks</p>
                  <ul>
                    {phase.risks.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
