"use client";

import { useState } from "react";
import { showToast } from "./Toast";

interface ChatMessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  showActions?: boolean;
}

export default function ChatMessage({
  role,
  content,
  showActions = false,
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      showToast("success", "Copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      showToast("error", "Failed to copy");
    }
  };

  if (role === "user") {
    return (
      <div className="flex justify-end message-enter">
        <div className="max-w-[80%] bg-gray-900 text-white rounded-2xl rounded-br-md px-4 py-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    );
  }

  if (role === "system") {
    return (
      <div className="flex justify-center message-enter">
        <div className="text-xs text-gray-400 bg-gray-100 px-3 py-1.5 rounded-full">
          {content}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex gap-3 message-enter">
      {/* Avatar */}
      <div className="flex-shrink-0 w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center mt-0.5">
        <span className="text-blue-600 font-bold text-[11px]">CF</span>
      </div>

      <div className="flex-1 min-w-0 group">
        <div className="text-[11px] font-medium text-gray-400 mb-1">
          ContextForge
        </div>
        <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
          {content}
        </div>

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2 py-1 text-[11px] text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            >
              {copied ? (
                <>
                  <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                  Copy
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
