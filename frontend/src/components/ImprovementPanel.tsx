"use client";

import type { QualityInfo } from "@/types/project";

interface ImprovementPanelProps {
  quality: QualityInfo;
  onImprove: () => void;
  loading: boolean;
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

function getScoreBg(score: number): string {
  if (score >= 90) return "bg-green-500";
  if (score >= 75) return "bg-yellow-500";
  return "bg-red-500";
}

function getStatusIcon(score: number): string {
  if (score >= 85) return "✓";
  return "✕";
}

export default function ImprovementPanel({
  quality,
  onImprove,
  loading,
}: ImprovementPanelProps) {
  const checks = quality.checks;
  const weakAreas = Object.entries(checks).filter(
    ([, score]) => (score as number) < 85
  );

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-200 px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-800">
                Context Needs Improvement
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Quality gate identified weak areas that need attention
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-amber-600">
                {quality.overall_score}
              </div>
              <div className="text-xs text-gray-400">/ 100</div>
            </div>
          </div>
        </div>

        {/* Check scores */}
        <div className="px-6 py-4">
          <p className="text-sm font-medium text-gray-500 mb-3">
            Quality Check Results
          </p>
          <div className="space-y-2">
            {Object.entries(checks).map(([key, score]) => {
              const s = score as number;
              const status = getStatusIcon(s);
              return (
                <div
                  key={key}
                  className="flex items-center justify-between py-1.5"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                        s >= 85
                          ? "bg-green-100 text-green-600"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {status}
                    </span>
                    <span className="text-sm text-gray-700">
                      {CHECK_LABELS[key] || key}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${getScoreBg(s)}`}
                        style={{ width: `${s}%` }}
                      />
                    </div>
                    <span
                      className={`text-sm font-medium w-10 text-right ${getScoreColor(s)}`}
                    >
                      {s}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Weak areas summary */}
        {weakAreas.length > 0 && (
          <div className="px-6 py-3 border-t border-gray-100 bg-red-50">
            <p className="text-sm font-medium text-red-700 mb-2">
              Areas that need improvement:
            </p>
            <div className="space-y-1">
              {weakAreas.map(([key, score]) => (
                <p key={key} className="text-xs text-red-600">
                  - {CHECK_LABELS[key] || key}: {score as number}% (target: 85%+)
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Rejection reasons */}
        {quality.rejection_reasons.length > 0 && (
          <div className="px-6 py-3 border-t border-gray-100 bg-orange-50">
            <p className="text-sm font-medium text-orange-700 mb-2">
              Quality gate failures:
            </p>
            <div className="space-y-1">
              {quality.rejection_reasons.map((reason, i) => (
                <p key={i} className="text-xs text-orange-600">
                  - {reason}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Improve button */}
        <div className="px-6 py-5 border-t border-gray-100">
          <button
            onClick={onImprove}
            disabled={loading}
            className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
              loading
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                Improving context with AI...
              </span>
            ) : (
              "Improve Context with AI"
            )}
          </button>
          <p className="text-xs text-gray-400 text-center mt-2">
            ContextForge will target the weak areas and regenerate an improved context
          </p>
        </div>
      </div>
    </div>
  );
}
