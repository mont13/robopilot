"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { v4 as uuidv4 } from "uuid";
import {
  checkHealth,
  listModels,
  listChatSessions,
  getActiveSession,
  createChatSession,
  getChatSession,
  deleteChatSession,
  sendMessage,
  ChatSession,
  ModelInfo,
} from "@/app/api/lmstudio";
import { useEvent } from "@/app/contexts/EventContext";
import { SessionStatus } from "@/app/types";
import { getObjectCookie, setObjectCookie } from "@/app/utils/cookies";

interface LMStudioContextProps {
  sessionStatus: SessionStatus;
  currentSession: ChatSession | null;
  chatSessions: ChatSession[];
  models: ModelInfo[];
  loadedModel: ModelInfo | null;
  messages: {
    role: string;
    content: string;
    created_at?: string;
  }[];
  connect: () => Promise<boolean>;
  disconnect: () => void;
  sendUserMessage: (content: string) => Promise<string>;
  deleteChatSessionById: (sessionId: string) => Promise<boolean>;
  loadChatSession: (sessionId: string) => Promise<ChatSession | null>;
  createNewChatSession: (name?: string) => Promise<ChatSession | null>;
  refreshSessions: () => Promise<void>;
}

const LMStudioContext = createContext<LMStudioContextProps | undefined>(
  undefined,
);

