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
        <PanelHeader title="Studio" collapsed onToggle={onToggle} />
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
    <aside className="panel-surface flex h-full flex-col overflow-hidden p-5">
      <PanelHeader
        title="Studio"
        subtitle="Herramientas, estado del stack y acciones del flujo RAG."
        onToggle={onToggle}
        rightSlot={
          <button className="icon-button" type="button" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </button>
        }
      />

      <div className="mt-5 grid grid-cols-2 gap-3">
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
              className={`studio-card ${statusClass}`}
              key={card.id}
              onClick={card.action === "reindex" ? onReindex : undefined}
              type="button"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="studio-icon">
                  <Icon className="h-4 w-4" />
                </span>
                <span className="text-xs uppercase tracking-[0.16em] text-[color:var(--muted)]">
                  {card.value}
                </span>
              </div>
              <div className="mt-4 text-left">
                <p className="font-semibold text-[color:var(--text)]">{card.title}</p>
                <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                  {card.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-5 rounded-[24px] border border-[color:var(--stroke)] bg-[color:var(--surface-strong)] p-4">
        <p className="text-[0.72rem] uppercase tracking-[0.2em] text-[color:var(--accent)]">
          Estado rapido
        </p>
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="text-[color:var(--muted)]">Fuentes indexadas</span>
            <strong className="text-[color:var(--text)]">{summary?.indexed_sources ?? 0}</strong>
          </div>
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="text-[color:var(--muted)]">Chunks persistidos</span>
            <strong className="text-[color:var(--text)]">{summary?.total_chunks ?? 0}</strong>
          </div>
          <div className="flex items-start justify-between gap-3 text-sm">
            <span className="text-[color:var(--muted)]">Vector store</span>
            <strong className="max-w-[11rem] text-right text-[color:var(--text)]">
              {summary?.vector_db_path ?? "N/D"}
            </strong>
          </div>
        </div>
      </div>
    </aside>
  );
}
