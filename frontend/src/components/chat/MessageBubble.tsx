"use client";

import { Message } from "@/lib/types";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ReasoningTrace } from "./ReasoningTrace";
import { User, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="mt-0.5 h-8 w-8 shrink-0 border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <AvatarFallback className="bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`max-w-[88%] sm:max-w-[80%] ${isUser ? "order-first" : ""}`}>
        {!isStreaming || message.content ? (
          <div
            className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
              isUser
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                : "border border-slate-200 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : isStreaming && (!message.reasoning_steps || message.reasoning_steps.length === 0) ? (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <p className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
              Thinking
              <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-500" />
            </p>
          </div>
        ) : null}

        {!isUser && message.reasoning_steps && (
          <ReasoningTrace steps={message.reasoning_steps} isStreaming={isStreaming} />
        )}
      </div>

      {isUser && (
        <Avatar className="mt-0.5 h-8 w-8 shrink-0 border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <AvatarFallback className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
