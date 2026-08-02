import type { ScenarioStakeholder } from "../../types/scenario";

export default function StakeholderList({ stakeholders }: { stakeholders: ScenarioStakeholder[] }) {
  return (
    <div className="stakeholder-list">
      {stakeholders.map((s) => (
        <div className="stakeholder-item" key={s.role}>
          <div className="role">{s.role}</div>
          <div className="concern">{s.concern}</div>
        </div>
      ))}
    </div>
  );
}
