import Constants from "expo-constants";
import {
  ConversationHistory,
  AgentExecutionRequest,
  AgentExecutionResponse,
  CreateSessionResponse,
} from "../types/api";

// Get API base URL from environment or use default
const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ||
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  "http://localhost:8009";

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    };

    const response = await fetch(url, {
      ...defaultOptions,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Session Management
  async createSession(name?: string): Promise<CreateSessionResponse> {
    const url = name
      ? `/api/agent/sessions?name=${encodeURIComponent(name)}`
      : "/api/agent/sessions";
    return this.makeRequest<CreateSessionResponse>(url, {
      method: "POST",
    });
  }

  async getActiveSession(): Promise<ConversationHistory | null> {
    try {
      return await this.makeRequest<ConversationHistory>(
        "/api/agent/sessions/active",
      );
    } catch (error: any) {
      if (error.message.includes("404")) {
        return null;
      }
      throw error;
    }
  }

  async getSessionHistory(sessionId: string): Promise<ConversationHistory> {
    return this.makeRequest<ConversationHistory>(
      `/api/agent/sessions/${sessionId}`,
    );
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.makeRequest(`/api/agent/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  // Chat Operations
  async sendMessage(
    request: AgentExecutionRequest,
  ): Promise<AgentExecutionResponse> {
    return this.makeRequest<AgentExecutionResponse>("/api/agent/chat", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Voice Operations
  async transcribeAudio(
    audioBlob: Blob,
    language: string = "en",
  ): Promise<{ text: string }> {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.wav");
    formData.append("language", language);
    formData.append("format", "wav");

    const response = await fetch(`${this.baseURL}/api/stt/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.status}`);
    }

    return response.json();
  }

  async synthesizeSpeech(text: string, voiceId?: string): Promise<ArrayBuffer> {
    const response = await fetch(`${this.baseURL}/api/tts/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        voice_id: voiceId,
      }),
    });

    if (!response.ok) {
      throw new Error(`TTS failed: ${response.status}`);
    }

    return response.arrayBuffer();
  }

  // Health Check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Utility method to update base URL (useful for settings)
  updateBaseURL(newBaseURL: string) {
    this.baseURL = newBaseURL;
  }

  getBaseURL(): string {
    return this.baseURL;
  }
}

export const apiService = new ApiService();
export default apiService;
