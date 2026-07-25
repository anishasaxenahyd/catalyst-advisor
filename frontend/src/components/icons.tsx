// A small hand-rolled icon set — deliberately not an icon library dependency.
// Every icon is a 20x20 stroke glyph on a 1.75 stroke width, currentColor,
// so they inherit text color and size like a glyph.

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = {
  width: 20,
  height: 20,
  viewBox: "0 0 20 20",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function IconLightbulb(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 15.5h6M8 18h4M6.5 8a3.5 3.5 0 1 1 7 0c0 1.6-.9 2.4-1.6 3.1-.5.5-.9 1-.9 1.9h-2c0-.9-.4-1.4-.9-1.9C7.4 10.4 6.5 9.6 6.5 8Z" />
    </svg>
  );
}

export function IconDiagram(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2.5" y="3" width="6" height="4.5" rx="1" />
      <rect x="11.5" y="3" width="6" height="4.5" rx="1" />
      <rect x="7" y="12.5" width="6" height="4.5" rx="1" />
      <path d="M5.5 7.5v2a2 2 0 0 0 2 2h5a2 2 0 0 0 2-2v-2M10 11.5v1" />
    </svg>
  );
}

export function IconArrowRight(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 10h12M11 5l5 5-5 5" />
    </svg>
  );
}

export function IconChevron(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M7 4.5 12.5 10 7 15.5" />
    </svg>
  );
}

export function IconCheckCircle(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M7 10.2l2.1 2.1L13.3 8" />
    </svg>
  );
}

export function IconAlertTriangle(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3.5 17.5 16h-15L10 3.5Z" />
      <path d="M10 8.25v3.25M10 14.25v.1" />
    </svg>
  );
}

export function IconInfo(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 9.25v4.25M10 6.5v.1" />
    </svg>
  );
}

export function IconSparkles(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3.5 11.2 7.3 15 8.5l-3.8 1.2L10 13.5 8.8 9.7 5 8.5l3.8-1.2L10 3.5Z" />
      <path d="M15.5 13.5l.6 1.7 1.7.6-1.7.6-.6 1.7-.6-1.7-1.7-.6 1.7-.6.6-1.7Z" />
    </svg>
  );
}

export function IconShield(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3 16 5.2v4.4c0 4-2.6 6.5-6 7.4-3.4-.9-6-3.4-6-7.4V5.2L10 3Z" />
      <path d="M7.3 10.1l1.9 1.9 3.5-3.8" />
    </svg>
  );
}

export function IconServer(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="3.5" width="14" height="5" rx="1.3" />
      <rect x="3" y="11.5" width="14" height="5" rx="1.3" />
      <path d="M6 6h.01M6 14h.01" />
    </svg>
  );
}

export function IconLayers(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3 17 7l-7 4-7-4 7-4Z" />
      <path d="M3 10.5 10 14.5 17 10.5M3 14 10 18 17 14" />
    </svg>
  );
}

export function IconCloud(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6.2 15.5A3.7 3.7 0 0 1 5.5 8.1a4.5 4.5 0 0 1 8.7-1.4A3.6 3.6 0 0 1 14.5 15.5H6.2Z" />
    </svg>
  );
}

export function IconClock(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7.25" />
      <path d="M10 6v4.2l3 1.8" />
    </svg>
  );
}

export function IconTarget(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="10" r="7" />
      <circle cx="10" cy="10" r="3.6" />
      <circle cx="10" cy="10" r="0.6" fill="currentColor" />
    </svg>
  );
}

export function IconBarChart(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 16.5V11M10 16.5V4.5M16 16.5V8.5" />
      <path d="M2.5 16.5h15" />
    </svg>
  );
}

export function IconLoader(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3v3M10 14v3M4.6 4.6l2.1 2.1M13.3 13.3l2.1 2.1M3 10h3M14 10h3M4.6 15.4l2.1-2.1M13.3 6.7l2.1-2.1" />
    </svg>
  );
}

export function IconFileWarning(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 2.5h5.5L15 6v11.5H6V2.5Z" />
      <path d="M11.3 2.5V6H15" />
      <path d="M10.5 9v3M10.5 13.6v.1" />
    </svg>
  );
}

export function IconRefresh(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M16 6.5a6.5 6.5 0 0 0-11.2-2.3M4 3.5v3.7h3.7" />
      <path d="M4 13.5a6.5 6.5 0 0 0 11.2 2.3M16 16.5v-3.7h-3.7" />
    </svg>
  );
}

export function IconPrint(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 7.5V3h8v4.5" />
      <rect x="3" y="7.5" width="14" height="6.5" rx="1.2" />
      <path d="M6 12.5h8v4.5H6v-4.5Z" />
    </svg>
  );
}

export function IconUpload(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 12.5V4M6.8 7.2 10 4l3.2 3.2" />
      <path d="M4 14.5v1.8a1.2 1.2 0 0 0 1.2 1.2h9.6a1.2 1.2 0 0 0 1.2-1.2v-1.8" />
    </svg>
  );
}

export function IconUser(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="10" cy="6.8" r="3.3" />
      <path d="M3.8 17c.7-3.3 3.2-5 6.2-5s5.5 1.7 6.2 5" />
    </svg>
  );
}

export function IconLock(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="4.5" y="9" width="11" height="8" rx="1.4" />
      <path d="M6.5 9V6.2a3.5 3.5 0 0 1 7 0V9" />
      <path d="M10 12v2.2" />
    </svg>
  );
}

export function IconRoute(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2.5" y="7" width="15" height="6" rx="1.4" />
      <path d="M6.5 7v6M13.5 7v6" />
      <path d="M9 10h2" />
    </svg>
  );
}

export function IconDatabase(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <ellipse cx="10" cy="5" rx="6" ry="2.3" />
      <path d="M4 5v10c0 1.27 2.69 2.3 6 2.3s6-1.03 6-2.3V5" />
      <path d="M4 10c0 1.27 2.69 2.3 6 2.3s6-1.03 6-2.3" />
    </svg>
  );
}

export function IconEye(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M2 10.3S5 4.8 10 4.8s8 5.5 8 5.5-3 5.5-8 5.5-8-5.5-8-5.5Z" />
      <circle cx="10" cy="10.3" r="2.2" />
    </svg>
  );
}

export function IconCpu(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="6" y="6" width="8" height="8" rx="1" />
      <rect x="8.4" y="8.4" width="3.2" height="3.2" />
      <path d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.6 4.6l1.4 1.4M14 14l1.4 1.4M4.6 15.4l1.4-1.4M14 6l1.4-1.4" />
    </svg>
  );
}

export function IconFileText(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M6 2.5h5.5L15 6v11.5H6V2.5Z" />
      <path d="M11.3 2.5V6H15" />
      <path d="M8 10h4M8 12.8h4M8 7.5h1.8" />
    </svg>
  );
}
