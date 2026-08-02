import { AlertCircle, Layers, Lightbulb, TrendingUp, type LucideIcon } from "lucide-react";
import type { ExecutiveCards } from "../../types/report";

const CARDS: { key: keyof ExecutiveCards; label: string; icon: LucideIcon }[] = [
  { key: "problem", label: "Problem", icon: AlertCircle },
  { key: "opportunity", label: "Opportunity", icon: Lightbulb },
  { key: "recommended_pattern", label: "Recommended AI Pattern", icon: Layers },
  { key: "expected_outcome", label: "Expected Business Outcome", icon: TrendingUp },
];

export default function ExecutiveCardsGrid({ cards }: { cards: ExecutiveCards }) {
  return (
    <div className="rpt-exec-cards">
      {CARDS.map(({ key, label, icon: Icon }) => (
        <div className="rpt-exec-card" key={key}>
          <span className="label">
            <Icon width={14} height={14} />
            {label}
          </span>
          <p>{cards[key]}</p>
        </div>
      ))}
    </div>
  );
}
