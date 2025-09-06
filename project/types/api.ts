export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ConversationHistory {
  messages: ConversationMessage[];
  sessionId: string;
}

export interface AgentExecutionRequest {
  message: string;
  sessionId?: string;
}

export interface AgentExecutionResponse {
  response: string;
  sessionId: string;
  messageId: string;
}

export interface CreateSessionResponse {
  sessionId: string;
}

export type InputMode = 'keyboard' | 'voice';