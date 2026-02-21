"use client";

import { useState, useCallback, useRef } from "react";
import { Message, ReasoningStep } from "@/lib/types";
import { sendMessageStream } from "@/lib/api";

export function useChat(agent: string = "Alice") {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const convIdRef = useRef<string | null>(null);

  const send = useCallback(
    async (text: string) => {
      const userMessage: Message = { role: "user", content: text };
      const placeholderAssistant: Message = {
        role: "assistant",
        content: "",
        reasoning_steps: [],
      };

      setMessages((prev) => [...prev, userMessage, placeholderAssistant]);
      setIsLoading(true);
      setIsStreaming(true);

      try {
        await sendMessageStream(
          text,
          agent,
          convIdRef.current,
          // onReasoningStep
          (step: ReasoningStep) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = { ...updated[updated.length - 1] };
              last.reasoning_steps = [...(last.reasoning_steps || []), step];
              updated[updated.length - 1] = last;
              return updated;
            });
          },
          // onComplete
          (newConvId: string, content: string) => {
            convIdRef.current = newConvId;
            setConversationId(newConvId);
            setMessages((prev) => {
              const updated = [...prev];
              const last = { ...updated[updated.length - 1] };
              last.content = content;
              updated[updated.length - 1] = last;
              return updated;
            });
          },
          // onError
          (error: string) => {
            setMessages((prev) => {
              const updated = [...prev];
              const last = { ...updated[updated.length - 1] };
              last.content = "Sorry, something went wrong. Please try again.";
              updated[updated.length - 1] = last;
              return updated;
            });
            console.error(error);
          }
        );
      } catch (err) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = { ...updated[updated.length - 1] };
          last.content = "Sorry, something went wrong. Please try again.";
          updated[updated.length - 1] = last;
          return updated;
        });
        console.error(err);
      } finally {
        setIsLoading(false);
        setIsStreaming(false);
      }

      return convIdRef.current;
    },
    [agent]
  );

  const loadMessages = useCallback((msgs: Message[], convId: string) => {
    setMessages(msgs);
    setConversationId(convId);
    convIdRef.current = convId;
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    convIdRef.current = null;
  }, []);

  return { messages, conversationId, isLoading, isStreaming, send, loadMessages, reset };
}
