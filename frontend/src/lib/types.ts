export interface ReasoningStep {
  type: string;
  tool_name: string;
  summary: string;
  result: string;
  screenshot_url?: string | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  reasoning_steps?: ReasoningStep[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  agent: string;
}

export interface Conversation {
  id: string;
  title: string;
  agent: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
}

export interface CalendarEvent {
  event: string;
  time: string;
  duration: string;
}

export interface Profile {
  name: string;
  role: string;
  skills: string[];
}

export interface AgentData {
  calendar: CalendarEvent[];
  profile: Profile;
}
