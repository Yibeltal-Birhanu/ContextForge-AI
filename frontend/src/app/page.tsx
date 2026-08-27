"use client";

import { useState, useCallback } from "react";
import type { PipelineResult } from "@/types/project";
import {
  startProject,
  continueProject,
  improveProject,
  getDownloadUrl,
  createProject as apiCreateProject,
  getProjectDetail,
} from "@/lib/api";
import ProjectInput from "@/components/ProjectInput";
import ProgressSteps from "@/components/ProgressSteps";
import DiscoveryPanel from "@/components/DiscoveryPanel";
import CompletionCard from "@/components/CompletionCard";
import ImprovementPanel from "@/components/ImprovementPanel";
import Dashboard from "@/components/Dashboard";

type View = "dashboard" | "workspace";

export default function Home() {
  const [view, setView] = useState<View>("dashboard");
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  // ============================================================
  // Dashboard handlers
  // ============================================================

  const handleCreateNew = useCallback(() => {
    setView("workspace");
    setResult(null);
    setActiveProjectId(null);
    setAnswers({});
    setCurrentQuestionIndex(0);
    setError(null);
  }, []);

  const handleOpenProject = useCallback(async (projectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getProjectDetail(projectId);
      setActiveProjectId(projectId);
      setView("workspace");

      // If project has project_data, reconstruct the pipeline result
      if (detail.project.project_data) {
        const projectData = detail.project.project_data as Record<string, unknown>;
        // If complete, show completion
        if (detail.project.status === "complete") {
          const latestArtifact = detail.latest_artifact;
          setResult({
            stage: "complete",
            complete: true,
            project: projectData as unknown as PipelineResult["project"],
            missing_fields: [],
            questions: [],
            project_id: latestArtifact?.id || projectId,
            download_markdown: latestArtifact
              ? `/export/${latestArtifact.id}/markdown`
              : null,
            download_txt: latestArtifact
              ? `/export/${latestArtifact.id}/txt`
              : null,
            quality: (detail.context?.quality_result as PipelineResult["quality"]) || null,
          });
        } else {
          // Project in progress - need to re-run discovery to get questions
          // For now, just show the project data
          setResult({
            stage: detail.project.current_stage as PipelineResult["stage"],
            complete: false,
            project: projectData as unknown as PipelineResult["project"],
            missing_fields: [],
            questions: [],
            project_id: null,
            download_markdown: null,
            download_txt: null,
            quality: null,
          });
        }
      } else {
        // Fresh project, show input
        setResult(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project.");
    } finally {
      setLoading(false);
    }
  }, []);

  // ============================================================
  // Pipeline handlers
  // ============================================================

  const handleStart = async (idea: string) => {
    setLoading(true);
    setError(null);
    try {
      // Create persistent project
      const project = await apiCreateProject(
        idea.slice(0, 60) || "Untitled Project",
        idea
      );
      setActiveProjectId(project.id);

      // Run pipeline
      const res = await startProject(idea);
      setResult(res);
      setCurrentQuestionIndex(0);
      setAnswers({});

      // Update project name if AI provided one
      if (res.project?.name) {
        const { updateProject } = await import("@/lib/api");
        await updateProject(project.id, { name: res.project.name });
      }
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

      // Update project name if AI provided one
      if (activeProjectId && nextResult.project?.name) {
        const { updateProject } = await import("@/lib/api");
        await updateProject(activeProjectId, { name: nextResult.project.name });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async () => {
    if (!result || !result.quality) return;

    setLoading(true);
    setError(null);

    try {
      const improvedResult = await improveProject(
        result.project,
        {},
        { checks: result.quality.checks }
      );
      setResult(improvedResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Improvement failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleBackToDashboard = () => {
    setView("dashboard");
    setResult(null);
    setActiveProjectId(null);
    setAnswers({});
    setCurrentQuestionIndex(0);
    setError(null);
  };

  const currentQuestion = result?.questions?.[currentQuestionIndex] || null;
  const totalQuestions = result?.questions?.length || 0;

  // Determine if quality gate failed
  const showImprovement =
    result &&
    !result.complete &&
    result.quality &&
    result.stage !== "discovery";

  return (
    <main className="min-h-screen py-12 px-4">
      {/* Header */}
      <div className="text-center mb-8">
        <h1
          className="text-4xl font-bold text-gray-800 mb-2 cursor-pointer hover:text-blue-600 transition-colors"
          onClick={handleBackToDashboard}
        >
          ContextForge AI
        </h1>
        <p className="text-gray-600">
          Turn your project idea into an AI-ready engineering context
        </p>
      </div>

      {/* Dashboard view */}
      {view === "dashboard" && (
        <Dashboard
          onOpenProject={handleOpenProject}
          onCreateNew={handleCreateNew}
        />
      )}

      {/* Workspace view */}
      {view === "workspace" && (
        <div className="max-w-4xl mx-auto">
          {/* Back button */}
          <button
            onClick={handleBackToDashboard}
            className="mb-6 text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <span>&larr;</span> Back to Projects
          </button>

          {/* Progress Steps */}
          {result && <ProgressSteps stage={result.stage} />}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-700 font-medium">
                    Something went wrong
                  </p>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-600 hover:text-red-800 text-sm underline"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-3 text-gray-600 font-medium">
                {result?.quality && !result?.complete
                  ? "Improving context with AI..."
                  : result?.stage === "discovery"
                  ? "Analyzing your answer..."
                  : "Generating your project context..."}
              </p>
              <p className="text-gray-400 text-sm mt-1">
                ContextForge is updating the project model
              </p>
            </div>
          )}

          {/* Content */}
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

          {/* Quality gate passed */}
          {result && result.complete && (
            <CompletionCard
              projectName={result.project.name || "Your Project"}
              downloadMarkdown={getDownloadUrl(
                result.download_markdown || ""
              )}
              downloadTxt={getDownloadUrl(result.download_txt || "")}
              quality={result.quality}
            />
          )}

          {/* Quality gate failed */}
          {showImprovement && !loading && (
            <ImprovementPanel
              quality={result.quality!}
              onImprove={handleImprove}
              loading={loading}
            />
          )}
        </div>
      )}
    </main>
  );
}
