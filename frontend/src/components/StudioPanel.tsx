import {
  Bot,
  DatabaseZap,
  Gauge,
  HardDriveDownload,
  Layers3,
  RefreshCw,
} from "lucide-react";

import PanelHeader from "./PanelHeader";
import type { DashboardSummary, StudioCard } from "../types";

type StudioPanelProps = {
  cards: StudioCard[];
  collapsed?: boolean;
  isBusy: boolean;
  onReindex: () => void;
  onRefresh: () => void;
  onToggle: () => void;
  summary: DashboardSummary | null;
};

function cardIcon(cardId: string) {
  switch (cardId) {
    case "reindex":
      return Layers3;
    case "ollama":
      return Bot;
    case "vector-store":
      return DatabaseZap;
    case "retrieval":
      return Gauge;
    default:
      return HardDriveDownload;
  }
}

export default function StudioPanel({
  cards,
  collapsed = false,
  isBusy,
  onReindex,
  onRefresh,
  onToggle,
  summary,
}: StudioPanelProps) {
  if (collapsed) {
    return (
      <aside className="panel-surface hidden h-full w-[5.25rem] shrink-0 lg:flex lg:flex-col lg:items-center lg:gap-4 lg:p-4">
        <PanelHeader title="Studio" collapsed side="right" onToggle={onToggle} />
        <button className="icon-button h-11 w-11" type="button" onClick={onReindex}>
          <Layers3 className={`h-4 w-4 ${isBusy ? "animate-spin" : ""}`} />
        </button>
        <button className="icon-button h-11 w-11" type="button" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="panel-surface flex h-full w-full flex-col overflow-hidden p-5">
      <PanelHeader
        title="Studio"
        side="right"
        onToggle={onToggle}
        rightSlot={
          <button className="icon-button" type="button" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </button>
        }
      />

      <div className="mt-5 flex flex-col gap-3 flex-1 min-h-0 overflow-y-auto pr-2 pb-2">
       <div className="grid grid-cols-[repeat(auto-fill,minmax(125px,1fr))] gap-2">
        {cards.map((card) => {
          const Icon = cardIcon(card.id);
          const statusClass =
            card.status === "ready"
              ? "studio-card-ready"
              : card.status === "warning"
                ? "studio-card-warning"
                : card.status === "action"
                  ? "studio-card-action"
                  : "studio-card-neutral";

          return (
            <button
              className={`studio-card ${statusClass} flex flex-col items-start justify-between gap-2 !p-3`}
              key={card.id}
              onClick={card.action === "reindex" ? onReindex : undefined}
              type="button"
            >
              <div className="flex w-full items-center justify-between gap-1">
                <span className="studio-icon !h-7 !w-7 !rounded-lg shrink-0">
                  <Icon className="h-3.5 w-3.5" />
                </span>
                <span className="text-[10px] uppercase tracking-[0.1em] text-[color:var(--muted)] truncate">
                  {card.value}
                </span>
              </div>
              <div className="w-full text-left mt-1">
                <p className="text-[13px] font-semibold leading-tight text-[color:var(--text)]">{card.title}</p>
              </div>
            </button>
          );
        })}
        </div>
       </div>


    </aside>
  );
}
