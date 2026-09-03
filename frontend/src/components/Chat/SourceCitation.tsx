'use client';

import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { SourceCitation as SourceCitationType } from '@/types';
import { cn, truncateText } from '@/lib/utils';

interface SourceCitationProps {
  source: SourceCitationType;
  index: number;
}

export function SourceCitation({ source, index }: SourceCitationProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="group rounded-lg border border-surface-200 bg-surface-50 hover:border-brand-200 hover:bg-brand-50/30 transition-all">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center gap-3 p-3 text-left"
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-100 text-brand-700 text-sm font-medium">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-surface-500" />
            <span className="text-sm font-medium text-surface-800 truncate">
              {source.document_name}
            </span>
            {source.page_number && (
              <span className="text-xs text-surface-400">
                p. {source.page_number}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-surface-500">
            Relevance: {(source.score * 100).toFixed(0)}%
          </p>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-surface-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-surface-400" />
        )}
      </button>
      
      {isExpanded && (
        <div className="border-t border-surface-200 p-3 pt-2 animate-fade-in">
          <p className="text-sm text-surface-600 leading-relaxed whitespace-pre-wrap">
            {source.content}
          </p>
        </div>
      )}
    </div>
  );
}

interface SourceCitationListProps {
  sources: SourceCitationType[];
}

export function SourceCitationList({ sources }: SourceCitationListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center gap-2 text-xs font-medium text-surface-500 uppercase tracking-wider">
        <FileText className="h-3.5 w-3.5" />
        <span>Sources ({sources.length})</span>
      </div>
      <div className="space-y-1.5">
        {sources.map((source, index) => (
          <SourceCitation key={source.chunk_id} source={source} index={index} />
        ))}
      </div>
    </div>
  );
}