"use client";

import { useState } from "react";
import { ReasoningStep } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { ChevronRight, ChevronDown, Wrench } from "lucide-react";

interface ReasoningTraceProps {
  steps: ReasoningStep[];
}

export function ReasoningTrace({ steps }: ReasoningTraceProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <Wrench className="h-3 w-3" />
        <span>
          {steps.length} tool {steps.length === 1 ? "call" : "calls"}
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2 border-l-2 border-muted pl-3">
          {steps.map((step, i) => (
            <div key={i} className="text-xs">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                  {step.tool_name}
                </Badge>
                <span className="text-muted-foreground">{step.summary}</span>
              </div>
              {step.result && (
                <pre className="mt-1 rounded bg-muted/50 p-2 text-[11px] text-muted-foreground overflow-x-auto max-h-32 overflow-y-auto">
                  {step.result}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
