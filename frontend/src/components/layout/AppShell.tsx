"use client";

import { useState, useCallback } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";
import { getConversation } from "@/lib/api";

const AGENTS = ["Alice", "Bob", "Charlie"] as const;

export function AppShell() {
  const [agent, setAgent] = useState<string>("Alice");
  const { messages, conversationId, isLoading, send, loadMessages, reset } =
    useChat(agent);
  const { conversations, refresh, deleteConversation } = useConversations();

  const handleSend = useCallback(
    async (text: string) => {
      const newConvId = await send(text);
      // Refresh sidebar after sending
      setTimeout(() => refresh(), 500);
      return newConvId;
    },
    [send, refresh]
  );

  const handleNewChat = useCallback(() => {
    reset();
  }, [reset]);

  const handleSelectConversation = useCallback(
    async (id: string) => {
      try {
        const conv = await getConversation(id);
        setAgent(conv.agent);
        loadMessages(conv.messages, conv.id);
      } catch (err) {
        console.error("Failed to load conversation:", err);
      }
    },
    [loadMessages]
  );

  const handleDeleteConversation = useCallback(
    async (id: string) => {
      await deleteConversation(id);
      if (id === conversationId) {
        reset();
      }
    },
    [deleteConversation, conversationId, reset]
  );

  return (
    <div className="flex h-screen">
      <Sidebar
        conversations={conversations}
        activeConversationId={conversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      <div className="flex flex-1 flex-col">
        {/* Agent selector */}
        <div className="flex items-center gap-2 border-b px-4 py-2 bg-muted/20">
          <span className="text-xs text-muted-foreground">Agent:</span>
          {AGENTS.map((a) => (
            <button
              key={a}
              onClick={() => {
                setAgent(a);
                reset();
              }}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                agent === a
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              {a}
            </button>
          ))}
        </div>

        <div className="flex-1">
          <ChatArea
            messages={messages}
            isLoading={isLoading}
            onSend={handleSend}
            agent={agent}
          />
        </div>
      </div>
    </div>
  );
}
