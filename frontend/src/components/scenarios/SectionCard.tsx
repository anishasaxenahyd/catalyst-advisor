import type { ComponentType, ReactNode, SVGProps } from "react";

export default function SectionCard({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="scenario-section">
      <div className="scenario-section-head">
        <Icon width={18} height={18} className="icon" />
        <h2>{title}</h2>
      </div>
      {subtitle && (
        <p className="subtitle" style={{ marginBottom: "1rem" }}>
          {subtitle}
        </p>
      )}
      {children}
    </section>
  );
}
