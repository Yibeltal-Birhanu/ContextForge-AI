"use client";

import { useState, useEffect } from "react";
import type { ProjectSummary } from "@/lib/api";
import { listProjects, deleteProject } from "@/lib/api";
import ProjectCard from "./ProjectCard";

interface DashboardProps {
  onOpenProject: (projectId: string) => void;
  onCreateNew: () => void;
}

export default function Dashboard({
  onOpenProject,
  onCreateNew,
}: DashboardProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">My Projects</h2>
          <p className="text-gray-500 text-sm mt-1">
            {projects.length} project{projects.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={onCreateNew}
          className="bg-blue-600 text-white py-2.5 px-5 rounded-lg font-semibold hover:bg-blue-700 transition-colors text-sm"
        >
          + Create New Project
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-500 text-xs mt-1 underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-500 mt-3">Loading projects...</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && projects.length === 0 && (
        <div className="text-center py-16 bg-gray-50 rounded-2xl border border-gray-200">
          <div className="text-4xl mb-4"> </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            No projects yet
          </h3>
          <p className="text-gray-500 text-sm mb-6">
            Create your first project to get started with ContextForge AI.
          </p>
          <button
            onClick={onCreateNew}
            className="bg-blue-600 text-white py-2.5 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Create Your First Project
          </button>
        </div>
      )}

      {/* Project grid */}
      {!loading && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onOpen={onOpenProject}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
