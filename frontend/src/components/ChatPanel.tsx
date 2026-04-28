import { ArrowUp, Bot, LoaderCircle, MessageSquareQuote, SendHorizonal } from "lucide-react";

import type { ChatMessage, DashboardSummary, HealthResponse } from "../types";

type ChatPanelProps = {
  composer: string;
  health: HealthResponse | null;
  isSending: boolean;
  messages: ChatMessage[];
  onComposerChange: (value: string) => void;
  onSend: () => void;
  summary: DashboardSummary | null;
};

function formatModelName(model: string | undefined): string {
  if (!model) {
    return "sin modelo";
  }
  return model.replace(":latest", "");
}

export default function ChatPanel({
  composer,
  health,
  isSending,
  messages,
  onComposerChange,
  onSend,
  summary,
}: ChatPanelProps) {
  return (
    <main className="panel-surface flex min-h-[70vh] flex-col overflow-hidden p-5 lg:min-h-0">
      <div className="flex items-start justify-between gap-4 border-b border-[color:var(--stroke)] pb-4">
        <div>
          <p className="text-[0.72rem] uppercase tracking-[0.24em] text-[color:var(--accent)]">
            Chat
          </p>
          <h1 className="mt-2 font-heading text-3xl text-[color:var(--text)]">
            Conversacion guiada por contexto
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-[color:var(--muted)]">
            El motor responde usando el conocimiento indexado y deja trazabilidad en cada
            mensaje.
          </p>
        </div>
        <div className="hidden items-center gap-2 lg:flex">
          <span className="status-chip">
            <Bot className="h-4 w-4" />
            {formatModelName(health?.chat_model)}
          </span>
          <span className="status-chip">
            <MessageSquareQuote className="h-4 w-4" />
            {summary?.indexed_sources ?? 0} fuentes
          </span>
        </div>
      </div>

      <div className="mt-5 flex flex-1 flex-col gap-4 overflow-y-auto pr-1">
        {messages.map((message) => (
          <article
            key={message.id}
            className={
              message.role === "assistant"
                ? "message-card message-assistant"
                : "message-card message-user self-end"
            }
          >
            <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em]">
              <span>{message.role === "assistant" ? "Asistente" : "Tu pregunta"}</span>
              <span className="text-[color:var(--muted)]">{message.timestampLabel}</span>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-[15px] leading-7 text-[color:var(--text)]">
              {message.content}
            </p>
            {message.sources?.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {message.sources.map((source) => (
                  <span className="source-pill" key={`${message.id}-${source.source_path}`}>
                    {source.file_name}
                  </span>
                ))}
              </div>
            ) : null}
          </article>
        ))}

        {isSending ? (
          <div className="message-card message-assistant">
            <div className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Consultando el indice y preparando una respuesta grounded...
            </div>
          </div>
        ) : null}
      </div>

      <form
        className="mt-5 rounded-[28px] border border-[color:var(--stroke)] bg-[color:var(--surface-strong)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
        onSubmit={(event) => {
          event.preventDefault();
          onSend();
        }}
      >
        <textarea
          className="min-h-[124px] w-full resize-none bg-transparent text-[15px] leading-7 text-[color:var(--text)] outline-none placeholder:text-[color:var(--muted)]"
          placeholder="Pregunta sobre politicas, procesos, hallazgos o cualquier dato disponible en tus fuentes..."
          value={composer}
          onChange={(event) => onComposerChange(event.target.value)}
        />
        <div className="mt-4 flex flex-col gap-3 border-t border-[color:var(--stroke)] pt-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-2 text-sm text-[color:var(--muted)]">
            <span className="status-chip">
              <ArrowUp className="h-4 w-4" />
              {summary?.total_chunks ?? 0} chunks persistidos
            </span>
            <span className="status-chip">
              <Bot className="h-4 w-4" />
              {health?.vector_store_ready ? "RAG listo" : "RAG pendiente"}
            </span>
          </div>

          <button className="accent-button" disabled={isSending} type="submit">
            {isSending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SendHorizonal className="h-4 w-4" />}
            Enviar
          </button>
        </div>
      </form>
    </main>
  );
}
