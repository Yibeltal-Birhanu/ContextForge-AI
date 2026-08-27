"use client";

import type { QualityInfo } from "@/types/project";

interface QualityReportProps {
  quality: QualityInfo;
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

function getScoreBarColor(score: number): string {
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-yellow-500";
  return "bg-red-500";
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center gap-2">
        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${getScoreBarColor(score)}`}
            style={{ width: `${score}%` }}
          />
        </div>
        <span className={`text-sm font-medium w-10 text-right ${getScoreColor(score)}`}>
          {score}%
        </span>
      </div>
    </div>
  );
}

export default function QualityReport({ quality }: QualityReportProps) {
  const passed = quality.ready_for_agent;
  const checks = quality.checks;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div
        className={`px-6 py-4 ${
          passed
            ? "bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-200"
            : "bg-gradient-to-r from-red-50 to-orange-50 border-b border-red-200"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              Context Quality Report
            </h3>
            <p className="text-sm text-gray-500 mt-0.5">
              {passed
                ? "Ready for AI coding agent"
                : "Needs improvement before use"}
            </p>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${passed ? "text-green-600" : "text-red-600"}`}>
              {quality.overall_score}
            </div>
            <div className="text-xs text-gray-400">/ 100</div>
          </div>
        </div>
      </div>

      {/* Scores breakdown */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-2 gap-x-8 gap-y-1">
          <div className="col-span-2 flex items-center justify-between py-1.5 border-b border-gray-100 mb-1">
            <span className="text-sm font-medium text-gray-700">Validation</span>
            <span className={`text-sm font-bold ${getScoreColor(quality.validation_score)}`}>
              {quality.validation_score}%
            </span>
          </div>
          <div className="col-span-2 flex items-center justify-between py-1.5 border-b border-gray-100 mb-1">
            <span className="text-sm font-medium text-gray-700">Agent Readiness</span>
            <span className={`text-sm font-bold ${getScoreColor(quality.readiness_score)}`}>
              {quality.readiness_score}%
            </span>
          </div>
        </div>

        <div className="mt-3 space-y-0.5">
          {Object.entries(checks).map(([key, score]) => (
            <ScoreBar
              key={key}
              label={CHECK_LABELS[key] || key}
              score={score as number}
            />
          ))}
        </div>
      </div>

      {/* Warnings */}
      {quality.warnings_count > 0 && (
        <div className="px-6 py-3 border-t border-gray-100 bg-yellow-50">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-yellow-600 text-sm font-medium">
              {quality.warnings_count} Warning{quality.warnings_count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-1">
            {quality.warnings.slice(0, 3).map((w, i) => (
              <p key={i} className="text-xs text-yellow-700">
                [{w.category}] {w.message}
              </p>
            ))}
            {quality.warnings_count > 3 && (
              <p className="text-xs text-yellow-500">
                +{quality.warnings_count - 3} more warnings
              </p>
            )}
          </div>
        </div>
      )}

      {/* Assumptions */}
      {quality.assumptions_count > 0 && (
        <div className="px-6 py-3 border-t border-gray-100 bg-blue-50">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-blue-600 text-sm font-medium">
              {quality.assumptions_count} AI Assumption{quality.assumptions_count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-1">
            {quality.assumptions.slice(0, 3).map((a, i) => (
              <p key={i} className="text-xs text-blue-700">
                [{a.severity}] [{a.area}] {a.assumption}
              </p>
            ))}
            {quality.assumptions_count > 3 && (
              <p className="text-xs text-blue-500">
                +{quality.assumptions_count - 3} more assumptions
              </p>
            )}
          </div>
        </div>
      )}

      {/* Rejection reasons (if failed) */}
      {!passed && quality.rejection_reasons.length > 0 && (
        <div className="px-6 py-3 border-t border-red-200 bg-red-50">
          <p className="text-sm font-medium text-red-700 mb-2">
            Why the quality gate failed:
          </p>
          <div className="space-y-1">
            {quality.rejection_reasons.map((reason, i) => (
              <p key={i} className="text-xs text-red-600">
                - {reason}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
