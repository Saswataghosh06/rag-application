'use client';

import { useState } from 'react';
import { FileStack, Settings, ChevronLeft, ChevronRight, Database, Cpu, Box } from 'lucide-react';
import { DocumentUpload } from '../Documents/DocumentUpload';
import { DocumentList } from '../Documents/DocumentList';
import { useDocuments } from '@/hooks/useDocuments';
import { cn } from '@/lib/utils';

interface SidebarProps {
  onDocumentCountChange: (count: number) => void;
}

export function Sidebar({ onDocumentCountChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { documents, isLoading, isUploading, uploadDocument, deleteDocument, refreshDocuments } = useDocuments();

  // Notify parent of document count changes
  const handleUpload = async (file: File) => {
    const result = await uploadDocument(file);
    onDocumentCountChange(documents.length + 1);
    return result;
  };

  const handleDelete = async (id: string) => {
    await deleteDocument(id);
    onDocumentCountChange(documents.length - 1);
  };

  return (
    <div className={cn(
      'flex flex-col border-r border-surface-200 bg-surface-50 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-80'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-surface-200 p-4">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <FileStack className="h-5 w-5 text-brand-600" />
            <h2 className="font-semibold text-surface-800">Documents</h2>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-surface-400 hover:bg-surface-200 hover:text-surface-600 transition-colors"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Upload section */}
          <DocumentUpload onUpload={handleUpload} isUploading={isUploading} />

          {/* Document list */}
          <DocumentList
            documents={documents}
            isLoading={isLoading}
            onDelete={handleDelete}
            onRefresh={refreshDocuments}
          />
        </div>
      )}

      {isCollapsed && (
        <div className="flex flex-col items-center py-4">
          <FileStack className="h-5 w-5 text-surface-400" />
          <span className="mt-1 text-xs text-surface-400">{documents.length}</span>
        </div>
      )}
    </div>
  );
}
