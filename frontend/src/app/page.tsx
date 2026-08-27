"use client";

import { useState } from "react";
import type { PipelineResult } from "@/types/project";
import { startProject, continueProject, getDownloadUrl } from "@/lib/api";
import ProjectInput from "@/components/ProjectInput";
import ProgressSteps from "@/components/ProgressSteps";
import DiscoveryPanel from "@/components/DiscoveryPanel";
import CompletionCard from "@/components/CompletionCard";

export default function Home() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async (idea: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await startProject(idea);
      setResult(res);
      setCurrentQuestionIndex(0);
      setAnswers({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (field: string, answer: string) => {
    if (!result) return;

    const updatedAnswers = { ...answers, [field]: answer };
    setAnswers(updatedAnswers);
    setLoading(true);
    setError(null);

    try {
      const nextResult = await continueProject(
        result.project,
        updatedAnswers
      );
      setResult(nextResult);
      setAnswers({});
      setCurrentQuestionIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const currentQuestion = result?.questions?.[currentQuestionIndex] || null;
  const totalQuestions = result?.questions?.length || 0;

  return (
    <main className="min-h-screen py-12 px-4">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          ContextForge AI
        </h1>
        <p className="text-gray-600">
          Turn your project idea into an AI-ready engineering context
        </p>
      </div>

      {/* Progress Steps */}
      {result && <ProgressSteps stage={result.stage} />}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-700 font-medium">⚠ Something went wrong</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setError(null);
                  if (!result) return;
                  if (result.complete) return;
                  // Retry: keep current state, just dismiss error
                }}
                className="text-red-600 hover:text-red-800 text-sm underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-3 text-gray-600 font-medium">
            {result?.stage === "discovery"
              ? "Analyzing your answer..."
              : "Generating your project context..."}
          </p>
          <p className="text-gray-400 text-sm mt-1">
            ContextForge is updating the project model
          </p>
        </div>
      )}

      {/* Content */}
      <div className="max-w-4xl mx-auto">
        {!result && !loading && (
          <ProjectInput onSubmit={handleStart} loading={loading} />
        )}

        {result && !result.complete && !loading && currentQuestion && (
          <DiscoveryPanel
            question={currentQuestion}
            questionNumber={currentQuestionIndex + 1}
            totalQuestions={totalQuestions}
            onAnswer={handleAnswer}
          />
        )}

        {result && result.complete && (
          <CompletionCard
            projectName={result.project.name || "Your Project"}
            downloadMarkdown={getDownloadUrl(result.download_markdown || "")}
            downloadTxt={getDownloadUrl(result.download_txt || "")}
          />
        )}
      </div>
    </main>
  );
}
