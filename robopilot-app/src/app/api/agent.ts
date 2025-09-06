import { API_BASE_URL } from "@/app/config/api";
import { LLMConnectionResponse } from "@/app/api/connections";

// Core API Types
export interface AgentMessage {
  role: "system" | "user" | "assistant";
  content: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface AgentSessionInfo {
  session_id: string;
  session_name?: string;
  message_count: number;
  tool_calls_count: number;
  created_at?: string;
  updated_at?: string;
  is_active: boolean;
  agent_config?: Record<string, any>;
}

export interface ConversationHistory {
  session_id: string;
  messages: AgentMessage[];
  created_at?: string;
  updated_at?: string;
}

export interface AgentExecutionRequest {
  session_id: string;
  message: string;
  temperature?: number;
  max_iterations?: number;
  max_retries?: number;
  include_robot_tools?: boolean;
  stream_response?: boolean;
  system_prompt_override?: string;
}

export interface AgentExecutionResponse {
  session_id: string;
  response: string;
  tool_calls?: Record<string, any>[];
  execution_time?: number;
  iterations_used?: number;
  metadata?: Record<string, any>;
}

// TTS Integration Types
export interface TTSVoice {
  id: string;
}

export interface TTSRequest {
  text: string;
  voice_id?: string;
  speaker_id?: number;
}

// Enhanced Message with TTS support
export interface EnhancedMessage extends AgentMessage {
  id: string;
  isPlaying?: boolean;
  hasAudio?: boolean;
  audioUrl?: string;
}

// Streaming support
export interface StreamingOptions {
  onChunk?: (chunk: string) => void;
  onComplete?: (fullResponse: string) => void;
  onError?: (error: Error) => void;
}

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/active/`);
    return response.ok;
  } catch (error) {
    console.error("Health check failed:", error);
    return false;
  }
}

// Models management
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

export async function getActiveModel(): Promise<LLMConnectionResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/active/`);
    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error(`Failed to get active model: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting active model:", error);
    return null;
  }
}

export async function activateModel(
  connectionId: string,
): Promise<LLMConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/connections/${connectionId}/activate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`Failed to activate model: ${response.status}`);
    }

    // Get the complete connection details after activation
    const activeResponse = await fetch(
      `${API_BASE_URL}/api/connections/active/`,
    );
    if (!activeResponse.ok) {
      throw new Error(
        `Failed to get active connection: ${activeResponse.status}`,
      );
    }

    return await activeResponse.json();
  } catch (error) {
    console.error(`Error activating model ${connectionId}:`, error);
    throw error;
  }
}

// Session management
export async function listSessions(): Promise<AgentSessionInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent/sessions`);
    if (!response.ok) {
      throw new Error(`Failed to list sessions: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error listing sessions:", error);
    throw error;
  }
}

export async function createSession(name?: string): Promise<AgentSessionInfo> {
  try {
    const url = new URL(`${API_BASE_URL}/api/agent/sessions`);
    if (name) {
      url.searchParams.append("name", name);
    }

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error creating session:", error);
    throw error;
  }
}

export async function getSession(
  sessionId: string,
): Promise<ConversationHistory> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/agent/sessions/${sessionId}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error getting session ${sessionId}:`, error);
    throw error;
  }
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/agent/sessions/${sessionId}`,
      {
        method: "DELETE",
      },
    );
    return response.ok;
  } catch (error) {
    console.error(`Error deleting session ${sessionId}:`, error);
    throw error;
  }
}

export async function getActiveSession(): Promise<ConversationHistory | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/agent/sessions/active/`);
    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error(`Failed to get active session: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting active session:", error);
    return null;
  }
}

// Chat functionality with streaming support
export async function sendMessage(
  request: AgentExecutionRequest,
  streamingOptions?: StreamingOptions,
): Promise<AgentExecutionResponse> {
  try {
    console.log("Sending request:", request);

    const response = await fetch(`${API_BASE_URL}/api/agent/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.status}`);
    }

    console.log(
      "Response headers:",
      Object.fromEntries(response.headers.entries()),
    );
    console.log("Response content type:", response.headers.get("content-type"));

    if (request.stream_response && streamingOptions) {
      try {
        return await handleStreamingResponse(response, streamingOptions);
      } catch (streamError) {
        console.warn(
          "Streaming failed, falling back to regular response:",
          streamError,
        );
        // Try to get regular JSON response as fallback
        try {
          const textResponse = await response.text();
          console.log("Fallback response text:", textResponse);
          const jsonResponse = JSON.parse(textResponse);
          streamingOptions.onComplete?.(jsonResponse.response || "");
          return jsonResponse;
        } catch (fallbackError) {
          console.error("Fallback also failed:", fallbackError);
          throw streamError;
        }
      }
    }

    const jsonResponse = await response.json();
    console.log("Non-streaming response:", jsonResponse);
    return jsonResponse;
  } catch (error) {
    console.error("Error sending message:", error);
    if (streamingOptions?.onError) {
      streamingOptions.onError(error as Error);
    }
    throw error;
  }
}

async function handleStreamingResponse(
  response: Response,
  options: StreamingOptions,
): Promise<AgentExecutionResponse> {
  if (!response.body) {
    throw new Error("No response body for streaming");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullResponse = "";
  let sessionId = "";
  let executionTime: number | undefined;
  let iterationsUsed: number | undefined;
  let toolCalls: Record<string, any>[] = [];
  let metadata: Record<string, any> = {};

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      console.log("Received chunk:", chunk);

      // Check if this is a complete JSON response (non-streaming fallback)
      if (chunk.trim().startsWith('{"session_id"')) {
        try {
          const completeResponse = JSON.parse(chunk);
          console.log(
            "Received complete JSON response instead of stream:",
            completeResponse,
          );

          fullResponse = completeResponse.response || "";
          sessionId = completeResponse.session_id || "";
          executionTime = completeResponse.execution_time;
          iterationsUsed = completeResponse.iterations_used;
          toolCalls = completeResponse.tool_calls || [];
          metadata = completeResponse.metadata || {};

          // Send the complete response as one chunk
          options.onChunk?.(fullResponse);
          break;
        } catch {
          console.log(
            "Failed to parse as complete JSON, continuing with streaming",
          );
        }
      }

      // Handle both SSE format and plain JSON chunks
      const lines = chunk.split("\n").filter((line) => line.trim());

      for (const line of lines) {
        let data: any;

        try {
          // Try SSE format first
          if (line.startsWith("data: ")) {
            data = JSON.parse(line.slice(6));
          } else if (line.trim().startsWith("{") && line.trim().endsWith("}")) {
            // Try direct JSON format
            data = JSON.parse(line);
          } else {
            // Plain text chunk - treat as response content
            if (line.trim()) {
              fullResponse += line + "\n";
              options.onChunk?.(line + "\n");
            }
            continue;
          }

          // Handle different chunk types
          if (data.chunk || data.response) {
            const content = data.chunk || data.response;
            fullResponse += content;
            options.onChunk?.(content);
          }

          if (data.session_id) {
            sessionId = data.session_id;
          }

          if (data.execution_time !== undefined) {
            executionTime = data.execution_time;
          }

          if (data.iterations_used !== undefined) {
            iterationsUsed = data.iterations_used;
          }

          if (data.tool_calls) {
            toolCalls = data.tool_calls;
          }

          if (data.metadata) {
            metadata = { ...metadata, ...data.metadata };
          }
        } catch (parseError) {
          console.warn(
            "Error parsing streaming chunk, treating as text:",
            line,
            parseError,
          );
          // If JSON parsing fails, treat as plain text content
          if (line.trim()) {
            fullResponse += line;
            options.onChunk?.(line);
          }
        }
      }
    }

    const finalResponse: AgentExecutionResponse = {
      session_id: sessionId,
      response: fullResponse,
      execution_time: executionTime,
      iterations_used: iterationsUsed,
      tool_calls: toolCalls,
      metadata,
    };

    options.onComplete?.(fullResponse);
    return finalResponse;
  } catch (error) {
    console.error("Streaming error:", error);
    options.onError?.(error as Error);
    throw error;
  } finally {
    reader.releaseLock();
  }
}

// TTS Integration
export async function getAvailableVoices(): Promise<TTSVoice[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tts/voices`);
    if (!response.ok) {
      throw new Error(`Failed to get voices: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error getting voices:", error);
    throw error;
  }
}

export async function synthesizeSpeech(request: TTSRequest): Promise<Blob> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tts/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to synthesize speech: ${response.status}`);
    }

    return await response.blob();
  } catch (error) {
    console.error("Error synthesizing speech:", error);
    throw error;
  }
}

