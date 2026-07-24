import type { ReactNode } from "react";

export default function StatTile({
  label,
  value,
  subvalue,
}: {
  label: string;
  value: ReactNode;
  subvalue?: ReactNode;
}) {
  return (
    <div className="stat-tile">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {subvalue ? <div className="subvalue">{subvalue}</div> : null}
    </div>
  );
}
