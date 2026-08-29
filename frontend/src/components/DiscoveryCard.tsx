"use client";

import { useState } from "react";
import type { Question } from "@/types/project";

interface DiscoveryCardProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (field: string, answer: string) => void;
  loading: boolean;
}

export default function DiscoveryCard({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  loading,
}: DiscoveryCardProps) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = () => {
    if (answer.trim() && !loading) {
      onAnswer(question.field, answer.trim());
      setAnswer("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const progressPercent = Math.round((questionNumber / totalQuestions) * 100);

  return (
    <div className="flex gap-3 message-enter">
      {/* Avatar */}
      <div className="flex-shrink-0 w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center mt-0.5">
        <span className="text-blue-600 font-bold text-[11px]">CF</span>
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-medium text-gray-400 mb-1">
          ContextForge
        </div>

        {/* Question card */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden max-w-lg">
          {/* Progress indicator */}
          <div className="px-4 py-2.5 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-gray-500">
                Discovery
              </span>
              <span className="text-[11px] text-gray-400">
                {questionNumber}/{totalQuestions}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <span className="text-[11px] text-gray-400">
                {progressPercent}%
              </span>
            </div>
          </div>

          {/* Question */}
          <div className="px-4 py-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">
              {question.question}
            </h3>
            {question.reason && (
              <p className="text-xs text-gray-400 mb-4">
                {question.reason}
              </p>
            )}

            {/* Answer input */}
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your answer..."
              rows={2}
              disabled={loading}
              className="w-full p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300 disabled:opacity-50"
              autoFocus
            />

            {/* Submit */}
            <div className="flex items-center justify-between mt-3">
              <span className="text-[11px] text-gray-400">
                <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Enter</kbd> to submit
              </span>
              <button
                onClick={handleSubmit}
                disabled={!answer.trim() || loading}
                className="px-4 py-1.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Thinking...
                  </span>
                ) : (
                  "Continue"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
