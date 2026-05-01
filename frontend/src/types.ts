export type HealthResponse = {
  ollama_connected: boolean;
  vector_store_ready: boolean;
  chat_model: string;
  embedding_model: string;
};

export type SourceRecord = {
  source_path: string;
  file_name: string;
  file_type: string;
  file_size: number | null;
  last_modified: string | null;
  chunk_count: number;
  is_indexed: boolean;
  is_available: boolean;
};

export type StudioCard = {
  id: string;
  title: string;
  description: string;
  value: string;
  status: string;
  action: string | null;
};

export type DashboardSummary = {
  total_sources: number;
  indexed_sources: number;
  total_chunks: number;
  raw_data_path: string;
  vector_db_path: string;
};

export type DashboardResponse = {
  health: HealthResponse;
  sources: SourceRecord[];
  summary: DashboardSummary;
  studio_cards: StudioCard[];
};

export type SourceResponse = {
  source_path: string;
  file_name: string;
  file_type: string;
};

export type ChunkResponse = {
  text: string;
  score: number | null;
  metadata: Record<string, unknown>;
};

export type ChatResponse = {
  answer: string;
  model: string;
  conversation_id: string;
  sources: SourceResponse[];
  retrieved_chunks: ChunkResponse[];
  grounded: boolean;
  retrieval_strategy: string;
};

export type IngestionResponse = {
  files_processed: number;
  chunks_created: number;
  vector_table: string;
  vector_db_path: string;
  embedding_model: string;
  source_files: string[];
};

export type UploadResponse = {
  uploaded_files: string[];
  rejected_files: string[];
};

export type DeleteSourceResponse = {
  source_path: string;
  file_deleted: boolean;
  chunks_deleted: boolean;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceResponse[];
  grounded?: boolean;
  retrievalStrategy?: string;
  timestampLabel: string;
};
