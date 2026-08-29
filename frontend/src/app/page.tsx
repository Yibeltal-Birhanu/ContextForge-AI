"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { PipelineResult, ConversationEntry } from "@/types/project";
import {
  startProject,
  continueProject,
  improveProject,
  getDownloadUrl,
  createProject as apiCreateProject,
  getProjectDetail,
  updateProject,
  saveProjectState,
} from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Composer from "@/components/Composer";
import ChatMessage from "@/components/ChatMessage";
import DiscoveryCard from "@/components/DiscoveryCard";
import CompletionView from "@/components/CompletionView";
import LoadingIndicator from "@/components/LoadingIndicator";
import PipelineIndicator from "@/components/PipelineIndicator";
import ToastContainer, { showToast } from "@/components/Toast";

interface ChatEntry {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}

export default function Home() {
  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Project state
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [conversationHistory, setConversationHistory] = useState<
    ConversationEntry[]
  >([]);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatEntry[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll
  const scrollToBottom = useCallback(() => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, loading, scrollToBottom]);

  const handleScroll = () => {
    const container = chatContainerRef.current;
    if (!container) return;
    const isAtBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 60;
    setAutoScroll(isAtBottom);
  };

  // Add message to chat
  const addMessage = useCallback(
    (role: "user" | "assistant" | "system", content: string) => {
      const msg: ChatEntry = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        role,
        content,
      };
      setChatMessages((prev) => [...prev, msg]);
    },
    []
  );

  // ============================================================
  // Sidebar handlers
  // ============================================================

  const handleCreateNew = useCallback(() => {
    setResult(null);
    setActiveProjectId(null);
    setAnswers({});
    setConversationHistory([]);
    setChatMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Welcome to ContextForge AI.\n\nDescribe your project idea and I'll help you create an AI-ready engineering context.",
      },
    ]);
    setInputValue("");
    setError(null);
    setSidebarOpen(false);
  }, []);

  const handleSelectProject = useCallback(async (projectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getProjectDetail(projectId);
      setActiveProjectId(projectId);

      const projectData = detail.project.project_data as Record<
        string,
        unknown
      > | null;

      if (detail.project.status === "complete" && projectData) {
        // Completed project — show results
        const latestArtifact = detail.latest_artifact;
        const pr: PipelineResult = {
          stage: "complete",
          complete: true,
          project: projectData as unknown as PipelineResult["project"],
          missing_fields: [],
          questions: [],
          conversation_history: [],
          project_id: latestArtifact?.id || projectId,
          download_markdown: latestArtifact
            ? `/export/${latestArtifact.id}/markdown`
            : null,
          download_txt: latestArtifact
            ? `/export/${latestArtifact.id}/txt`
            : null,
          quality:
            (detail.context?.quality_result as PipelineResult["quality"]) ||
            null,
        };
        setResult(pr);
        setChatMessages([
          {
            id: "loaded",
            role: "assistant",
            content: `Project **${detail.project.name || "Untitled"}** loaded.\n\nThis project is complete with a quality score of ${
              pr.quality?.overall_score || "N/A"
            }/100.`,
          },
        ]);
      } else if (projectData && Object.keys(projectData).length > 0) {
        // Discovery project with saved state — restore and continue
        const savedHistory = (projectData as Record<string, unknown>)._conversation_history as
          ConversationEntry[] | undefined;
        const restoredHistory = Array.isArray(savedHistory) ? savedHistory : [];
        setConversationHistory(restoredHistory);
        setAnswers({});

        // Build chat messages from conversation history
        const restoredMessages: ChatEntry[] = [];
        for (const entry of restoredHistory) {
          restoredMessages.push({
            id: `hist-q-${entry.field}`,
            role: "assistant",
            content: entry.question,
          });
          restoredMessages.push({
            id: `hist-a-${entry.field}`,
            role: "user",
            content: entry.answer,
          });
        }
        restoredMessages.push({
          id: "resumed",
          role: "assistant",
          content: `Project **${detail.project.name || "Untitled"}** resumed.\n\nLet me continue where we left off.`,
        });
        setChatMessages(restoredMessages);

        // Reconstruct pipeline result for discovery continuation
        // The project has partial data — we need to re-run discovery
        // to get the next questions
        const pr: PipelineResult = {
          stage: (detail.project.current_stage as PipelineResult["stage"]) || "discovery",
          complete: false,
          project: projectData as unknown as PipelineResult["project"],
          missing_fields: [],
          questions: [],
          conversation_history: restoredHistory,
          project_id: null,
          download_markdown: null,
          download_txt: null,
          quality: null,
        };
        setResult(pr);
      } else {
        // Fresh project or no saved data — show input
        setResult(null);
        setChatMessages([
          {
            id: "fresh",
            role: "assistant",
            content: `Project **${detail.project.name || "Untitled"}** loaded.\n\nDescribe what you want to build to continue.`,
          },
        ]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load project."
      );
    } finally {
      setLoading(false);
      setSidebarOpen(false);
    }
  }, []);

  const handleBackToDashboard = useCallback(() => {
    setSidebarOpen(true);
    setResult(null);
    setActiveProjectId(null);
    setAnswers({});
    setConversationHistory([]);
    setChatMessages([]);
    setInputValue("");
    setError(null);
  }, []);

  // ============================================================
  // Pipeline handlers
  // ============================================================

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const message = inputValue.trim();
    setInputValue("");

    if (!result) {
      // Starting a new project
      addMessage("user", message);
      setLoading(true);
      setError(null);

      try {
        // Create persistent project
        const project = await apiCreateProject(
          message.slice(0, 60) || "Untitled Project",
          message
        );
        setActiveProjectId(project.id);

        // Run pipeline
        const res = await startProject(message, project.id);
        setResult(res);
        setAnswers({});
        setConversationHistory([]);

        // Update project name if AI provided one
        if (res.project?.name) {
          await updateProject(project.id, { name: res.project.name }).catch(() => {});
        }

        // Save initial state for resumption
        const initialState: Record<string, unknown> = {
          ...((res.project as unknown as Record<string, unknown>) || {}),
          _conversation_history: [],
          _answers: {},
        };
        await saveProjectState(project.id, initialState, {
          status: "discovery",
          current_stage: res.stage,
          name: res.project?.name || undefined,
        }).catch(() => {});
        setRefreshKey((k) => k + 1);

        // Add first question or completion
        if (res.complete) {
          addMessage(
            "assistant",
            `Project **${res.project.name || "Your Project"}** is complete!`
          );
        } else if (res.questions.length > 0) {
          // Don't add a text message - the question card will show
        } else {
          addMessage(
            "assistant",
            "I understand the basic idea. Let me gather a few more details..."
          );
        }
      } catch (err) {
        const errMsg =
          err instanceof Error ? err.message : "Something went wrong.";
        setError(errMsg);
        addMessage(
          "assistant",
          `I encountered an issue: ${errMsg}\n\nPlease try again.`
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    // Resuming a discovery project with no loaded questions —
    // the first message is the user describing what they want,
    // we need to run continueProject to get the next questions
    if (result && !result.complete && result.questions.length === 0) {
      addMessage("user", message);
      setLoading(true);
      setError(null);

      try {
        const nextResult = await continueProject(
          result.project,
          { idea: message },
          conversationHistory,
          activeProjectId
        );

        setResult(nextResult);
        setConversationHistory(
          nextResult.conversation_history || conversationHistory
        );

        // Save state
        if (activeProjectId) {
          const stateToSave: Record<string, unknown> = {
            ...((nextResult.project as unknown as Record<string, unknown>) || {}),
            _conversation_history: nextResult.conversation_history || conversationHistory,
            _answers: {},
          };
          await saveProjectState(activeProjectId, stateToSave, {
            status: "discovery",
            current_stage: nextResult.stage,
            name: nextResult.project?.name || undefined,
          }).catch(() => {});
          setRefreshKey((k) => k + 1);
        }
      } catch (err) {
        const errMsg =
          err instanceof Error ? err.message : "Something went wrong.";
        setError(errMsg);
        addMessage(
          "assistant",
          `I encountered an issue: ${errMsg}\n\nPlease try again.`
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    // Answering a question
    if (!result || result.complete || result.questions.length === 0) return;

    const currentQ = result.questions.find(
      (q) => q.field === Object.keys(answers)[0] || true
    );
    const questionText =
      currentQ?.question || "Answer";

    // Find which question the user is answering
    const activeQuestion = result.questions[0]; // first unanswered

    if (!activeQuestion) return;

    addMessage("user", message);

    const newHistory: ConversationEntry[] = [
      ...conversationHistory,
      {
        field: activeQuestion.field,
        question: questionText,
        answer: message,
      },
    ];
    setConversationHistory(newHistory);

    const updatedAnswers = {
      ...answers,
      [activeQuestion.field]: message,
    };
    setAnswers(updatedAnswers);
    setLoading(true);
    setError(null);

    try {
      const nextResult = await continueProject(
        result.project,
        updatedAnswers,
        newHistory,
        activeProjectId
      );

      setResult(nextResult);
      setAnswers({});
      setConversationHistory(
        nextResult.conversation_history || newHistory
      );

      // Save project state for resumption
      if (activeProjectId) {
        const stateToSave: Record<string, unknown> = {
          ...((nextResult.project as unknown as Record<string, unknown>) || {}),
          _conversation_history: nextResult.conversation_history || newHistory,
          _answers: {},
        };
        await saveProjectState(activeProjectId, stateToSave, {
          status: nextResult.complete ? "complete" : "discovery",
          current_stage: nextResult.stage,
          name: nextResult.project?.name || undefined,
        }).catch(() => {}); // non-critical
        setRefreshKey((k) => k + 1);
      }

      // Update project name
      if (activeProjectId && nextResult.project?.name) {
        await updateProject(activeProjectId, {
          name: nextResult.project.name,
        }).catch(() => {});
      }

      if (nextResult.complete) {
        addMessage(
          "assistant",
          `Project **${nextResult.project?.name || "Your Project"}** is complete!`
        );
      }
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "Something went wrong.";
      setError(errMsg);
      addMessage(
        "assistant",
        `I encountered an issue: ${errMsg}\n\nPlease try again or re-enter your answer.`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDiscoveryAnswer = async (field: string, answer: string) => {
    if (!result || loading) return;

    const currentQ = result.questions.find((q) => q.field === field);
    const questionText = currentQ?.question || field;

    addMessage("user", answer);

    const newHistory: ConversationEntry[] = [
      ...conversationHistory,
      { field, question: questionText, answer },
    ];
    setConversationHistory(newHistory);

    const updatedAnswers = { ...answers, [field]: answer };
    setAnswers(updatedAnswers);
    setLoading(true);
    setError(null);

    try {
      const nextResult = await continueProject(
        result.project,
        updatedAnswers,
        newHistory,
        activeProjectId
      );

      setResult(nextResult);
      setAnswers({});
      setConversationHistory(
        nextResult.conversation_history || newHistory
      );

      // Save project state for resumption
      if (activeProjectId) {
        const stateToSave: Record<string, unknown> = {
          ...((nextResult.project as unknown as Record<string, unknown>) || {}),
          _conversation_history: nextResult.conversation_history || newHistory,
          _answers: {},
        };
        await saveProjectState(activeProjectId, stateToSave, {
          status: nextResult.complete ? "complete" : "discovery",
          current_stage: nextResult.stage,
          name: nextResult.project?.name || undefined,
        }).catch(() => {});
        setRefreshKey((k) => k + 1);
      }

      if (activeProjectId && nextResult.project?.name) {
        await updateProject(activeProjectId, {
          name: nextResult.project.name,
        }).catch(() => {});
      }

      if (nextResult.complete) {
        addMessage(
          "assistant",
          `Project **${nextResult.project?.name || "Your Project"}** is complete!`
        );
      }
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "Something went wrong.";
      setError(errMsg);
      addMessage(
        "assistant",
        `I encountered an issue: ${errMsg}\n\nPlease try again.`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async () => {
    if (!result || !result.quality) return;

    const prevScore = result.quality.overall_score;
    setLoading(true);
    addMessage("assistant", "Improving the context with AI...");
    setError(null);

    try {
      const improvedResult = await improveProject(
        result.project,
        {},
        { checks: result.quality.checks },
        activeProjectId
      );
      setResult(improvedResult);

      if (improvedResult.complete) {
        const newScore = improvedResult.quality?.overall_score || 0;
        addMessage(
          "assistant",
          `Context improved! Quality score: ${prevScore}/100 → ${newScore}/100.`
        );
      } else if (improvedResult.quality) {
        const newScore = improvedResult.quality.overall_score;
        if (newScore > prevScore) {
          addMessage(
            "assistant",
            `Context improved. Quality score: ${prevScore}/100 → ${newScore}/100. Still needs work — review the weak areas below.`
          );
        } else {
          addMessage(
            "assistant",
            `Improvement completed but the quality score remains at ${newScore}/100. The weak areas need different changes.`
          );
        }
      }

      // Persist the improvement
      if (activeProjectId) {
        const stateToSave: Record<string, unknown> = {
          ...((improvedResult.project as unknown as Record<string, unknown>) || {}),
          _conversation_history: conversationHistory,
          _answers: {},
        };
        await saveProjectState(activeProjectId, stateToSave, {
          status: improvedResult.complete ? "complete" : "improvement",
          current_stage: improvedResult.stage,
          name: improvedResult.project?.name || undefined,
        }).catch(() => {});
        setRefreshKey((k) => k + 1);
      }
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : "Improvement failed.";
      setError(errMsg);
      addMessage(
        "assistant",
        `Improvement failed: ${errMsg}`
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // Render
  // ============================================================

  const hasActiveProject = result !== null;
  const isDiscovery = !!(result && !result.complete && result.questions.length > 0);
  const isComplete = !!(result && result.complete);
  const showImprovement =
    !!(
      result &&
      !result.complete &&
      result.quality &&
      result.stage !== "discovery"
    );

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        activeProjectId={activeProjectId}
        onSelectProject={handleSelectProject}
        onCreateNew={handleCreateNew}
        onBackToDashboard={handleBackToDashboard}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        refreshKey={refreshKey}
      />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white flex-shrink-0">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-1.5 rounded-lg text-gray-500 hover:bg-gray-100"
            aria-label="Open sidebar"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Project name or brand */}
          <div className="flex-1 min-w-0">
            {result?.project?.name ? (
              <h1 className="text-sm font-semibold text-gray-900 truncate">
                {result.project.name}
              </h1>
            ) : (
              <h1 className="text-sm font-semibold text-gray-900">
                ContextForge AI
              </h1>
            )}
          </div>

          {/* Pipeline indicator */}
          {result && (
            <div className="hidden sm:block">
              <PipelineIndicator stage={result.stage} />
            </div>
          )}

          {/* Score badge */}
          {isComplete && result.quality && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-50 border border-green-200 rounded-full">
              <svg className="w-3.5 h-3.5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-xs font-bold text-green-700">
                {result.quality.overall_score}
              </span>
            </div>
          )}
        </header>

        {/* Chat area or empty state */}
        {!hasActiveProject && chatMessages.length === 0 ? (
          // Empty state
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center max-w-lg">
              <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
                <span className="text-blue-600 font-bold text-xl">CF</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Build something great
              </h2>
              <p className="text-gray-500 mb-8 leading-relaxed">
                Tell ContextForge what you want to build and it will create an
                AI-ready engineering context for your team.
              </p>
              <div className="relative max-w-md mx-auto">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Describe your project idea..."
                  rows={3}
                  disabled={loading}
                  className="w-full p-4 pr-12 bg-white border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 shadow-sm"
                />
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || loading}
                  className="absolute right-3 bottom-3 w-8 h-8 rounded-lg bg-gray-900 text-white flex items-center justify-center hover:bg-gray-700 disabled:bg-gray-200 disabled:cursor-not-allowed transition-colors"
                  aria-label="Send"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="text-[11px] text-gray-400 mt-3">
                Press Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        ) : (
          // Chat view
          <>
            <div
              ref={chatContainerRef}
              onScroll={handleScroll}
              className="flex-1 overflow-y-auto"
            >
              <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
                {/* Chat messages */}
                {chatMessages.map((msg) => (
                  <ChatMessage
                    key={msg.id}
                    role={msg.role}
                    content={msg.content}
                    showActions={msg.role === "assistant"}
                  />
                ))}

                {/* Error */}
                {error && !loading && (
                  <div className="flex justify-center">
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                      <span>⚠</span>
                      <span>{error}</span>
                      <button
                        onClick={() => {
                          setError(null);
                          handleSend();
                        }}
                        className="text-red-600 underline ml-1 hover:text-red-800"
                      >
                        Retry
                      </button>
                    </div>
                  </div>
                )}

                {/* Discovery question card */}
                {isDiscovery && !loading && (
                  <DiscoveryCard
                    question={result.questions[0]}
                    questionNumber={1}
                    totalQuestions={result.questions.length}
                    onAnswer={handleDiscoveryAnswer}
                    loading={loading}
                  />
                )}

                {/* Loading indicator */}
                {loading && !isDiscovery && (
                  <LoadingIndicator
                    message={
                      result?.quality && !result?.complete
                        ? "Improving context"
                        : result?.stage === "discovery"
                        ? "Analyzing your answer"
                        : "Generating project context"
                    }
                  />
                )}

                {/* Completion view */}
                {isComplete && (
                  <CompletionView
                    projectName={
                      result.project?.name || "Your Project"
                    }
                    downloadMarkdown={getDownloadUrl(
                      result.download_markdown || ""
                    )}
                    downloadTxt={getDownloadUrl(
                      result.download_txt || ""
                    )}
                    quality={result.quality}
                  />
                )}

                {/* Improvement panel */}
                {showImprovement && !loading && (
                  <div className="flex gap-3 message-enter">
                    <div className="flex-shrink-0 w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center mt-0.5">
                      <span className="text-blue-600 font-bold text-[11px]">
                        CF
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="text-[11px] font-medium text-gray-400 mb-1">
                        ContextForge
                      </div>
                      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 max-w-lg">
                        <p className="text-sm text-gray-800 mb-3">
                          Quality score: {result.quality!.overall_score}/100
                          — not ready yet because:
                        </p>
                        {result.quality!.rejection_reasons.length > 0 && (
                          <ul className="mb-3 space-y-1 text-xs text-gray-600">
                            {result.quality!.rejection_reasons.map((reason, index) => (
                              <li key={index}>- {reason}</li>
                            ))}
                          </ul>
                        )}
                        <button
                          onClick={handleImprove}
                          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Improve with AI
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Composer - only show during discovery or before completion */}
            {(!isComplete || chatMessages.length > 0) && (
              <Composer
                value={inputValue}
                onChange={setInputValue}
                onSend={handleSend}
                loading={loading}
                disabled={isDiscovery}
                placeholder={
                  isDiscovery
                    ? "Answer the question above..."
                    : isComplete
                    ? "Start a new project..."
                    : "Tell ContextForge what you want to build..."
                }
              />
            )}
          </>
        )}
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}
