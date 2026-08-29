"use client";

interface LoadingIndicatorProps {
  message?: string;
}

export default function LoadingIndicator({
  message = "Thinking",
}: LoadingIndicatorProps) {
  return (
    <div className="flex gap-3 message-enter">
      <div className="flex-shrink-0 w-7 h-7 bg-blue-50 rounded-lg flex items-center justify-center mt-0.5">
        <span className="text-blue-600 font-bold text-[11px]">CF</span>
      </div>
      <div className="flex-1">
        <div className="text-[11px] font-medium text-gray-400 mb-1">
          ContextForge
        </div>
        <div className="flex items-center gap-1.5 py-2">
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 pulse-dot-1" />
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 pulse-dot-2" />
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 pulse-dot-3" />
          <span className="text-xs text-gray-400 ml-1">{message}</span>
        </div>
      </div>
    </div>
  );
}
