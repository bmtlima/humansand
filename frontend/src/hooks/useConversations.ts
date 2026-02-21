"use client";

import { useState, useCallback, useEffect } from "react";
import { ConversationSummary } from "@/lib/types";
import {
  listConversations,
  deleteConversation as apiDeleteConversation,
} from "@/lib/api";

export function useConversations() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const convos = await listConversations();
      setConversations(convos);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteConversation = useCallback(
    async (id: string) => {
      try {
        await apiDeleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
      } catch (err) {
        console.error("Failed to delete conversation:", err);
      }
    },
    []
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { conversations, isLoading, refresh, deleteConversation };
}
