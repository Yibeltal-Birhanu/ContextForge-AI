"use client";

import { useRef, useEffect, useCallback } from "react";

interface ComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  loading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export default function Composer({
  value,
  onChange,
  onSend,
  loading,
  disabled = false,
  placeholder = "Tell ContextForge what you want to build...",
}: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow the textarea
  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [value, adjustHeight]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !loading && !disabled) {
        onSend();
      }
    }
  };

  const handleSubmit = () => {
    if (value.trim() && !loading && !disabled) {
      onSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3 lg:px-6 lg:py-4">
      <div className="max-w-3xl mx-auto">
        <div className="relative flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-2 focus-within:border-gray-300 focus-within:ring-1 focus-within:ring-gray-300 transition-all">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={loading || disabled}
            rows={1}
            className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 resize-none outline-none py-1.5 max-h-[200px] disabled:opacity-50"
            style={{ minHeight: "24px" }}
          />
          <button
            onClick={handleSubmit}
            disabled={!value.trim() || loading || disabled}
            className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-900 text-white flex items-center justify-center hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-[11px] text-gray-400 mt-1.5 text-center">
          Press <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Enter</kbd> to send · <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
