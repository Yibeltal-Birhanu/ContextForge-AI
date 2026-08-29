"use client";

import { useState } from "react";
import type { QualityInfo } from "@/types/project";
import { showToast } from "./Toast";

interface CompletionViewProps {
  projectName: string;
  downloadMarkdown: string;
  downloadTxt: string;
  quality: QualityInfo | null;
}

const CHECK_LABELS: Record<string, string> = {
  requirements_coverage: "Requirements",
  architecture_consistency: "Architecture",
  technology_consistency: "Technology",
  api_coverage: "API Coverage",
  data_model_coverage: "Data Model",
  security_coverage: "Security",
  implementation_coverage: "Implementation",
  agent_rules_quality: "Agent Rules",
  definition_of_done: "Definition of Done",
};

function getScoreColor(score: number): string {
  if (score >= 90) return "text-green-600";
  if (score >= 75) return "text-yellow-600";
  return "text-red-600";
}

function getScoreBarBg(score: number): string {
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-yellow-500";
  return "bg-red-500";
}

export default function CompletionView({
  projectName,
  downloadMarkdown,
  downloadTxt,
  quality,
}: CompletionViewProps) {
  const [showDetails, setShowDetails] = useState(false);
  const passed = quality?.ready_for_agent ?? true;

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

        {/* Completion card */}
        <div
          className={`rounded-xl border overflow-hidden max-w-lg ${
            passed
              ? "bg-green-50/50 border-green-200"
              : "bg-red-50/50 border-red-200"
          }`}
        >
          {/* Header */}
          <div className="px-5 py-4">
            <div className="flex items-center gap-3 mb-3">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  passed ? "bg-green-100" : "bg-red-100"
                }`}
              >
                {passed ? (
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900">
                  {passed ? "Engineering Context Ready" : "Context Needs Improvement"}
                </h3>
                <p className="text-xs text-gray-500">{projectName}</p>
              </div>
            </div>

            {/* Score summary */}
            {quality && (
              <div className="flex items-center gap-4 mb-3">
                <div>
                  <div className={`text-2xl font-bold ${passed ? "text-green-600" : "text-red-600"}`}>
                    {quality.overall_score}
                  </div>
                  <div className="text-[10px] text-gray-400">Overall</div>
                </div>
                <div className="h-8 w-px bg-gray-200" />
                <div>
                  <div className="text-base font-bold text-gray-700">{quality.validation_score}</div>
                  <div className="text-[10px] text-gray-400">Validation</div>
                </div>
                <div>
                  <div className="text-base font-bold text-gray-700">{quality.readiness_score}</div>
                  <div className="text-[10px] text-gray-400">Readiness</div>
                </div>
              </div>
            )}

            {/* Download buttons */}
            {passed && (
              <div className="flex gap-2">
                <a
                  href={downloadMarkdown}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => showToast("success", "Markdown download started")}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Markdown
                </a>
                <a
                  href={downloadTxt}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => showToast("success", "TXT download started")}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  TXT
                </a>
              </div>
            )}
          </div>

          {/* Quality breakdown */}
          {quality && (
            <div className="border-t border-gray-200/60">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="w-full px-5 py-2.5 flex items-center justify-between text-xs text-gray-500 hover:bg-gray-100/50 transition-colors"
              >
                <span>Quality Details</span>
                <svg
                  className={`w-3.5 h-3.5 transition-transform ${showDetails ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDetails && (
                <div className="px-5 pb-4">
                  <div className="space-y-1.5">
                    {Object.entries(quality.checks).map(([key, score]) => (
                      <div
                        key={key}
                        className="flex items-center justify-between py-1"
                      >
                        <span className="text-xs text-gray-600">
                          {CHECK_LABELS[key] || key}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${getScoreBarBg(
                                score as number
                              )}`}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs font-medium w-8 text-right ${getScoreColor(
                              score as number
                            )}`}
                          >
                            {score}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Warnings */}
                  {quality.warnings.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-[11px] font-medium text-yellow-600 mb-1">
                        {quality.warnings_count} Warning{quality.warnings_count !== 1 ? "s" : ""}
                      </p>
                      {quality.warnings.slice(0, 2).map((w, i) => (
                        <p key={i} className="text-[11px] text-gray-500">
                          {w.message}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Assumptions */}
                  {quality.assumptions.length > 0 && (
                    <div className="mt-2 pt-3 border-t border-gray-100">
                      <p className="text-[11px] font-medium text-blue-500 mb-1">
                        {quality.assumptions_count} AI Assumption{quality.assumptions_count !== 1 ? "s" : ""}
                      </p>
                      {quality.assumptions.slice(0, 2).map((a, i) => (
                        <p key={i} className="text-[11px] text-gray-500">
                          [{a.area}] {a.assumption}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer info */}
        {passed && (
          <p className="text-[11px] text-gray-400 mt-2 ml-10">
            Give this context to Cursor, Claude Code, Codex, or any AI coding agent.
          </p>
        )}
      </div>
    </div>
  );
}
