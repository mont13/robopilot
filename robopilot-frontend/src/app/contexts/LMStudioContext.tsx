"use client";

import {
  LLMConnectionResponse,
  activateConnection,
  checkServerHealth,
  getActiveConnection,
  listConnections,
} from "@/app/api/connections";
import {
  AgentSessionInfo,
  ConversationHistory,
  AgentExecutionRequest,
  EnhancedMessage,
  createSession,
  deleteSession,
  getActiveSession,
  getSession,
  listSessions,
  sendMessageWithTTS,
  getAvailableVoices,
  TTSVoice,
  enhanceConversationHistory,
  parseMessageContent,
} from "@/app/api/agent";
import { selectStreamingSettings } from "@/app/lib/features/settings/settingsSlice";
import { useAppSelector } from "@/app/lib/hooks";
import { useEvent } from "@/app/contexts/EventContext";
import { SessionStatus } from "@/app/types";
import { getObjectCookie, setObjectCookie } from "@/app/utils/cookies";
import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  useRef,
} from "react";
import { v4 as uuidv4 } from "uuid";

interface LMStudioContextProps {
  sessionStatus: SessionStatus;
  currentSession: ConversationHistory | null;
  chatSessions: AgentSessionInfo[];
  connections: LLMConnectionResponse[];
  activeConnection: LLMConnectionResponse | null;
  availableVoices: TTSVoice[];
  messages: EnhancedMessage[];
  isStreaming: boolean;
  isTTSEnabled: boolean;
  selectedVoice: string | null;
  currentAudio: HTMLAudioElement | null;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  sendUserMessage: (
    content: string,
    options?: {
      temperature?: number;
      enableStreaming?: boolean;
      enableTTS?: boolean;
    },
  ) => Promise<string>;
  deleteChatSessionById: (sessionId: string) => Promise<boolean>;
  loadChatSession: (sessionId: string) => Promise<ConversationHistory | null>;
  createNewChatSession: (name?: string) => Promise<AgentSessionInfo | null>;
  refreshSessions: () => Promise<void>;
  activateConnectionById: (connectionId: string) => Promise<boolean>;
  toggleTTS: () => void;
  setSelectedVoice: (voiceId: string | null) => void;
  playMessageAudio: (messageId: string) => Promise<void>;
  stopCurrentAudio: () => void;
  refreshVoices: () => Promise<void>;
}

const LMStudioContext = createContext<LMStudioContextProps | undefined>(
  undefined,
);

