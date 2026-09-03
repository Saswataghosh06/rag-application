'use client';

import { FileText, Trash2, RefreshCw } from 'lucide-react';
import { DocumentInfo } from '@/types';
import { formatFileSize, formatDate, cn } from '@/lib/utils';

interface DocumentListProps {
  documents: DocumentInfo[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onRefresh: () => void;
}

export function DocumentList({ documents, isLoading, onDelete, onRefresh }: DocumentListProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-surface-700">
          Documents ({documents.length})
        </h3>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1.5 text-xs text-surface-500 hover:text-surface-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn('h-3.5 w-3.5', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {documents.length === 0 ? (
        <p className="py-8 text-center text-sm text-surface-400">
          No documents uploaded yet
        </p>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="group flex items-center gap-3 rounded-lg border border-surface-200 bg-white p-3 hover:border-surface-300 transition-all"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-100">
                <FileText className="h-5 w-5 text-surface-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-surface-800 truncate">
                  {doc.filename}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-surface-400">
                    {formatFileSize(doc.file_size)}
                  </span>
                  <span className="text-xs text-surface-300">•</span>
                  <span className="text-xs text-surface-400">
                    {doc.chunk_count} chunks
                  </span>
                </div>
              </div>
              <button
                onClick={() => onDelete(doc.id)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-surface-400 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                title="Delete document"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}