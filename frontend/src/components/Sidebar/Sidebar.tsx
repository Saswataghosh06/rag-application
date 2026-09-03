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
      'relative flex flex-col bg-white border-r border-surface-200 transition-all duration-300 z-10',
      isCollapsed ? 'w-16' : 'w-80'
    )}>
      {/* Premium Header */}
      <div className="flex items-center justify-between border-b border-surface-200 px-4 py-4 bg-surface-50/50">
        {!isCollapsed && (
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-glow">
              <FileStack className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-surface-800 tracking-tight">Knowledge Base</h2>
              <p className="text-[10px] text-surface-400 font-medium uppercase tracking-wider">Enterprise RAG</p>
            </div>
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
        <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin">
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
        <div className="flex flex-col items-center py-4 space-y-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-glow">
            <FileStack className="h-5 w-5" />
          </div>
          <div className="h-px w-8 bg-surface-200"></div>
          <span className="text-[10px] font-bold text-surface-400">{documents.length}</span>
        </div>
      )}
    </div>
  );
}