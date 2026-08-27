"use client";

import type { PipelineStage } from "@/types/project";

interface ProgressStepsProps {
  stage: PipelineStage;
}

const stages: { key: PipelineStage; label: string }[] = [
  { key: "discovery", label: "Discovery" },
  { key: "requirements", label: "Requirements" },
  { key: "architecture", label: "Architecture" },
  { key: "context", label: "Context" },
  { key: "validation", label: "Validation" },
  { key: "complete", label: "Ready" },
];

export default function ProgressSteps({ stage }: ProgressStepsProps) {
  const currentIndex = stages.findIndex((s) => s.key === stage);

  return (
    <div className="flex items-center justify-center space-x-1 mb-8 max-w-3xl mx-auto">
      {stages.map((s, index) => {
        const isActive = index <= currentIndex;
        const isCurrent = s.key === stage;
        const isComplete = stage === "complete" && index < stages.length - 1;

        return (
          <div key={s.key} className="flex items-center">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                isCurrent
                  ? "bg-blue-600 text-white shadow-md"
                  : isComplete
                  ? "bg-green-100 text-green-700"
                  : isActive
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {isComplete ? (
                <span className="text-green-600">✓</span>
              ) : isCurrent ? (
                <span className="animate-pulse">●</span>
              ) : (
                <span>○</span>
              )}
              {s.label}
            </div>
            {index < stages.length - 1 && (
              <div
                className={`w-6 h-0.5 mx-1 ${
                  index < currentIndex || isComplete
                    ? "bg-blue-400"
                    : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
