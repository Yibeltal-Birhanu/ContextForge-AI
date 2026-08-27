"use client";

import { useState } from "react";

interface ProjectInputProps {
  onSubmit: (idea: string) => void;
  loading: boolean;
}

export default function ProjectInput({
  onSubmit,
  loading,
}: ProjectInputProps) {
  const [idea, setIdea] = useState("");

  const handleSubmit = () => {
    if (idea.trim()) {
      onSubmit(idea.trim());
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        What do you want to build?
      </h2>
      <p className="text-gray-600 mb-6">
        Describe your project idea and I&apos;ll help you create an
        AI-ready engineering context.
      </p>

      <textarea
        value={idea}
        onChange={(e) => setIdea(e.target.value)}
        placeholder="I want to build an online supermarket where customers can browse products, add them to a cart, pay online, and track their orders..."
        className="w-full h-40 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        disabled={loading}
      />

      <button
        onClick={handleSubmit}
        disabled={!idea.trim() || loading}
        className="mt-4 w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Starting Discovery..." : "Start Discovery"}
      </button>
    </div>
  );
}
