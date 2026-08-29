"use client";

import type { PipelineStage } from "@/types/project";

interface PipelineIndicatorProps {
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

export default function PipelineIndicator({ stage }: PipelineIndicatorProps) {
  const currentIndex = stages.findIndex((s) => s.key === stage);

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {stages.map((s, index) => {
        const isComplete = stage === "complete" && index < stages.length - 1;
        const isActive = s.key === stage && stage !== "complete";
        const isPast = index < currentIndex;

        return (
          <div key={s.key} className="flex items-center gap-1">
            <div
              className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                isActive
                  ? "bg-blue-100 text-blue-700"
                  : isComplete
                  ? "text-green-600"
                  : isPast
                  ? "text-blue-500"
                  : "text-gray-400"
              }`}
            >
              {isComplete ? (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : isActive ? (
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
              )}
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {index < stages.length - 1 && (
              <div
                className={`w-3 h-px ${
                  isPast || isComplete ? "bg-blue-300" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
