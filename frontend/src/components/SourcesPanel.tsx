import { useRef } from "react";
import {
  CheckCircle2,
  Database,
  FileText,
  FolderUp,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import PanelHeader from "./PanelHeader";
import type { SourceRecord } from "../types";

type SourcesPanelProps = {
  collapsed?: boolean;
  isBusy: boolean;
  onToggle: () => void;
  onUpload: (files: File[]) => void;
  onDelete: (sourcePath: string) => void;
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
  onDelete,
  onReindex,
  onRefresh,
  query,
  onQueryChange,
  sources,
}: SourcesPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const indexedSources = sources.filter((source) => source.is_indexed).length;

  function handleDeleteClick(source: SourceRecord) {
    const confirmed = window.confirm(
      `¿Seguro que deseas eliminar "${source.file_name}"?\n\nEsto eliminará el archivo y sus chunks del índice vectorial.`,
    );
    if (confirmed) {
      onDelete(source.source_path);
    }
  }

  if (collapsed) {
    return (
      <aside className="panel-surface hidden h-full w-[5.25rem] shrink-0 lg:flex lg:flex-col lg:items-center lg:gap-4 lg:p-4">
        <PanelHeader title="Fuentes" collapsed side="left" onToggle={onToggle} />
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
    <aside className="panel-surface flex h-full w-full flex-col overflow-hidden p-5">
      <PanelHeader
        title="Fuentes"
        side="left"
        onToggle={onToggle}
        rightSlot={
          <button className="icon-button" type="button" onClick={onRefresh}>
            <RefreshCw className={`h-4 w-4 ${isBusy ? "animate-spin" : ""}`} />
          </button>
        }
      />

      <div className="mt-5 flex shrink-0 flex-col gap-3">
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


      </div>

      <div className="mt-4 flex flex-col space-y-3 flex-1 min-h-0 overflow-y-auto pr-2 pb-2">
        {sources.length ? (
          sources.map((source) => (
            <article className="source-row group" key={source.source_path}>
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[color:var(--surface-strong)]">
                <FileText className="h-5 w-5 text-[color:var(--accent)]" />
              </div>
              <div className="min-w-0 flex-1 overflow-hidden">
                <p className="truncate text-sm font-semibold text-[color:var(--text)]">
                  {source.file_name}
                </p>
                <p className="mt-0.5 truncate text-xs text-[color:var(--muted)]">
                  {formatFileSize(source.file_size)} · {source.chunk_count} chunks
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                {source.is_indexed ? (
                  <span className="status-badge status-badge-ready" title="Activa">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  </span>
                ) : (
                  <span className="status-badge status-badge-warning" title="Pendiente">●</span>
                )}
                <button
                  className="delete-source-button"
                  type="button"
                  title={`Eliminar ${source.file_name}`}
                  aria-label={`Eliminar ${source.file_name}`}
                  disabled={isBusy}
                  onClick={() => handleDeleteClick(source)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
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
