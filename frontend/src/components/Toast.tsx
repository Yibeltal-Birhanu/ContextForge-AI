"use client";

import { useEffect, useState } from "react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}

let toastListeners: Array<(toast: ToastMessage) => void> = [];

export function showToast(
  type: "success" | "error" | "info",
  message: string
) {
  const toast: ToastMessage = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    type,
    message,
  };
  toastListeners.forEach((l) => l(toast));
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const listener = (toast: ToastMessage) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 3500);
    };
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast-enter px-4 py-3 rounded-lg shadow-lg text-sm font-medium max-w-sm ${
            toast.type === "success"
              ? "bg-gray-900 text-white"
              : toast.type === "error"
              ? "bg-red-600 text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          {toast.type === "success" && (
            <span className="mr-2 text-green-400">✓</span>
          )}
          {toast.type === "error" && (
            <span className="mr-2">⚠</span>
          )}
          {toast.message}
        </div>
      ))}
    </div>
  );
}
