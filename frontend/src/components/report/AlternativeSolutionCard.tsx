import type { ModelRecommendation } from "../../types/report";

function levelLabel(level: string): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export default function AlternativeSolutionCard({ modelRecommendation }: { modelRecommendation: ModelRecommendation }) {
  const { primary, alternatives, relative_cost } = modelRecommendation;

  const cards = [
    {
      id: primary.id,
      name: primary.name,
      advantages: primary.strengths,
      limitations: primary.weaknesses,
      cost: relative_cost,
      bestUseCase: primary.suitable_for_tags.slice(0, 3).join(", ") || "General purpose",
      recommended: true,
    },
    ...alternatives.map((alt) => ({
      id: alt.model.id,
      name: alt.model.name,
      advantages: alt.model.strengths,
      limitations: alt.model.weaknesses,
      cost: alt.relative_cost,
      bestUseCase: alt.model.suitable_for_tags.slice(0, 3).join(", ") || "General purpose",
      recommended: false,
    })),
  ];

  return (
    <div className="rpt-alt-grid">
      {cards.map((card) => (
        <div className={`rpt-alt-card ${card.recommended ? "recommended" : ""}`} key={card.id}>
          <div className="heading">
            <span className="name">{card.name}</span>
            {card.recommended && <span className="rpt-badge accent">Recommended</span>}
          </div>
          <div className="field">
            <span className="field-label">Advantages</span>
            <ul>
              {card.advantages.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
          <div className="field">
            <span className="field-label">Limitations</span>
            <ul>
              {card.limitations.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </div>
          <div className="field">
            <span className="field-label">Cost</span>
            <p>{levelLabel(card.cost)}</p>
          </div>
          <div className="field">
            <span className="field-label">Best Use Case</span>
            <p>{card.bestUseCase}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
