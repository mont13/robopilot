import { API_BASE_URL } from "@/app/config/api";

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
    const response = await fetch(`${API_BASE_URL}/api/lmstudio/health`);
    return response.ok;
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

// Models
export async function listModels(): Promise<ModelInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/lmstudio/models`);
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
): Promise<ModelInfo[]> {
  try {
    const url = modelType
      ? `${API_BASE_URL}/api/lmstudio/models/loaded?model_type=${modelType}`
      : `${API_BASE_URL}/api/lmstudio/models/loaded`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to list loaded models: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error listing loaded models:", error);
    throw error;
  }
}

export async function loadModel(
  modelKey: string,
  ttl?: number,
): Promise<ModelInfo> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/lmstudio/models/load`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model_key: modelKey, ttl }),
    });

    if (!response.ok) {
      throw new Error(`Failed to load model: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error loading model ${modelKey}:`, error);
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
