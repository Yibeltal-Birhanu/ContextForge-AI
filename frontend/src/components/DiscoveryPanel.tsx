"use client";

import type { Question } from "@/types/project";
import QuestionCard from "./QuestionCard";

interface DiscoveryPanelProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (field: string, answer: string) => void;
}

export default function DiscoveryPanel({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
}: DiscoveryPanelProps) {
  const progressPercent = (questionNumber / totalQuestions) * 100;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Intro message */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 mb-6">
        <div className="flex items-start gap-3">
          <div className="text-2xl">🏗️</div>
          <div>
            <p className="text-gray-800 font-medium">
              I understand the basic idea.
            </p>
            <p className="text-gray-600 text-sm mt-1">
              Before I design the system, I need to clarify a few things.
            </p>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-600">
            Question {questionNumber} of {totalQuestions}
          </span>
          <span className="text-sm text-gray-400">Discovery</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Question card */}
      <QuestionCard
        question={question.question}
        reason={question.reason}
        field={question.field}
        onAnswer={(answer) => onAnswer(question.field, answer)}
      />
    </div>
  );
}
