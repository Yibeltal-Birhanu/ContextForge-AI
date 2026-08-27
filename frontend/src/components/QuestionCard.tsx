"use client";

import { useState } from "react";

interface QuestionCardProps {
  question: string;
  reason: string;
  field: string;
  onAnswer: (answer: string) => void;
}

export default function QuestionCard({
  question,
  reason,
  field,
  onAnswer,
}: QuestionCardProps) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = () => {
    if (answer.trim()) {
      onAnswer(answer.trim());
      setAnswer("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
      {/* Question */}
      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        {question}
      </h3>

      {/* Reason */}
      <p className="text-gray-500 text-sm mb-5 flex items-center gap-2">
        <span className="inline-block w-1 h-1 bg-gray-400 rounded-full"></span>
        {reason}
      </p>

      {/* Answer input */}
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your answer..."
        rows={3}
        className="w-full p-4 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800 placeholder-gray-400"
        autoFocus
      />

      {/* Hint */}
      <p className="text-gray-400 text-xs mt-2 mb-4">
        Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-600">Enter</kbd> to submit, or click the button below
      </p>

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={!answer.trim()}
        className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        Continue →
      </button>
    </div>
  );
}
