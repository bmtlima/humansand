"use client";

import { useState, useCallback } from "react";
import { Message } from "@/lib/types";
import { sendMessage } from "@/lib/api";

export function useChat(agent: string = "Alice") {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const send = useCallback(
    async (text: string) => {
      const userMessage: Message = { role: "user", content: text };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const res = await sendMessage(text, agent, conversationId);
        setConversationId(res.conversation_id);
        setMessages((prev) => [...prev, res.message]);
        return res.conversation_id;
      } catch (err) {
        const errorMessage: Message = {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        };
        setMessages((prev) => [...prev, errorMessage]);
        console.error(err);
        return conversationId;
      } finally {
        setIsLoading(false);
      }
    },
    [agent, conversationId]
  );

  const loadMessages = useCallback((msgs: Message[], convId: string) => {
    setMessages(msgs);
    setConversationId(convId);
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return { messages, conversationId, isLoading, send, loadMessages, reset };
}
