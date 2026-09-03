import { ChatRequest, StreamEvent, DocumentInfo, UploadResponse } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new ApiError(response.status, error.detail || 'An error occurred');
  }
  return response.json();
}

export const api = {
  // Chat endpoints
  async chat(request: ChatRequest) {
    const response = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<{ message: string; sources: any[]; conversation_id: string }>(response);
  },

  async *streamChat(request: ChatRequest): AsyncGenerator<StreamEvent> {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new ApiError(response.status, error.detail || 'An error occurred');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event: StreamEvent = JSON.parse(line.slice(6));
            yield event;
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  },

  // Document endpoints
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<UploadResponse>(response);
  },

  async getDocuments(): Promise<DocumentInfo[]> {
    const response = await fetch(`${API_BASE}/documents/`);
    return handleResponse<DocumentInfo[]>(response);
  },

  async deleteDocument(id: string): Promise<void> {
    const response = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
      throw new ApiError(response.status, error.detail || 'Delete failed');
    }
  },

  // Health check
  async healthCheck() {
    const response = await fetch(`${API_BASE.replace('/api/v1', '')}/health`);
    return handleResponse<{
      status: string;
      llm_provider: string;
      vector_db: string;
      embedding_provider: string;
    }>(response);
  },
};