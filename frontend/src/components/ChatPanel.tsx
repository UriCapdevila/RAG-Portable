import { useEffect, useRef } from "react";
import { Bot, CheckCircle2, LoaderCircle, MessageSquareQuote, SendHorizonal, TriangleAlert } from "lucide-react";

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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleInput = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    onComposerChange(event.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  useEffect(() => {
    if (textareaRef.current && composer === "") {
      textareaRef.current.style.height = "auto";
    }
  }, [composer]);

  return (
    <main className="panel-surface flex h-full w-full flex-col overflow-hidden p-5">
      <div className="flex shrink-0 items-start justify-between gap-4 border-b border-[color:var(--stroke)] pb-4">
        <div className="flex items-center gap-2">
          <p className="text-[0.75rem] uppercase tracking-[0.2em] text-[color:var(--accent)]">
            Chat
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

      <div className="mt-5 flex flex-col gap-4 flex-1 min-h-0 overflow-y-auto pr-2 pb-2">
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
            {message.role === "assistant" && (message.grounded !== undefined || message.retrievalStrategy) ? (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {message.grounded !== undefined ? (
                  <span className={`status-badge ${message.grounded ? "status-badge-ready" : "status-badge-warning"}`}>
                    {message.grounded ? <CheckCircle2 className="h-3.5 w-3.5" /> : <TriangleAlert className="h-3.5 w-3.5" />}
                    {message.grounded ? "Grounded" : "Baja evidencia"}
                  </span>
                ) : null}
                {message.retrievalStrategy ? (
                  <span className="status-badge status-badge-neutral">
                    Retrieval: {message.retrievalStrategy}
                  </span>
                ) : null}
              </div>
            ) : null}
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
              Consultando el índice y preparando una respuesta grounded...
            </div>
          </div>
        ) : null}
      </div>

      <form
        className="mt-5 shrink-0 rounded-[28px] border border-[color:var(--stroke)] bg-[color:var(--surface-strong)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]"
        onSubmit={(event) => {
          event.preventDefault();
          onSend();
        }}
      >
        <textarea
          ref={textareaRef}
          className="min-h-[44px] max-h-[240px] w-full resize-none bg-transparent text-[15px] leading-6 text-[color:var(--text)] outline-none placeholder:text-[color:var(--muted)]"
          placeholder="Comienza a escribir..."
          value={composer}
          onChange={handleInput}
          rows={1}
        />
        <div className="mt-3 flex justify-end">
          <button className="accent-button !px-5 !py-2 !text-sm" disabled={isSending} type="submit">
            {isSending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SendHorizonal className="h-4 w-4" />}
            Enviar
          </button>
        </div>
      </form>
    </main>
  );
}