export function LMStudioProvider({ children }: { children: ReactNode }) {
  const [sessionStatus, setSessionStatus] =
    useState<SessionStatus>("DISCONNECTED");
  const [currentSession, setCurrentSession] =
    useState<ConversationHistory | null>(null);
  const [chatSessions, setChatSessions] = useState<AgentSessionInfo[]>([]);
  const [connections, setConnections] = useState<LLMConnectionResponse[]>([]);
  const [activeConnection, setActiveConnection] =
    useState<LLMConnectionResponse | null>(null);
  const [availableVoices, setAvailableVoices] = useState<TTSVoice[]>([]);
  const [messages, setMessages] = useState<EnhancedMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(
    null,
  );

  const streamingContentRef = useRef("");
  const { streamingEnabled } = useAppSelector(selectStreamingSettings);
  const { logClientEvent, logServerEvent } = useEvent();

  // Function to check connection status
  const checkConnection = useCallback(async () => {
    try {
      const isConnected = await checkServerHealth();
      return isConnected;
    } catch {
      return false;
    }
  }, []);

  // Load TTS voices
  const refreshVoices = useCallback(async () => {
    try {
      const voices = await getAvailableVoices();
      setAvailableVoices(voices);

      // Auto-select first voice if none selected
      if (voices.length > 0 && !selectedVoice) {
        setSelectedVoice(voices[0].id);
      }
    } catch (error) {
      console.error("Error loading voices:", error);
    }
  }, [selectedVoice]);

  // Connect to backend
  const connect = useCallback(async () => {
    try {
      setSessionStatus("CONNECTING");
      logClientEvent({ type: "connection_attempt" });

      const isConnected = await checkConnection();
      if (!isConnected) {
        throw new Error("Failed to connect to backend API");
      }

      // Get available connections
      const connectionsList = await listConnections();
      setConnections(connectionsList);

      // Get active connection if any
      const active = await getActiveConnection();
      if (active) {
        setActiveConnection(active);
      }

      // Get chat sessions
      const sessions = await listSessions();
      setChatSessions(sessions);

      // Try to get active session
      const activeSession = await getActiveSession();
      if (activeSession) {
        const enhanced = enhanceConversationHistory(activeSession);
        setCurrentSession(activeSession);
        setMessages(enhanced.enhancedMessages);
      }

      // Load TTS voices
      await refreshVoices();

      setSessionStatus("CONNECTED");
      logClientEvent({
        type: "connection_success",
        connectionsCount: connectionsList.length,
        sessionsCount: sessions.length,
        hasActiveSession: !!activeSession,
        hasActiveConnection: !!active,
      });

      return true;
    } catch (error) {
      console.error("Connection error:", error);
      setSessionStatus("DISCONNECTED");
      logClientEvent({
        type: "connection_error",
        error: error instanceof Error ? error.message : String(error),
      });
      return false;
    }
  }, [checkConnection, logClientEvent, refreshVoices]);

  // Disconnect from backend
  const disconnect = useCallback(() => {
    setSessionStatus("DISCONNECTED");
    setCurrentSession(null);
    setMessages([]);
    stopCurrentAudio();
    logClientEvent({ type: "disconnect" });
  }, [logClientEvent]);

  // Stop current audio playback
  const stopCurrentAudio = useCallback(() => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
    }

    // Update message states
    setMessages((prev) => prev.map((msg) => ({ ...msg, isPlaying: false })));
  }, [currentAudio]);

  // Toggle TTS on/off
  const toggleTTS = useCallback(() => {
    setIsTTSEnabled((prev) => !prev);
    if (!isTTSEnabled) {
      stopCurrentAudio();
    }
  }, [isTTSEnabled, stopCurrentAudio]);

  // Play audio for a specific message
  const playMessageAudio = useCallback(
    async (messageId: string) => {
      const message = messages.find((msg) => msg.id === messageId);
      if (!message || message.role !== "assistant") return;

      try {
        stopCurrentAudio();

        setMessages((prev) =>
          prev.map((msg) => ({
            ...msg,
            isPlaying: msg.id === messageId,
          })),
        );

        // Parse message content to get only the response part (no thinking)
        const parsedContent = parseMessageContent(message.content);

        const { playMessageAudio } = await import("@/app/api/agent");
        const audio = await playMessageAudio(
          parsedContent.response,
          selectedVoice || undefined,
        );

        setCurrentAudio(audio);

        audio.addEventListener("ended", () => {
          setCurrentAudio(null);
          setMessages((prev) =>
            prev.map((msg) => ({ ...msg, isPlaying: false })),
          );
        });

        audio.addEventListener("error", () => {
          setCurrentAudio(null);
          setMessages((prev) =>
            prev.map((msg) => ({ ...msg, isPlaying: false })),
          );
        });
      } catch (error) {
        console.error("Error playing message audio:", error);
        setMessages((prev) =>
          prev.map((msg) => ({ ...msg, isPlaying: false })),
        );
      }
    },
    [messages, selectedVoice, stopCurrentAudio],
  );

  // Activate a connection
  const activateConnectionById = useCallback(
    async (connectionId: string) => {
      if (sessionStatus !== "CONNECTED") {
        return false;
      }

      try {
        const result = await activateConnection(connectionId);

        if (result) {
          // Update active connection
          const active = await getActiveConnection();
          if (active) {
            setActiveConnection(active);
          }

          logClientEvent({
            type: "connection_activated",
            connectionId: connectionId,
            connectionName: result.name,
            provider: result.provider,
          });

          return true;
        }
        return false;
      } catch (error) {
        console.error(`Error activating connection ${connectionId}:`, error);
        logClientEvent({
          type: "connection_activation_error",
          connectionId,
          error: error instanceof Error ? error.message : String(error),
        });
        return false;
      }
    },
    [sessionStatus, logClientEvent],
  );

  // Create a new chat session
  const createNewChatSession = useCallback(
    async (name?: string) => {
      if (sessionStatus !== "CONNECTED") {
        return null;
      }

      try {
        const newSession = await createSession(
          name || `Session ${new Date().toLocaleTimeString()}`,
        );

        // Update sessions list
        setChatSessions((prev) => [newSession, ...prev]);

        // Load the new session
        const sessionHistory = await getSession(newSession.session_id);
        const enhanced = enhanceConversationHistory(sessionHistory);
        setCurrentSession(sessionHistory);
        setMessages(enhanced.enhancedMessages);

        logClientEvent({
          type: "session_created",
          sessionId: newSession.session_id,
          sessionName: newSession.session_name,
        });

        return newSession;
      } catch (error) {
        console.error("Error creating session:", error);
        logClientEvent({
          type: "session_creation_error",
          error: error instanceof Error ? error.message : String(error),
        });
        return null;
      }
    },
    [sessionStatus, logClientEvent],
  );

  // Load a specific chat session
  const loadChatSession = useCallback(
    async (sessionId: string) => {
      if (sessionStatus !== "CONNECTED") {
        return null;
      }

      try {
        const session = await getSession(sessionId);
        const enhanced = enhanceConversationHistory(session);
        setCurrentSession(session);
        setMessages(enhanced.enhancedMessages);

        logClientEvent({
          type: "session_loaded",
          sessionId: session.session_id,
          messageCount: session.messages?.length || 0,
        });

        return session;
      } catch (error) {
        console.error(`Error loading session ${sessionId}:`, error);
        logClientEvent({
          type: "session_load_error",
          sessionId,
          error: error instanceof Error ? error.message : String(error),
        });
        return null;
      }
    },
    [sessionStatus, logClientEvent],
  );

  // Delete a chat session
  const deleteChatSessionById = useCallback(
    async (sessionId: string) => {
      if (sessionStatus !== "CONNECTED") {
        return false;
      }

      try {
        const success = await deleteSession(sessionId);

        if (success) {
          // Update sessions list
          setChatSessions((prev) =>
            prev.filter((s) => s.session_id !== sessionId),
          );

          // If current session was deleted, clear it
          if (currentSession?.session_id === sessionId) {
            setCurrentSession(null);
            setMessages([]);
            stopCurrentAudio();
          }

          logClientEvent({
            type: "session_deleted",
            sessionId,
          });
        }

        return success;
      } catch (error) {
        console.error(`Error deleting session ${sessionId}:`, error);
        logClientEvent({
          type: "session_deletion_error",
          sessionId,
          error: error instanceof Error ? error.message : String(error),
        });
        return false;
      }
    },
    [sessionStatus, currentSession, logClientEvent, stopCurrentAudio],
  );

  // Refresh the list of sessions
  const refreshSessions = useCallback(async () => {
    if (sessionStatus !== "CONNECTED") {
      return;
    }

    try {
      const sessions = await listSessions();
      setChatSessions(sessions);

      logClientEvent({
        type: "sessions_refreshed",
        count: sessions.length,
      });
    } catch (error) {
      console.error("Error refreshing sessions:", error);
      logClientEvent({
        type: "sessions_refresh_error",
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }, [sessionStatus, logClientEvent]);

  // Send a message and get a response
  const sendUserMessage = useCallback(
    async (
      content: string,
      options: {
        temperature?: number;
        enableStreaming?: boolean;
        enableTTS?: boolean;
      } = {},
    ) => {
      if (sessionStatus !== "CONNECTED" || !content.trim() || !currentSession) {
        return "";
      }

      const {
        temperature = 0.7,
        enableStreaming = streamingEnabled,
        enableTTS = isTTSEnabled,
      } = options;

      console.log("Streaming settings debug:", {
        streamingEnabled,
        enableStreaming,
        options,
        reduxStreamingState: streamingEnabled,
      });

      const messageId = uuidv4();
      streamingContentRef.current = "";

      try {
        setIsStreaming(enableStreaming);

        logClientEvent({
          type: "message_send",
          event_id: messageId,
          role: "user",
          contentLength: content.length,
          streaming: enableStreaming,
          tts: enableTTS,
        });

        // Add user message to local state
        const userMessage: EnhancedMessage = {
          role: "user",
          content,
          id: `${currentSession.session_id}-user-${Date.now()}`,
          timestamp: new Date().toISOString(),
          isPlaying: false,
          hasAudio: false,
          metadata: {
            contentLength: content.length,
            wordCount: content.trim().split(/\s+/).length,
            timestamp: new Date().toISOString(),
            messageId: messageId,
          },
        };
        setMessages((prev) => [...prev, userMessage]);

        // Prepare request
        const request: AgentExecutionRequest = {
          session_id: currentSession.session_id,
          message: content,
          temperature,
          stream_response: enableStreaming,
          include_robot_tools: true,
          max_iterations: 20,
          max_retries: 3,
        };

        console.log("Final request being sent:", {
          stream_response: request.stream_response,
          enableStreaming,
          streamingEnabled,
        });

        // Send to API with streaming and TTS support
        let response, audio;
        try {
          const result = await sendMessageWithTTS(request, {
            enableTTS,
            voiceId: selectedVoice || undefined,
            streamingOptions: enableStreaming
              ? {
                  onChunk: (chunk: string) => {
                    streamingContentRef.current += chunk;

                    // Update the assistant message in real-time
                    setMessages((prev) => {
                      const userMsgIndex = prev.findIndex(
                        (msg) => msg.id === userMessage.id,
                      );
                      if (userMsgIndex === -1) return prev;

                      const assistantMsgId = `${currentSession.session_id}-assistant-${Date.now()}`;
                      const existingAssistantIndex = prev.findIndex(
                        (msg, idx) =>
                          idx > userMsgIndex && msg.role === "assistant",
                      );

                      const assistantMessage: EnhancedMessage = {
                        role: "assistant",
                        content: streamingContentRef.current,
                        id:
                          existingAssistantIndex >= 0
                            ? prev[existingAssistantIndex].id
                            : assistantMsgId,
                        timestamp: new Date().toISOString(),
                        isPlaying: false,
                        hasAudio: enableTTS,
                        metadata: {
                          temperature,
                          streaming: enableStreaming,
                          tts: enableTTS,
                        },
                      };

                      if (existingAssistantIndex >= 0) {
                        // Update existing message
                        const newMessages = [...prev];
                        newMessages[existingAssistantIndex] = assistantMessage;
                        return newMessages;
                      } else {
                        // Add new assistant message
                        return [...prev, assistantMessage];
                      }
                    });
                  },
                  onComplete: (finalResponse: string) => {
                    console.log(
                      "Streaming completed with response:",
                      finalResponse,
                    );
                    setIsStreaming(false);
                  },
                  onError: (error: Error) => {
                    console.error("Streaming error:", error);
                    setIsStreaming(false);
                    // Add error message if streaming fails
                    const errorMessage: EnhancedMessage = {
                      role: "assistant",
                      content:
                        "Sorry, there was an error processing your request. Please try again.",
                      id: `${currentSession.session_id}-error-${Date.now()}`,
                      timestamp: new Date().toISOString(),
                      isPlaying: false,
                      hasAudio: false,
                      metadata: {
                        error: true,
                        errorMessage: error.message,
                      },
                    };
                    setMessages((prev) => [...prev, errorMessage]);
                  },
                }
              : undefined,
          });
          response = result.response;
          audio = result.audio;
        } catch (error) {
          console.error("Failed to send message:", error);
          setIsStreaming(false);

          // Add error message to chat
          const errorMessage: EnhancedMessage = {
            role: "assistant",
            content:
              "I apologize, but I encountered an error while processing your message. Please try again.",
            id: `${currentSession.session_id}-error-${Date.now()}`,
            timestamp: new Date().toISOString(),
            isPlaying: false,
            hasAudio: false,
            metadata: {
              error: true,
              errorMessage:
                error instanceof Error ? error.message : String(error),
            },
          };
          setMessages((prev) => [...prev, errorMessage]);

          throw error;
        }

        // For non-streaming responses, add the complete message
        if (!enableStreaming && response) {
          const assistantMessage: EnhancedMessage = {
            role: "assistant",
            content: response.response,
            id: `${currentSession.session_id}-assistant-${Date.now()}`,
            timestamp: new Date().toISOString(),
            isPlaying: false,
            hasAudio: enableTTS && !!audio,
            metadata: {
              temperature,
              streaming: false,
              tts: enableTTS,
              execution_time: response.execution_time,
              iterations_used: response.iterations_used,
              tool_calls: response.tool_calls,
              ...response.metadata,
            },
          };
          setMessages((prev) => [...prev, assistantMessage]);
        } else if (enableStreaming && response) {
          // Update final streaming message with complete metadata
          setMessages((prev) => {
            const lastAssistantIndex = [...prev]
              .reverse()
              .findIndex((msg) => msg.role === "assistant");
            if (lastAssistantIndex === -1) return prev;

            const actualIndex = prev.length - 1 - lastAssistantIndex;
            const newMessages = [...prev];
            newMessages[actualIndex] = {
              ...newMessages[actualIndex],
              metadata: {
                ...newMessages[actualIndex].metadata,
                execution_time: response.execution_time,
                iterations_used: response.iterations_used,
                tool_calls: response.tool_calls,
                ...response.metadata,
              },
            };
            return newMessages;
          });
        }

        // Handle audio playback
        if (audio) {
          setCurrentAudio(audio);
          audio.addEventListener("ended", () => {
            setCurrentAudio(null);
            setMessages((prev) =>
              prev.map((msg) => ({ ...msg, isPlaying: false })),
            );
          });
        }

        setIsStreaming(false);

        logServerEvent({
          type: "message_response",
          event_id: messageId,
          role: "assistant",
          contentLength: response.response.length,
          streaming: enableStreaming,
          tts: enableTTS,
          hasAudio: !!audio,
        });

        return response?.response || "";
      } catch (error) {
        console.error("Error sending message:", error);
        setIsStreaming(false);

        logClientEvent({
          type: "message_error",
          event_id: messageId,
          error: error instanceof Error ? error.message : String(error),
        });
        return "";
      }
    },
    [
      sessionStatus,
      currentSession,
      isTTSEnabled,
      selectedVoice,
      logClientEvent,
      logServerEvent,
    ],
  );

  // Load chat session from cookies
  useEffect(() => {
    let isMounted = true;

    if (sessionStatus === "CONNECTED" && !currentSession) {
      // Get the last active session ID from cookie
      const savedSettings = getObjectCookie<{
        activeSessionId: string | null;
        isTTSEnabled: boolean;
        selectedVoice: string | null;
      }>("lmStudioSettings", {
        activeSessionId: null,
        isTTSEnabled: false,
        selectedVoice: null,
      });

      // Restore TTS settings
      if (savedSettings.isTTSEnabled !== undefined) {
        setIsTTSEnabled(savedSettings.isTTSEnabled);
      }
      if (savedSettings.selectedVoice) {
        setSelectedVoice(savedSettings.selectedVoice);
      }

      if (savedSettings.activeSessionId) {
        getSession(savedSettings.activeSessionId)
          .then((session) => {
            if (isMounted) {
              const enhanced = enhanceConversationHistory(session);
              setCurrentSession(session);
              setMessages(enhanced.enhancedMessages);
              logClientEvent({
                type: "session_restored_from_cookie",
                sessionId: session.session_id,
              });
            }
          })
          .catch(() => {
            console.log("Could not restore saved session, creating a new one");
          });
      }
    }

    return () => {
      isMounted = false;
    };
  }, [sessionStatus, currentSession, logClientEvent]);

  // Save current session and settings to cookies
  useEffect(() => {
    if (typeof window !== "undefined") {
      const timeoutId = setTimeout(() => {
        setObjectCookie("lmStudioSettings", {
          activeSessionId: currentSession?.session_id || null,
          isTTSEnabled,
          selectedVoice,
        });
      }, 300);

      return () => {
        clearTimeout(timeoutId);
      };
    }
  }, [currentSession, isTTSEnabled, selectedVoice]);

  // Initialize periodic connection checking
  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;
    let isMounted = true;

    if (sessionStatus === "CONNECTED") {
      const timeoutId = setTimeout(() => {
        intervalId = setInterval(async () => {
          if (!isMounted) return;

          try {
            const isStillConnected = await checkConnection();
            if (
              !isStillConnected &&
              sessionStatus === "CONNECTED" &&
              isMounted
            ) {
              console.warn("Lost connection to backend API");
              setSessionStatus("DISCONNECTED");
              stopCurrentAudio();
              logClientEvent({ type: "connection_lost" });
            }
          } catch (error) {
            console.error("Error checking connection:", error);
          }
        }, 60000);
      }, 5000);

      return () => {
        isMounted = false;
        if (timeoutId) clearTimeout(timeoutId);
        if (intervalId) clearInterval(intervalId);
      };
    }

    return () => {
      isMounted = false;
    };
  }, [sessionStatus, checkConnection, logClientEvent, stopCurrentAudio]);

  return (
    <LMStudioContext.Provider
      value={{
        sessionStatus,
        currentSession,
        chatSessions,
        connections,
        activeConnection,
        availableVoices,
        messages,
        isStreaming,
        isTTSEnabled,
        selectedVoice,
        currentAudio,
        connect,
        disconnect,
        sendUserMessage,
        deleteChatSessionById,
        loadChatSession,
        createNewChatSession,
        refreshSessions,
        activateConnectionById,
        toggleTTS,
        setSelectedVoice,
        playMessageAudio,
        stopCurrentAudio,
        refreshVoices,
      }}
    >
      {children}
    </LMStudioContext.Provider>
  );
}

export function useLMStudio() {
  const context = useContext(LMStudioContext);
  if (context === undefined) {
    throw new Error("useLMStudio must be used within an LMStudioProvider");
  }
  return context;
}
