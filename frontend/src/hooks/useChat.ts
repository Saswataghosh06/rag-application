'use client';

import { useState, useCallback, useRef } from 'react';
import { Message, SourceCitation, StreamEvent } from '@/types';
import { api } from '@/lib/api';
import { generateId } from '@/lib/utils';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string, topK?: number) => {
    if (!content.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Add placeholder for assistant message
    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      sources: [],
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);

    try {
      let fullContent = '';
      let sources: SourceCitation[] = [];
      let conversationId = '';

      for await (const event of api.streamChat({
        query: content,
        top_k: topK,
      })) {
        switch (event.type) {
          case 'sources':
            sources = event.data;
            conversationId = event.conversation_id || '';
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, sources }
                  : m
              )
            );
            break;

          case 'token':
            fullContent += event.data;
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, content: fullContent }
                  : m
              )
            );
            break;

          case 'done':
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMessage.id
                  ? { ...m, isStreaming: false }
                  : m
              )
            );
            break;

          case 'error':
            throw new Error(event.data);
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantMessage.id
            ? {
                ...m,
                content: `Error: ${errorMessage}`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
}