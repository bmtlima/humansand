"use client";

import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { Message } from "@/lib/types";

interface ChatAreaProps {
  messages: Message[];
  isLoading: boolean;
  isStreaming?: boolean;
  onSend: (message: string) => void;
  agent: string;
}

export function ChatArea({ messages, isLoading, isStreaming = false, onSend, agent }: ChatAreaProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200/80 bg-white/75 px-4 py-4 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight text-slate-900 dark:text-slate-100">
              {agent}&apos;s Agent
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Multi-agent negotiation assistant</p>
          </div>
          <ThemeToggle />
        </div>
      </div>

      <MessageList messages={messages} isLoading={isLoading} isStreaming={isStreaming} />
      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
}
