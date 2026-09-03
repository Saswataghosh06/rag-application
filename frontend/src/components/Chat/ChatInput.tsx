'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-surface-200 bg-white p-4">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-3 rounded-2xl border border-surface-200 bg-surface-50 p-2 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-100 transition-all">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            disabled={disabled}
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent px-3 py-2 text-surface-800 placeholder:text-surface-400',
              'focus:outline-none disabled:opacity-50',
              'text-sm leading-relaxed'
            )}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading || disabled}
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-xl transition-all',
              'bg-brand-600 text-white hover:bg-brand-700',
              'disabled:opacity-40 disabled:cursor-not-allowed',
              'active:scale-95'
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-surface-400">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}