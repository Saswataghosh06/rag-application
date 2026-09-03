'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar/Sidebar';
import { ChatContainer } from '@/components/Chat/ChatContainer';
import { api } from '@/lib/api';
import { Database, Cpu, Box, AlertCircle, CheckCircle } from 'lucide-react';

export default function Home() {
  const [hasDocuments, setHasDocuments] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [statusInfo, setStatusInfo] = useState<{ llm: string; vectorDb: string; embedding: string } | null>(null);

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await api.healthCheck();
      setBackendStatus('online');
      setStatusInfo({
        llm: health.llm_provider,
        vectorDb: health.vector_db,
        embedding: health.embedding_provider,
      });
    } catch {
      setBackendStatus('offline');
    }
  };

  const handleDocumentCountChange = (count: number) => {
    setHasDocuments(count > 0);
  };

  return (
    <main className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar onDocumentCountChange={handleDocumentCountChange} />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Status bar */}
        <div className="flex items-center justify-between border-b border-surface-200 bg-white px-4 py-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {backendStatus === 'online' ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : backendStatus === 'offline' ? (
                <AlertCircle className="h-4 w-4 text-red-500" />
              ) : (
                <div className="h-4 w-4 rounded-full bg-surface-300 animate-pulse-slow" />
              )}
              <span className="text-xs text-surface-500">
                {backendStatus === 'online' ? 'Backend Connected' : 
                 backendStatus === 'offline' ? 'Backend Offline' : 'Checking...'}
              </span>
            </div>
            
            {statusInfo && (
              <>
                <div className="h-4 w-px bg-surface-200" />
                <div className="flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-surface-400" />
                  <span className="text-xs text-surface-400">{statusInfo.llm}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-surface-400" />
                  <span className="text-xs text-surface-400">{statusInfo.vectorDb}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Box className="h-3.5 w-3.5 text-surface-400" />
                  <span className="text-xs text-surface-400">{statusInfo.embedding}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Chat */}
        <ChatContainer hasDocuments={hasDocuments || backendStatus === 'offline'} />
      </div>
    </main>
  );
}