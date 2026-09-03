'use client';

import { useState, useCallback, useEffect } from 'react';
import { DocumentInfo, UploadResponse } from '@/types';
import { api } from '@/lib/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file: File): Promise<UploadResponse | null> => {
    setIsUploading(true);
    setError(null);
    try {
      const result = await api.uploadDocument(file);
      // Refresh document list after upload
      setTimeout(fetchDocuments, 1000); // Delay to allow background processing
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMsg);
      return null;
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  const deleteDocument = useCallback(async (id: string) => {
    setError(null);
    try {
      await api.deleteDocument(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return {
    documents,
    isLoading,
    isUploading,
    error,
    uploadDocument,
    deleteDocument,
    refreshDocuments: fetchDocuments,
  };
}