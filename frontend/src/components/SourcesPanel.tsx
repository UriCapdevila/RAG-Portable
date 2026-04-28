import { useRef } from "react";
import {
  CheckCircle2,
  Database,
  FileText,
  FolderUp,
  RefreshCw,
  Search,
} from "lucide-react";

import PanelHeader from "./PanelHeader";
import type { SourceRecord } from "../types";

type SourcesPanelProps = {
  collapsed?: boolean;
  isBusy: boolean;
  onToggle: () => void;
  onUpload: (files: File[]) => void;
  onReindex: () => void;
  onRefresh: () => void;
  query: string;
  onQueryChange: (value: string) => void;
  sources: SourceRecord[];
};

function formatFileSize(fileSize: number | null): string {
  if (!fileSize) {
    return "Sin tamano";
  }
  if (fileSize < 1024) {
    return `${fileSize} B`;
  }
  if (fileSize < 1024 * 1024) {
    return `${(fileSize / 1024).toFixed(1)} KB`;
  }
  return `${(fileSize / (1024 * 1024)).toFixed(1)} MB`;
}

export default function SourcesPanel({
  collapsed = false,
  isBusy,
  onToggle,
  onUpload,
  onReindex,
  onRefresh,
  query,
  onQueryChange,
  sources,
}: SourcesPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const indexedSources = sources.filter((source) => source.is_indexed).length;

  if (collapsed) {
    return (
      <aside className="panel-surface hidden h-full w-[5.25rem] shrink-0 lg:flex lg:flex-col lg:items-center lg:gap-4 lg:p-4">
        <PanelHeader title="Fuentes" collapsed onToggle={onToggle} />
        <div className="flex flex-col items-center gap-3 pt-2">
          <div className="status-chip">
            <Database className="h-4 w-4" />
            <span>{indexedSources}</span>
          </div>
          <button className="icon-button h-11 w-11" type="button" onClick={onReindex}>
            <RefreshCw className={`h-4 w-4 ${isBusy ? "animate-spin" : ""}`} />
          </button>
          <button
            className="icon-button h-11 w-11"
            type="button"
            onClick={() => fileInputRef.current?.click()}
          >
            <FolderUp className="h-4 w-4" />
          </button>
        </div>
        <input
          ref={fileInputRef}
          className="hidden"
          type="file"
          multiple
          accept=".pdf,.txt,.md,.csv"
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            if (files.length) {
              onUpload(files);
            }
            event.currentTarget.value = "";
          }}
        />
      </aside>
    );
  }

  return (
    <aside className="panel-surface flex h-full flex-col overflow-hidden p-5">
      <PanelHeader
        title="Fuentes"
        subtitle={`${indexedSources}/${sources.length} activas en el RAG`}
        onToggle={onToggle}
        rightSlot={
          <button className="icon-button" type="button" onClick={onRefresh}>
            <RefreshCw className={`h-4 w-4 ${isBusy ? "animate-spin" : ""}`} />
          </button>
        }
      />

      <div className="mt-5 flex flex-col gap-3">
        <button
          className="ghost-button w-full justify-center"
          type="button"
          onClick={() => fileInputRef.current?.click()}
        >
          <FolderUp className="h-4 w-4" />
          Agregar fuentes
        </button>
        <input
          ref={fileInputRef}
          className="hidden"
          type="file"
          multiple
          accept=".pdf,.txt,.md,.csv"
          onChange={(event) => {
            const files = Array.from(event.target.files ?? []);
            if (files.length) {
              onUpload(files);
            }
            event.currentTarget.value = "";
          }}
        />

        <div className="input-shell">
          <Search className="h-4 w-4 text-[color:var(--muted)]" />
          <input
            className="w-full bg-transparent text-sm outline-none placeholder:text-[color:var(--muted)]"
            placeholder="Buscar fuentes indexadas o cargadas"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
          />
        </div>

        <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
          <span>Fuentes vivas</span>
          <button className="text-[color:var(--accent)]" type="button" onClick={onReindex}>
            Reindexar
          </button>
        </div>
      </div>

      <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1">
        {sources.length ? (
          sources.map((source) => (
            <article className="source-row" key={source.source_path}>
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[color:var(--surface-strong)]">
                <FileText className="h-5 w-5 text-[color:var(--accent)]" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-[color:var(--text)]">
                  {source.file_name}
                </p>
                <p className="mt-1 text-xs text-[color:var(--muted)]">
                  {formatFileSize(source.file_size)} · {source.chunk_count} chunks
                </p>
              </div>
              <div className="flex items-center gap-2">
                {source.is_indexed ? (
                  <span className="status-badge status-badge-ready">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Activa
                  </span>
                ) : (
                  <span className="status-badge status-badge-warning">Pendiente</span>
                )}
              </div>
            </article>
          ))
        ) : (
          <div className="empty-panel">
            <p className="text-base font-semibold text-[color:var(--text)]">
              Todavia no hay fuentes cargadas
            </p>
            <p className="mt-2 text-sm text-[color:var(--muted)]">
              Sube archivos o colocalos en <code>data/raw</code> para que el RAG pueda usarlos.
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
