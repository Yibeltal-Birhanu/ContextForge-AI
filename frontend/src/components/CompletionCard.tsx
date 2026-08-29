"use client";

import type { QualityInfo } from "@/types/project";
import QualityReport from "./QualityReport";

interface CompletionCardProps {
  projectName: string;
  downloadMarkdown: string;
  downloadTxt: string;
  quality: QualityInfo | null;
}

export default function CompletionCard({
  projectName,
  downloadMarkdown,
  downloadTxt,
  quality,
}: CompletionCardProps) {
  const passed = quality?.ready_for_agent ?? true;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Success header */}
      <div
        className={`rounded-2xl shadow-xl p-8 text-center ${
          passed
            ? "bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200"
            : "bg-gradient-to-br from-red-50 to-orange-50 border border-red-200"
        }`}
      >
        {/* Icon */}
        <div
          className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 ${
            passed ? "bg-green-100" : "bg-red-100"
          }`}
        >
          <span className="text-3xl">{passed ? "✅" : "⚠️"}</span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          {passed ? "Project Ready" : "Needs Improvement"}
        </h2>
        <p className="text-gray-600 mb-2">
          <strong>{projectName}</strong>
        </p>
        <p className="text-gray-500 text-sm mb-6">
          {passed
            ? "Your project has been analyzed, designed, validated, and converted into an AI-agent-ready engineering context."
            : "The generated context did not pass the quality gate. Review the report below."}
        </p>

        {/* Score summary */}
        {quality && (
          <div className="flex items-center justify-center gap-8 mb-6">
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">Overall</p>
              <p className={`text-3xl font-bold ${passed ? "text-green-600" : "text-red-600"}`}>
                {quality.overall_score}
              </p>
            </div>
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">Validation</p>
              <p className="text-xl font-bold text-gray-700">{quality.validation_score}</p>
            </div>
            <div className="text-center">
              <p className="text-gray-500 text-xs mb-1">Readiness</p>
              <p className="text-xl font-bold text-gray-700">{quality.readiness_score}</p>
            </div>
          </div>
        )}

        {/* Download buttons (only if passed) */}
        {passed && (
          <div className="space-y-3">
            <a
              href={downloadMarkdown}
              className="block w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download Markdown
            </a>
            <a
              href={downloadTxt}
              className="block w-full bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              Download TXT
            </a>
          </div>
        )}

        {!passed && (
          <p className="text-red-600 text-sm font-medium">
            Fix the issues below, then try generating again.
          </p>
        )}
      </div>

      {/* Detailed quality report */}
      {quality && <QualityReport quality={quality} />}

      {/* Info footer */}
      {passed && (
        <p className="text-center text-gray-400 text-xs">
          Give this context to Cursor, Claude Code, Codex, Gemini CLI, or any
          AI coding agent to build your project.
        </p>
      )}
    </div>
  );
}
