import type {
  ChatResponse,
  DashboardResponse,
  DeleteSourceResponse,
  IngestionResponse,
  UploadResponse,
} from "../types";

async function requestJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail =
      typeof payload?.detail === "string" ? payload.detail : "La solicitud fallo.";
    throw new Error(detail);
  }

  return payload as T;
}

async function requestBlob(input: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(input, init);

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail =
      typeof payload?.detail === "string" ? payload.detail : "La solicitud fallo.";
    throw new Error(detail);
  }

  return response.blob();
}

export type TTSStatus = {
  enabled: boolean;
  voice: string;
  lang: string;
  speed: number;
};

export function fetchTTSStatus(): Promise<TTSStatus> {
  return requestJson<TTSStatus>("/api/tts/status");
}

export function synthesizeSpeech(
  text: string,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return requestBlob("/api/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal: options?.signal,
  });
}

export function fetchDashboard(): Promise<DashboardResponse> {
  return requestJson<DashboardResponse>("/api/dashboard");
}

export function runIngestion(rebuildIndex = true): Promise<IngestionResponse> {
  return requestJson<IngestionResponse>("/api/ingestion/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rebuild_index: rebuildIndex }),
  });
}

export function sendChat(question: string, conversationId: string | null): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, conversation_id: conversationId }),
  });
}

export function uploadSources(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  return requestJson<UploadResponse>("/api/sources/upload", {
    method: "POST",
    body: formData,
  });
}

export function deleteSource(sourcePath: string): Promise<DeleteSourceResponse> {
  return requestJson<DeleteSourceResponse>("/api/sources/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_path: sourcePath }),
  });
}
