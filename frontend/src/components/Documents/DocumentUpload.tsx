'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { UploadResponse } from '@/types';

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<UploadResponse | null>;
  isUploading: boolean;
}

const ACCEPTED_TYPES = {
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/csv': ['.csv'],
  'application/json': ['.json'],
};

const MAX_SIZE = 50 * 1024 * 1024; // 50MB

export function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [lastMessage, setLastMessage] = useState<string>('');

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      setUploadStatus('idle');
      const result = await onUpload(file);
      if (result) {
        setUploadStatus('success');
        setLastMessage(result.message);
      } else {
        setUploadStatus('error');
        setLastMessage('Upload failed');
      }
      // Reset status after 3 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setLastMessage('');
      }, 3000);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: true,
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all cursor-pointer',
          isDragActive
            ? 'border-brand-400 bg-brand-50'
            : 'border-surface-300 hover:border-brand-300 hover:bg-surface-50',
          isUploading && 'pointer-events-none opacity-60'
        )}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <>
            <Loader2 className="h-10 w-10 text-brand-500 animate-spin" />
            <p className="mt-3 text-sm font-medium text-surface-700">Uploading and processing...</p>
          </>
        ) : uploadStatus === 'success' ? (
          <>
            <CheckCircle className="h-10 w-10 text-green-500" />
            <p className="mt-3 text-sm font-medium text-green-700">{lastMessage}</p>
          </>
        ) : uploadStatus === 'error' ? (
          <>
            <AlertCircle className="h-10 w-10 text-red-500" />
            <p className="mt-3 text-sm font-medium text-red-700">{lastMessage}</p>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-surface-400" />
            <p className="mt-3 text-sm font-medium text-surface-700">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to select'}
            </p>
            <p className="mt-1 text-xs text-surface-400">
              Supports PDF, DOCX, TXT, MD, CSV, JSON (max 50MB)
            </p>
          </>
        )}
      </div>
    </div>
  );
}