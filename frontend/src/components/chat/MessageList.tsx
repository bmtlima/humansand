"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  isStreaming?: boolean;
}

export function MessageList({ messages, isLoading, isStreaming = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">Start a conversation</p>
          <p className="mt-1 text-sm">
            Ask your agent to find someone, check schedules, or coordinate tasks.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="mx-auto max-w-3xl space-y-4">
        {messages.map((msg, i) => {
          const isLastMessage = i === messages.length - 1;
          const isStreamingMessage = isLastMessage && isStreaming && msg.role === "assistant";

          return (
            <MessageBubble
              key={i}
              message={msg}
              isStreaming={isStreamingMessage}
            />
          );
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
