import { ChatResponse, Conversation, ConversationSummary, ReasoningStep } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export async function sendMessage(
  message: string,
  agent: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      agent,
      conversation_id: conversationId || null,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function sendMessageStream(
  message: string,
  agent: string,
  conversationId: string | null,
  onReasoningStep: (step: ReasoningStep) => void,
  onComplete: (conversationId: string, content: string) => void,
  onError: (error: string) => void
): Promise<void> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      agent,
      conversation_id: conversationId || null,
    }),
  });

  if (!res.ok) {
    onError(`Chat failed: ${res.status}`);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    onError("No response body");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE lines (delimited by double newline)
    while (buffer.includes("\n\n")) {
      const idx = buffer.indexOf("\n\n");
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 2);

      if (!line.startsWith("data: ")) continue;

      try {
        const event = JSON.parse(line.slice(6));

        if (event.type === "reasoning_step") {
          onReasoningStep({
            type: "tool_call",
            tool_name: event.tool_name,
            summary: event.summary,
            result: event.result,
          });
        } else if (event.type === "final") {
          onComplete(event.conversation_id, event.content);
        }
      } catch {
        // skip malformed events
      }
    }
  }
}

export async function listConversations(): Promise<ConversationSummary[]> {
  const res = await fetch(`${API_URL}/conversations`);
  if (!res.ok) throw new Error(`Failed to list conversations: ${res.status}`);
  return res.json();
}

export async function getConversation(id: string): Promise<Conversation> {
  const res = await fetch(`${API_URL}/conversations/${id}`);
  if (!res.ok) throw new Error(`Failed to get conversation: ${res.status}`);
  return res.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete conversation: ${res.status}`);
}
