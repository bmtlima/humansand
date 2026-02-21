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
        <Avatar className="h-8 w-8 shrink-0 mt-0.5">
          <AvatarFallback className="bg-primary/10 text-primary">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        {/* Hide empty content bubble while streaming; show thinking if no steps yet */}
        {(!isStreaming || message.content) ? (
          <div
            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              isUser
                ? "bg-primary text-primary-foreground"
                : "bg-muted"
            }`}
          >
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : isStreaming && (!message.reasoning_steps || message.reasoning_steps.length === 0) ? (
          <div className="rounded-2xl px-4 py-2.5 text-sm leading-relaxed bg-muted">
            <p className="text-muted-foreground flex items-center gap-2">
              Thinking
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
            </p>
          </div>
        ) : null}

        {!isUser && message.reasoning_steps && (
          <ReasoningTrace steps={message.reasoning_steps} isStreaming={isStreaming} />
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 shrink-0 mt-0.5">
          <AvatarFallback className="bg-muted">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
}
