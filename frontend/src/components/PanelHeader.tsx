import type { ReactNode } from "react";

type PanelHeaderProps = {
  title: string;
  subtitle?: string;
  collapsed?: boolean;
  onToggle?: () => void;
  toggleLabel?: string;
  rightSlot?: ReactNode;
};

export default function PanelHeader({
  title,
  subtitle,
  collapsed = false,
  onToggle,
  toggleLabel,
  rightSlot,
}: PanelHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-[color:var(--stroke)] pb-4">
      <div className={collapsed ? "hidden" : "min-w-0"}>
        <p className="text-[0.72rem] uppercase tracking-[0.24em] text-[color:var(--accent)]">
          {title}
        </p>
        {subtitle ? (
          <p className="mt-1 text-sm text-[color:var(--muted)]">{subtitle}</p>
        ) : null}
      </div>

      <div className="ml-auto flex items-center gap-2">
        {rightSlot}
        {onToggle ? (
          <button
            className="icon-button"
            type="button"
            onClick={onToggle}
            aria-label={toggleLabel ?? `Alternar ${title}`}
            title={toggleLabel ?? `Alternar ${title}`}
          >
            {collapsed ? "›" : "‹"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
