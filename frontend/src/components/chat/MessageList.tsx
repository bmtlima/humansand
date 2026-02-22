"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
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
      <div className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <Image
            src="/linkmate_2d-no-bg.png"
            alt="LinkMate"
            width={80}
            height={80}
            className="mx-auto mb-4"
          />
          <p className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">Start a conversation</p>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Ask your agent to find someone, check schedules, or coordinate tasks.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6">
      <div className="mx-auto max-w-4xl space-y-5">
        {messages.map((msg, i) => {
          const isLastMessage = i === messages.length - 1;
          const isStreamingMessage = isLastMessage && isStreaming && msg.role === "assistant";

          return <MessageBubble key={i} message={msg} isStreaming={isStreamingMessage} />;
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
