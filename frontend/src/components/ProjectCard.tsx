"use client";

import type { ProjectSummary } from "@/lib/api";

interface ProjectCardProps {
  project: ProjectSummary;
  onOpen: (projectId: string) => void;
  onDelete: (projectId: string) => void;
}

function getStatusColor(status: string): string {
  switch (status) {
    case "complete":
      return "bg-green-100 text-green-700";
    case "discovery":
      return "bg-blue-100 text-blue-700";
    case "improvement":
      return "bg-amber-100 text-amber-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "complete":
      return "Complete";
    case "discovery":
      return "In Discovery";
    case "improvement":
      return "Improving";
    default:
      return status;
  }
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function ProjectCard({
  project,
  onOpen,
  onDelete,
}: ProjectCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-800 truncate">
            {project.name || "Untitled Project"}
          </h3>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">
            {project.idea}
          </p>
        </div>
        <span
          className={`ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
            project.status
          )}`}
        >
          {getStatusLabel(project.status)}
        </span>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-400 mb-4">
        <span>Created {formatDate(project.created_at)}</span>
        <span>Updated {formatDate(project.updated_at)}</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onOpen(project.id)}
          className={`flex-1 py-2 px-4 rounded-lg font-medium text-sm transition-colors ${
            project.status === "complete"
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-gray-800 text-white hover:bg-gray-900"
          }`}
        >
          {project.status === "complete" ? "Open" : "Continue"}
        </button>
        <button
          onClick={() => {
            if (confirm("Delete this project? This cannot be undone.")) {
              onDelete(project.id);
            }
          }}
          className="py-2 px-3 rounded-lg text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
