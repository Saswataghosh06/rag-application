'use client';

import { User, Bot, Loader2 } from 'lucide-react';
import { Message } from '@/types';
import { cn } from '@/lib/utils';
import { SourceCitationList } from './SourceCitation';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={cn(
      'flex gap-3 animate-fade-in',
      isUser ? 'flex-row-reverse' : 'flex-row'
    )}>
      {/* Avatar */}
      <div className={cn(
        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
        isUser
          ? 'bg-brand-600 text-white'
          : 'bg-surface-200 text-surface-700'
      )}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div className={cn(
        'max-w-[80%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-brand-600 text-white rounded-tr-md'
          : 'bg-surface-100 text-surface-800 rounded-tl-md'
      )}>
        {message.isStreaming && !message.content ? (
          <div className="flex items-center gap-2 text-surface-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Searching documents...</span>
          </div>
        ) : (
          <>
            <div className={cn(
              'text-sm leading-relaxed prose prose-sm max-w-none',
              isUser ? 'prose-invert' : 'prose-slate'
            )}>
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="mb-2 ml-4 list-disc">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  code: ({ children, className }) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="rounded bg-surface-200 px-1.5 py-0.5 text-xs font-mono">
                        {children}
                      </code>
                    ) : (
                      <code className={className}>{children}</code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
            
            {/* Streaming cursor */}
            {message.isStreaming && message.content && (
              <span className="inline-block w-2 h-4 bg-brand-500 animate-pulse ml-0.5" />
            )}
          </>
        )}

        {/* Sources (only for assistant) */}
        {!isUser && message.sources && message.sources.length > 0 && !message.isStreaming && (
          <div className="mt-2">
            <SourceCitationList sources={message.sources} />
          </div>
        )}
      </div>
    </div>
  );
}