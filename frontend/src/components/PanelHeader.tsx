import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

type PanelHeaderProps = {
  title: string;
  subtitle?: string;
  collapsed?: boolean;
  /** Which side of the layout this panel is on. Controls arrow direction. */
  side?: "left" | "right";
  onToggle?: () => void;
  toggleLabel?: string;
  rightSlot?: ReactNode;
};

export default function PanelHeader({
  title,
  subtitle,
  collapsed = false,
  side = "left",
  onToggle,
  toggleLabel,
  rightSlot,
}: PanelHeaderProps) {
  // Determine the correct chevron icon based on panel side and collapsed state:
  // Left panel:  expanded → ‹ (collapse left)   collapsed → › (expand right)
  // Right panel: expanded → › (collapse right)   collapsed → ‹ (expand left)
  function getToggleIcon() {
    if (side === "left") {
      return collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />;
    }
    // side === "right"
    return collapsed ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />;
  }

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
            {getToggleIcon()}
          </button>
        ) : null}
      </div>
    </div>
  );
}
