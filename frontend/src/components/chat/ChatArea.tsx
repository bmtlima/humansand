"use client";

import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
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
      <div className="border-b px-4 py-3">
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <h2 className="font-semibold">{agent}&apos;s Agent</h2>
          <span className="inline-flex h-2 w-2 rounded-full bg-green-500" />
        </div>
      </div>

      <MessageList messages={messages} isLoading={isLoading} isStreaming={isStreaming} />
      <ChatInput onSend={onSend} disabled={isLoading} />
    </div>
  );
}