export async function playMessageAudio(
  messageText: string,
  voiceId?: string,
): Promise<HTMLAudioElement> {
  try {
    // Parse the message to extract only the response part (no thinking)
    const parsed = parseMessageContent(messageText);

    const audioBlob = await synthesizeSpeech({
      text: parsed.response,
      voice_id: voiceId,
    });

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);

    // Clean up the URL when audio finishes playing
    audio.addEventListener("ended", () => {
      URL.revokeObjectURL(audioUrl);
    });

    await audio.play();
    return audio;
  } catch (error) {
    console.error("Error playing message audio:", error);
    throw error;
  }
}

// Enhanced messaging with TTS support
export async function sendMessageWithTTS(
  request: AgentExecutionRequest,
  options?: {
    voiceId?: string;
    enableTTS?: boolean;
    streamingOptions?: StreamingOptions;
  },
): Promise<{
  response: AgentExecutionResponse;
  audio?: HTMLAudioElement;
}> {
  const { voiceId, enableTTS = false, streamingOptions } = options || {};

  try {
    let audioElement: HTMLAudioElement | undefined;

    const enhancedStreamingOptions: StreamingOptions = {
      ...streamingOptions,
      onComplete: async (responseText: string) => {
        streamingOptions?.onComplete?.(responseText);

        // Wait for streaming to complete before starting TTS
        if (enableTTS && responseText.trim()) {
          try {
            // Parse response to get only non-thinking content for TTS
            const parsed = parseMessageContent(responseText);
            if (parsed.response.trim()) {
              audioElement = await playMessageAudio(parsed.response, voiceId);
            }
          } catch (ttsError) {
            console.warn("TTS failed, continuing without audio:", ttsError);
          }
        }
      },
    };

    const response = await sendMessage(request, enhancedStreamingOptions);

    // For non-streaming responses, handle TTS immediately
    if (!request.stream_response && enableTTS && response.response.trim()) {
      try {
        // Parse response to get only non-thinking content for TTS
        const parsed = parseMessageContent(response.response);
        if (parsed.response.trim()) {
          audioElement = await playMessageAudio(parsed.response, voiceId);
        }
      } catch (ttsError) {
        console.warn("TTS failed, continuing without audio:", ttsError);
      }
    }

    return { response, audio: audioElement };
  } catch (error) {
    console.error("Error sending message with TTS:", error);
    throw error;
  }
}

