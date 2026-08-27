"use client";

interface CompletionCardProps {
  projectName: string;
  downloadMarkdown: string;
  downloadTxt: string;
}

export default function CompletionCard({
  projectName,
  downloadMarkdown,
  downloadTxt,
}: CompletionCardProps) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-2xl shadow-xl p-8 text-center">
        {/* Success icon */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">✅</span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Project Ready
        </h2>
        <p className="text-gray-600 mb-2">
          <strong>{projectName}</strong>
        </p>
        <p className="text-gray-500 text-sm mb-8">
          Your project has been analyzed, designed, validated, and converted
          into an AI-agent-ready engineering context.
        </p>

        {/* Validation score */}
        <div className="bg-white rounded-xl p-6 mb-8 shadow-sm">
          <p className="text-gray-500 text-sm mb-2">Validation Score</p>
          <div className="text-4xl font-bold text-green-600">100</div>
          <p className="text-gray-400 text-sm">out of 100</p>
        </div>

        {/* Download buttons */}
        <div className="space-y-3">
          <a
            href={downloadMarkdown}
            className="block w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            📄 Download Markdown
          </a>
          <a
            href={downloadTxt}
            className="block w-full bg-gray-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-gray-700 transition-colors"
            target="_blank"
            rel="noopener noreferrer"
          >
            📝 Download TXT
          </a>
        </div>

        {/* Info */}
        <p className="text-gray-400 text-xs mt-6">
          Give this context to Cursor, Claude Code, Codex, or any AI coding
          agent to build your project.
        </p>
      </div>
    </div>
  );
}
