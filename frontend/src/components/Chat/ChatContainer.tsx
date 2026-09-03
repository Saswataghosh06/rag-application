'use client';

import { useChat } from '@/hooks/useChat';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { Trash2 } from 'lucide-react';

interface ChatContainerProps {
  hasDocuments: boolean;
}

export function ChatContainer({ hasDocuments }: ChatContainerProps) {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();

  return (
    <div className="flex h-full flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-surface-200 px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold text-surface-800">Chat</h1>
          <p className="text-xs text-surface-500">
            {hasDocuments
              ? 'Ask questions about your documents'
              : 'Upload documents to start chatting'
            }
          </p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-surface-500 hover:bg-surface-100 hover:text-surface-700 transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear chat
          </button>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-2 rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        isLoading={isLoading}
        disabled={!hasDocuments}
      />
    </div>
  );
}