// Utility function to parse message content and separate thinking from response
export function parseMessageContent(content: string): {
  thinking: string | null;
  response: string;
} {
  // Handle multiple thinking blocks by combining them all
  const thinkingRegex = /<think>([\s\S]*?)<\/think>/g;
  const thinkingBlocks: string[] = [];
  let match;

  // Extract all thinking blocks
  while ((match = thinkingRegex.exec(content)) !== null) {
    const thinkingContent = match[1].trim();
    if (thinkingContent) {
      thinkingBlocks.push(thinkingContent);
    }
  }

  // Remove all thinking blocks from the response
  const response = content.replace(/<think>[\s\S]*?<\/think>/g, "").trim();

  // Combine all thinking blocks if any exist with better section labels
  let combinedThinking: string | null = null;
  if (thinkingBlocks.length > 0) {
    if (thinkingBlocks.length === 1) {
      combinedThinking = thinkingBlocks[0];
    } else {
      combinedThinking = thinkingBlocks
        .map((block, index) => {
          return `[Thinking Section ${index + 1}]\n${block}`;
        })
        .join("\n\n" + "=".repeat(50) + "\n\n");
    }
  }

  return {
    thinking: combinedThinking,
    response: response || "Processing...",
  };
}

// Utility function to create enhanced messages with TTS support
export function createEnhancedMessage(
  message: AgentMessage,
  id: string,
): EnhancedMessage {
  return {
    ...message,
    id,
    isPlaying: false,
    hasAudio: false,
  };
}

// Utility function to convert conversation history to enhanced messages
export function enhanceConversationHistory(
  history: ConversationHistory,
): ConversationHistory & { enhancedMessages: EnhancedMessage[] } {
  const enhancedMessages = history.messages.map((msg, index) =>
    createEnhancedMessage(msg, `${history.session_id}-${index}`),
  );

  return {
    ...history,
    enhancedMessages,
  };
}
