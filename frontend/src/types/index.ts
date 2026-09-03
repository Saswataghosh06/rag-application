export interface SourceCitation {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  page_number?: number;
  score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  upload_date: string;
  chunk_count: number;
  file_size: number;
}

export interface ChatRequest {
  query: string;
  conversation_id?: string;
  top_k?: number;
}

export interface StreamEvent {
  type: 'token' | 'sources' | 'done' | 'error';
  data: any;
  conversation_id?: string;
}

export interface UploadResponse {
  id: string;
  filename: string;
  chunks_created: number;
  status: string;
  message: string;
}