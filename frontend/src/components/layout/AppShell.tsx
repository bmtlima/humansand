"use client";

import { useCallback } from "react";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";
import { getConversation } from "@/lib/api";

const AGENT = "Alice";

export function AppShell() {
  const { messages, conversationId, isLoading, isStreaming, send, loadMessages, reset } =
    useChat(AGENT);
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
        <ChatArea
          messages={messages}
          isLoading={isLoading}
          isStreaming={isStreaming}
          onSend={handleSend}
          agent={AGENT}
        />
      </div>
    </div>
  );
}
