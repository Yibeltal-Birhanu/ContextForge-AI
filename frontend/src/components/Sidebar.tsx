"use client";

import { useState, useEffect } from "react";
import type { ProjectSummary } from "@/lib/api";
import { listProjects, deleteProject } from "@/lib/api";
import { showToast } from "./Toast";

interface SidebarProps {
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onCreateNew: () => void;
  onBackToDashboard: () => void;
  isOpen: boolean;
  onClose: () => void;
  refreshKey?: number;
}

function getStatusDot(status: string): string {
  switch (status) {
    case "complete":
      return "bg-green-400";
    case "discovery":
      return "bg-blue-400";
    case "improvement":
      return "bg-amber-400";
    default:
      return "bg-gray-400";
  }
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default function Sidebar({
  activeProjectId,
  onSelectProject,
  onCreateNew,
  onBackToDashboard,
  isOpen,
  onClose,
  refreshKey = 0,
}: SidebarProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredProject, setHoveredProject] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [refreshKey]);

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this project?")) return;
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
      showToast("success", "Project deleted");
      if (activeProjectId === projectId) {
        onBackToDashboard();
      }
    } catch {
      showToast("error", "Failed to delete project");
    }
  };

  const handleNewProject = () => {
    onCreateNew();
    onClose();
  };

  const handleSelectProject = (projectId: string) => {
    onSelectProject(projectId);
    onClose();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-[280px] bg-[#0f172a] text-white z-50
          flex flex-col transition-transform duration-200 ease-out
          lg:relative lg:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Branding */}
        <div className="px-5 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CF</span>
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight leading-tight">
                ContextForge
              </div>
              <div className="text-[11px] text-gray-400 leading-tight">
                AI Engineering Workspace
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-gray-400 hover:text-white p-1"
            aria-label="Close sidebar"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Project Button */}
        <div className="px-3 mb-3">
          <button
            onClick={handleNewProject}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-300 hover:bg-white/10 hover:text-white transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Project
          </button>
        </div>

        {/* Divider */}
        <div className="px-5 mb-2">
          <div className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">
            Projects
          </div>
        </div>

        {/* Project list */}
        <div className="flex-1 overflow-y-auto sidebar-scroll px-3">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="w-5 h-5 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {!loading && projects.length === 0 && (
            <div className="text-center py-8 px-4">
              <p className="text-gray-500 text-sm">No projects yet</p>
              <p className="text-gray-600 text-xs mt-1">
                Create your first project to get started.
              </p>
            </div>
          )}

          {!loading &&
            projects.map((project) => {
              const isActive = project.id === activeProjectId;
              const isHovered = project.id === hoveredProject;

              return (
                <div
                  key={project.id}
                  onClick={() => handleSelectProject(project.id)}
                  onMouseEnter={() => setHoveredProject(project.id)}
                  onMouseLeave={() => setHoveredProject(null)}
                  className={`
                    group flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer
                    transition-colors mb-0.5
                    ${
                      isActive
                        ? "bg-white/15 text-white"
                        : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                    }
                  `}
                >
                  <div
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDot(
                      project.status
                    )}`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      {project.name || "Untitled"}
                    </div>
                    <div className="text-[11px] text-gray-500 truncate">
                      {formatDate(project.updated_at)}
                    </div>
                  </div>

                  {/* Delete button */}
                  {isHovered && (
                    <button
                      onClick={(e) => handleDelete(e, project.id)}
                      className="flex-shrink-0 p-1 rounded text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                      aria-label="Delete project"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              );
            })}
        </div>

        {/* Bottom section */}
        <div className="px-3 py-3 border-t border-white/10">
          <button
            onClick={() => {
              showToast("info", "ContextForge AI — v0.1.0");
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-white/5 hover:text-gray-200 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            About ContextForge
          </button>
        </div>
      </aside>
    </>
  );
}
