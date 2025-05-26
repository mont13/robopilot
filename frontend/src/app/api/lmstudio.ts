import { API_BASE_URL } from "@/app/config/api";
import { LLMConnectionResponse } from "@/app/api/connections";

// Types
export interface ModelInfo {
  id: string;
  name: string;
  type: string;
  instance_id?: string;
  context_length?: number;
}

export interface ChatMessage {
  role: string;
  content: string;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  name?: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
}

export interface CreateChatSessionRequest {
  name?: string;
}

export interface SingleMessageRequest {
  role: string;
  content: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface TextResponse {
  text: string;
}

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    // Try to get the active connection as a health check
    const response = await fetch(`${API_BASE_URL}/api/connections/active/`);
    return response.ok;
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

// Models
export async function listModels(): Promise<LLMConnectionResponse[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/`);
    if (!response.ok) {
      throw new Error(`Failed to list models: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error listing models:", error);
    throw error;
  }
}

export async function listLoadedModels(
  modelType?: string,
): Promise<LLMConnectionResponse[]> {
  try {
    // The API doesn't have direct endpoint for loaded models anymore
    // So we'll get all connections and filter the active ones
    const url = `${API_BASE_URL}/api/connections/`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to list loaded models: ${response.status}`);
    }
    
    const connections: LLMConnectionResponse[] = await response.json();
    return modelType 
      ? connections.filter(conn => conn.provider === modelType)
      : connections.filter(conn => conn.is_active);
  } catch (error) {
    console.error("Error listing loaded models:", error);
    throw error;
  }
}

export async function loadModel(
  connectionId: string,
  ttl?: number,
): Promise<LLMConnectionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/${connectionId}/activate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ttl }),
    });

    if (!response.ok) {
      throw new Error(`Failed to load model: ${response.status}`);
    }
    
    // Get the complete connection details after activation
    const activeResponse = await fetch(`${API_BASE_URL}/api/connections/active/`);
    if (!activeResponse.ok) {
      throw new Error(`Failed to get active connection: ${activeResponse.status}`);
    }
    
    return await activeResponse.json();
  } catch (error) {
    console.error(`Error loading model ${connectionId}:`, error);
    throw error;
  }
}

// Chat Sessions
export async function listChatSessions(): Promise<ChatSession[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/lmstudio/chat/sessions`);
    if (!response.ok) {
      throw new Error(`Failed to list chat sessions: ${response.status}`);
    }
    const data: ChatSessionListResponse = await response.json();
    return data.sessions;
  } catch (error) {
    console.error("Error listing chat sessions:", error);
    throw error;
  }
}

export async function createChatSession(name?: string): Promise<ChatSession> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/lmstudio/chat/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create chat session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error creating chat session:", error);
    throw error;
  }
}

export async function getChatSession(sessionId: string): Promise<ChatSession> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/lmstudio/chat/sessions/${sessionId}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get chat session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error getting chat session ${sessionId}:`, error);
    throw error;
  }
}

export async function deleteChatSession(sessionId: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/lmstudio/chat/sessions/${sessionId}`,
      {
        method: "DELETE",
      },
    );
    return response.ok;
  } catch (error) {
    console.error(`Error deleting chat session ${sessionId}:`, error);
    throw error;
  }
}

export async function getActiveSession(): Promise<ChatSession | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/lmstudio/chat/sessions/active/`,
    );
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to get active session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting active session:", error);
    throw error;
  }
}

// Chat Completions
export async function sendMessage(
  message: SingleMessageRequest,
): Promise<TextResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/lmstudio/chat/completions`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(message),
      },
    );

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error sending message:", error);
    throw error;
  }
}
