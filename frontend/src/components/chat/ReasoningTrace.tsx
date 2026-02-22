"use client";

import { useState, useEffect } from "react";
import { ReasoningStep } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { ChevronRight, ChevronDown, Wrench } from "lucide-react";

interface ReasoningTraceProps {
  steps: ReasoningStep[];
  isStreaming?: boolean;
}

export function ReasoningTrace({ steps, isStreaming = false }: ReasoningTraceProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Auto-expand while streaming
  useEffect(() => {
    if (isStreaming && steps.length > 0) {
      setIsOpen(true);
    }
  }, [isStreaming, steps.length]);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        {isOpen ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Wrench className="h-3 w-3" />
        <span>
          {steps.length} tool {steps.length === 1 ? "call" : "calls"}
          {isStreaming && "..."}
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2 border-l-2 border-slate-200 pl-3 dark:border-slate-700">
          {steps.map((step, i) => (
            <div key={i} className="text-xs">
              <div className="flex items-center gap-2">
                <Badge
                  variant="secondary"
                  className="bg-slate-100 px-1.5 py-0 text-[10px] text-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  {step.tool_name}
                </Badge>
                <span className="text-slate-500 dark:text-slate-400">{step.summary}</span>
                {isStreaming && i === steps.length - 1 && (
                  <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-500" />
                )}
              </div>

              {step.result && (
                <pre className="mt-1 max-h-32 overflow-x-auto overflow-y-auto rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
                  {step.result}
                </pre>
              )}

              {step.screenshot_url && (
                <div className="mt-2">
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}${step.screenshot_url}`}
                    alt={`${step.tool_name} screenshot`}
                    className="max-h-64 max-w-full cursor-pointer rounded-lg border border-slate-200 shadow-sm transition-opacity hover:opacity-90 dark:border-slate-700"
                    onClick={() =>
                      window.open(
                        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}${step.screenshot_url}`,
                        '_blank'
                      )
                    }
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
