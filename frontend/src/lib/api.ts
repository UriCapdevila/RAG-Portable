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

export function sendChat(question: string): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
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