export function LMStudioProvider({ children }: { children: ReactNode }) {
  const [sessionStatus, setSessionStatus] =
    useState<SessionStatus>("DISCONNECTED");
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(
    null,
  );
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loadedModel] = useState<ModelInfo | null>(null);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>(
    [],
  );

  const { logClientEvent, logServerEvent } = useEvent();

  // Function to check connection status
  const checkConnection = useCallback(async () => {
    try {
      const isConnected = await checkHealth();
      return isConnected;
    } catch {
      return false;
    }
  }, []);

  // Connect to backend
  const connect = useCallback(async () => {
    try {
      setSessionStatus("CONNECTING");
      logClientEvent({ type: "connection_attempt" });

      const isConnected = await checkConnection();
      if (!isConnected) {
        throw new Error("Failed to connect to LM Studio API");
      }

      // Get available models
      const modelsList = await listModels();
      setModels(modelsList);

      // Get chat sessions
      const sessions = await listChatSessions();
      setChatSessions(sessions);

      // Try to get active session
      const activeSession = await getActiveSession();
      if (activeSession) {
        setCurrentSession(activeSession);
        setMessages(activeSession.messages || []);
      }

      setSessionStatus("CONNECTED");
      logClientEvent({
        type: "connection_success",
        modelsCount: modelsList.length,
        sessionsCount: sessions.length,
        hasActiveSession: !!activeSession,
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
  }, [checkConnection, logClientEvent]);

  // Disconnect from backend
  const disconnect = useCallback(() => {
    setSessionStatus("DISCONNECTED");
    setCurrentSession(null);
    setMessages([]);
    logClientEvent({ type: "disconnect" });
  }, [logClientEvent]);

  // Create a new chat session
  const createNewChatSession = useCallback(
    async (name?: string) => {
      if (sessionStatus !== "CONNECTED") {
        return null;
      }

      try {
        const newSession = await createChatSession(
          name || `Session ${new Date().toLocaleTimeString()}`,
        );

        // Update sessions list
        setChatSessions((prev) => [newSession, ...prev]);

        // Set as current session
        setCurrentSession(newSession);
        setMessages([]);

        logClientEvent({
          type: "session_created",
          sessionId: newSession.id,
          sessionName: newSession.name,
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
        const session = await getChatSession(sessionId);
        setCurrentSession(session);
        setMessages(session.messages || []);

        logClientEvent({
          type: "session_loaded",
          sessionId: session.id,
          sessionName: session.name,
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
        const success = await deleteChatSession(sessionId);

        if (success) {
          // Update sessions list
          setChatSessions((prev) => prev.filter((s) => s.id !== sessionId));

          // If current session was deleted, clear it
          if (currentSession?.id === sessionId) {
            setCurrentSession(null);
            setMessages([]);
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
    [sessionStatus, currentSession, logClientEvent],
  );

  // Refresh the list of sessions
  const refreshSessions = useCallback(async () => {
    if (sessionStatus !== "CONNECTED") {
      return;
    }

    try {
      const sessions = await listChatSessions();
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
    async (content: string) => {
      if (sessionStatus !== "CONNECTED" || !content.trim()) {
        return "";
      }

      const messageId = uuidv4();

      try {
        logClientEvent({
          type: "message_send",
          event_id: messageId,
          role: "user",
          contentLength: content.length,
        });

        // Add user message to local state
        const userMessage = { role: "user", content };
        setMessages((prev) => [...prev, userMessage]);

        // Send to API
        const response = await sendMessage({
          role: "user",
          content,
          temperature: 0.7,
          max_tokens: 512,
          stream: false,
        });

        // Add assistant response to local state
        const assistantMessage = { role: "assistant", content: response.text };
        setMessages((prev) => [...prev, assistantMessage]);

        logServerEvent({
          type: "message_response",
          event_id: messageId,
          role: "assistant",
          contentLength: response.text.length,
        });

        return response.text;
      } catch (error) {
        console.error("Error sending message:", error);
        logClientEvent({
          type: "message_error",
          event_id: messageId,
          error: error instanceof Error ? error.message : String(error),
        });
        return "";
      }
    },
    [sessionStatus, logClientEvent, logServerEvent],
  );

  // Load chat session from cookies
  useEffect(() => {
    let isMounted = true;

    if (sessionStatus === "CONNECTED" && !currentSession) {
      // Get the last active session ID from cookie
      const savedSettings = getObjectCookie<{
        activeSessionId: string | null;
      }>("lmStudioSettings", {
        activeSessionId: null,
      });

      if (savedSettings.activeSessionId) {
        getChatSession(savedSettings.activeSessionId)
          .then((session) => {
            if (isMounted) {
              setCurrentSession(session);
              setMessages(session.messages || []);
              logClientEvent({
                type: "session_restored_from_cookie",
                sessionId: session.id,
              });
            }
          })
          .catch(() => {
            // Session might have been deleted or invalid
            console.log("Could not restore saved session, creating a new one");
          });
      }
    }

    return () => {
      isMounted = false;
    };
  }, [sessionStatus, currentSession, logClientEvent]);

  // Save current session to cookies
  useEffect(() => {
    if (currentSession && typeof window !== "undefined") {
      // Debounce the cookie setting with a short timeout
      const timeoutId = setTimeout(() => {
        setObjectCookie("lmStudioSettings", {
          activeSessionId: currentSession.id,
        });
      }, 300);

      return () => {
        clearTimeout(timeoutId);
      };
    }
  }, [currentSession]);

  // Initialize periodic connection checking
  useEffect(() => {
    let intervalId: NodeJS.Timeout | undefined;
    let isMounted = true;

    if (sessionStatus === "CONNECTED") {
      // Initial delay before starting interval checks
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
              console.warn("Lost connection to LM Studio API");
              setSessionStatus("DISCONNECTED");
              logClientEvent({ type: "connection_lost" });
            }
          } catch (error) {
            console.error("Error checking connection:", error);
          }
        }, 60000); // Check every minute instead of 30 seconds
      }, 5000); // Wait 5 seconds before first check

      return () => {
        isMounted = false;
        if (timeoutId) clearTimeout(timeoutId);
        if (intervalId) clearInterval(intervalId);
      };
    }

    return () => {
      isMounted = false;
    };
  }, [sessionStatus, checkConnection, logClientEvent]);

  return (
    <LMStudioContext.Provider
      value={{
        sessionStatus,
        currentSession,
        chatSessions,
        models,
        loadedModel,
        messages,
        connect,
        disconnect,
        sendUserMessage,
        deleteChatSessionById,
        loadChatSession,
        createNewChatSession,
        refreshSessions,
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
