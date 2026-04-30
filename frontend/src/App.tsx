import { useCallback, useDeferredValue, useEffect, useState, useTransition } from "react";
import { Database, PanelsTopLeft, SlidersHorizontal } from "lucide-react";

import ChatPanel from "./components/ChatPanel";
import ResizeHandle from "./components/ResizeHandle";
import SourcesPanel from "./components/SourcesPanel";
import StudioPanel from "./components/StudioPanel";
import { fetchDashboard, deleteSource, runIngestion, sendChat, uploadSources } from "./lib/api";
import type { ChatMessage, DashboardResponse } from "./types";

const DEFAULT_PANEL_WIDTH = 280;
const MIN_PANEL_WIDTH = 200;
const MAX_PANEL_WIDTH = 480;

function nowLabel(): string {
  return new Intl.DateTimeFormat("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function initialAssistantMessage(): ChatMessage {
  return {
    id: "assistant-welcome",
    role: "assistant",
    content:
      "Estoy listo para trabajar con tus fuentes indexadas. Puedes cargar nuevos documentos, reindexar el conocimiento y hacer preguntas apoyadas por el contexto disponible.",
    timestampLabel: nowLabel(),
  };
}

export default function App() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([initialAssistantMessage()]);
  const [composer, setComposer] = useState("");
  const [banner, setBanner] = useState<string | null>(null);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [leftWidth, setLeftWidth] = useState(DEFAULT_PANEL_WIDTH);
  const [rightWidth, setRightWidth] = useState(DEFAULT_PANEL_WIDTH);
  const [mobilePanel, setMobilePanel] = useState<"sources" | "studio" | null>(null);
  const [sourceQuery, setSourceQuery] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [isRefreshing, startRefreshing] = useTransition();

  const deferredSourceQuery = useDeferredValue(sourceQuery);

  async function loadDashboard() {
    const payload = await fetchDashboard();
    setDashboard(payload);
  }

  useEffect(() => {
    void loadDashboard().catch((error: Error) => {
      setBanner(error.message);
    });
  }, []);

  const filteredSources = (dashboard?.sources ?? []).filter((source) => {
    const query = deferredSourceQuery.trim().toLowerCase();
    if (!query) {
      return true;
    }
    return (
      source.file_name.toLowerCase().includes(query) ||
      source.source_path.toLowerCase().includes(query)
    );
  });

  function refreshDashboard() {
    startRefreshing(() => {
      void loadDashboard().catch((error: Error) => {
        setBanner(error.message);
      });
    });
  }

  async function handleReindex() {
    setBanner("Reconstruyendo el indice vectorial...");
    setIsBusy(true);
    try {
      const report = await runIngestion(true);
      await loadDashboard();
      setBanner(
        `Indice actualizado: ${report.files_processed} archivo(s) y ${report.chunks_created} chunk(s).`,
      );
    } catch (error) {
      setBanner(error instanceof Error ? error.message : "No se pudo reindexar.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUpload(files: File[]) {
    setBanner("Cargando nuevas fuentes y actualizando el RAG...");
    setIsBusy(true);
    try {
      const uploadReport = await uploadSources(files);
      await runIngestion(true);
      await loadDashboard();
      const uploadedCount = uploadReport.uploaded_files.length;
      const rejectedCount = uploadReport.rejected_files.length;
      setBanner(
        rejectedCount
          ? `${uploadedCount} fuente(s) agregadas. ${rejectedCount} archivo(s) se rechazaron por formato.`
          : `${uploadedCount} fuente(s) agregadas e indexadas correctamente.`,
      );
    } catch (error) {
      setBanner(error instanceof Error ? error.message : "No se pudo cargar la fuente.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(sourcePath: string) {
    const fileName = sourcePath.split("/").pop() ?? sourcePath;
    setBanner(`Eliminando "${fileName}"...`);
    setIsBusy(true);
    try {
      await deleteSource(sourcePath);
      await loadDashboard();
      setBanner(`Fuente "${fileName}" eliminada correctamente.`);
    } catch (error) {
      setBanner(error instanceof Error ? error.message : "No se pudo eliminar la fuente.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSendMessage() {
    const question = composer.trim();
    if (!question || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      timestampLabel: nowLabel(),
    };

    setMessages((current) => [...current, userMessage]);
    setComposer("");
    setIsSending(true);

    try {
      const response = await sendChat(question);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        timestampLabel: nowLabel(),
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "No pude completar la respuesta en este momento.",
          timestampLabel: nowLabel(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  const handleLeftResize = useCallback((w: number) => setLeftWidth(w), []);
  const handleRightResize = useCallback((w: number) => setRightWidth(w), []);

  const summary = dashboard?.summary ?? null;
  const health = dashboard?.health ?? null;

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-[color:var(--bg)] text-[color:var(--text)]">
      <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top_left,rgba(186,74,27,0.18),transparent_36%),radial-gradient(circle_at_top_right,rgba(62,96,79,0.14),transparent_30%)]" />
      <div className="relative mx-auto flex h-full w-full max-w-[1600px] flex-col px-4 py-4 lg:px-6 lg:py-6">
        {/* Mobile Navbar */}
        <div className="mb-4 flex shrink-0 items-center justify-between lg:hidden">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-[color:var(--accent)]" />
            <span className="font-heading text-xl text-[color:var(--text)]">RAG Portable</span>
          </div>
          <div className="flex gap-2">
            <button className="icon-button h-10 w-10" type="button" onClick={() => setMobilePanel("sources")}>
              <PanelsTopLeft className="h-4 w-4" />
            </button>
            <button className="icon-button h-10 w-10" type="button" onClick={() => setMobilePanel("studio")}>
              <SlidersHorizontal className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Floating Toast Banner */}
        {banner ? (
          <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 shadow-xl banner-shell px-6 py-3 animate-in fade-in slide-in-from-top-4">
            {banner}
          </div>
        ) : null}

        <div className="flex flex-1 min-h-0 gap-0 overflow-hidden">
          {/* Mobile drawers */}
          <div className={`${mobilePanel === "sources" ? "drawer-open" : "drawer-closed"} drawer-shell lg:hidden`}>
            <div className="drawer-backdrop" onClick={() => setMobilePanel(null)} />
            <div className="drawer-panel">
              <SourcesPanel
                sources={filteredSources}
                collapsed={false}
                isBusy={isBusy || isRefreshing}
                onToggle={() => setMobilePanel(null)}
                onUpload={handleUpload}
                onDelete={handleDelete}
                onReindex={handleReindex}
                onRefresh={refreshDashboard}
                query={sourceQuery}
                onQueryChange={setSourceQuery}
              />
            </div>
          </div>

          <div className={`${mobilePanel === "studio" ? "drawer-open" : "drawer-closed"} drawer-shell lg:hidden`}>
            <div className="drawer-backdrop" onClick={() => setMobilePanel(null)} />
            <div className="drawer-panel drawer-panel-right">
              <StudioPanel
                cards={dashboard?.studio_cards ?? []}
                collapsed={false}
                isBusy={isBusy}
                onReindex={handleReindex}
                onRefresh={refreshDashboard}
                onToggle={() => setMobilePanel(null)}
                summary={summary}
              />
            </div>
          </div>

          {/* Desktop: Left panel */}
          <div
            className="hidden shrink-0 lg:flex lg:h-full"
            style={{ width: leftCollapsed ? undefined : `${leftWidth}px` }}
          >
            <SourcesPanel
              sources={filteredSources}
              collapsed={leftCollapsed}
              isBusy={isBusy || isRefreshing}
              onToggle={() => setLeftCollapsed((current) => !current)}
              onUpload={handleUpload}
              onDelete={handleDelete}
              onReindex={handleReindex}
              onRefresh={refreshDashboard}
              query={sourceQuery}
              onQueryChange={setSourceQuery}
            />
          </div>

          {/* Left resize handle */}
          {!leftCollapsed && (
            <div className="hidden lg:flex">
              <ResizeHandle
                side="left"
                currentWidth={leftWidth}
                onResize={handleLeftResize}
                minWidth={MIN_PANEL_WIDTH}
                maxWidth={MAX_PANEL_WIDTH}
              />
            </div>
          )}

          {/* Center: Chat panel */}
          <div className="flex min-w-0 flex-1 h-full">
            <ChatPanel
              composer={composer}
              health={health}
              isSending={isSending}
              messages={messages}
              onComposerChange={setComposer}
              onSend={handleSendMessage}
              summary={summary}
            />
          </div>

          {/* Right resize handle */}
          {!rightCollapsed && (
            <div className="hidden lg:flex">
              <ResizeHandle
                side="right"
                currentWidth={rightWidth}
                onResize={handleRightResize}
                minWidth={MIN_PANEL_WIDTH}
                maxWidth={MAX_PANEL_WIDTH}
              />
            </div>
          )}

          {/* Desktop: Right panel */}
          <div
            className="hidden shrink-0 lg:flex lg:h-full"
            style={{ width: rightCollapsed ? undefined : `${rightWidth}px` }}
          >
            <StudioPanel
              cards={dashboard?.studio_cards ?? []}
              collapsed={rightCollapsed}
              isBusy={isBusy}
              onReindex={handleReindex}
              onRefresh={refreshDashboard}
              onToggle={() => setRightCollapsed((current) => !current)}
              summary={summary}
            />
          </div>
        </div>

        <footer className="shrink-0 flex items-center text-[10px] font-bold tracking-widest uppercase opacity-75">
          <div className={`flex items-center gap-1.5 ${health?.ollama_connected ? "text-[color:var(--ready)]" : "text-[color:var(--accent)]"}`}>
            <div className={`h-1.5 w-1.5 rounded-full ${health?.ollama_connected ? "bg-[color:var(--ready)]" : "bg-[color:var(--accent)]"}`} />
            {health?.ollama_connected ? "Ollama Online" : "Ollama Offline"}
          </div>
        </footer>
      </div>
    </div>
  );
}
