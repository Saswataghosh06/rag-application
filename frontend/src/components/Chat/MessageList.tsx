'use client';

import { useEffect, useRef } from 'react';
import { Message } from '@/types';
import { MessageBubble } from './MessageBubble';
import { FileQuestion } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50">
            <FileQuestion className="h-8 w-8 text-brand-500" />
          </div>
          <h3 className="text-lg font-semibold text-surface-800">
            No messages yet
          </h3>
          <p className="mt-2 text-sm text-surface-500">
            Upload some documents and ask questions about them. 
            The AI will search through your documents and provide answers with citations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-6">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}