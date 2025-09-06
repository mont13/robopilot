"use client";

import { useCallback, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

// Context providers & hooks
import { useAudio } from "@/app/contexts/AudioContext";
import { useLMStudio } from "@/app/contexts/LMStudioContext";
import { useTranscript } from "@/app/contexts/TranscriptContext";

// Redux hooks
import { useAppDispatch, useAppSelector } from "@/app/lib/hooks";
import {
  setInteractionMode,
  setVadEnabled,
  setIsAudioEnabled,
  setIsMobile,
  selectSettings,
} from "@/app/lib/features/settings/settingsSlice";

// Components
import AudioSettings from "./components/AudioSettings";
import ConnectionSelection from "./components/chat/ConnectionSelection";
import ModeSelection from "./components/ModeSelection";
import Transcript from "./components/Transcript";
import VADProcessor from "./components/VADProcessor";
import ChatLayout from "./components/ChatLayout";
import ChatSidebar from "./components/ChatSidebar";
import SidePanel from "./components/SidePanel";

import ConnectionModal from "./components/modals/ConnectionModal";

function AppContent() {
  const { addTranscriptMessage, updateTranscriptItemStatus } = useTranscript();

  // Access our audio context
  const {
    isRecording,
    isProcessingVoice,
    startRecording,
    stopRecording,
    ttsPlayingMessageId,
    playTextToSpeech,
    stopTextToSpeech,
  } = useAudio();

  // Access LM Studio context
  const {
    sessionStatus,
    connect,
    disconnect,
    sendUserMessage,
    chatSessions,
    currentSession,
    connections,
    activeConnection,
    loadChatSession,
    deleteChatSessionById,
    createNewChatSession,
    activateConnectionById,
  } = useLMStudio();

  // Redux state
  const dispatch = useAppDispatch();
  const settings = useAppSelector(selectSettings);
  const { interactionMode, isAudioEnabled, isMobile, vadEnabled } = settings;

  // Local UI state (not persisted)
  const [userText, setUserText] = useState<string>("");
  const [showAudioSettings, setShowAudioSettings] = useState<boolean>(false);
  const [showConnections, setShowConnections] = useState<boolean>(false);
  const [isConnectionLoading, setIsConnectionLoading] =
    useState<boolean>(false);
  const [isConnectionModalOpen, setIsConnectionModalOpen] =
    useState<boolean>(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);

  // Handle sending typed text message
  const handleSendTextMessage = useCallback(async () => {
    if (!userText.trim() || sessionStatus !== "CONNECTED") {
      return;
    }

    // Stop any ongoing speech
    stopTextToSpeech();

    // Add message to transcript
    const id = uuidv4();
    addTranscriptMessage(id, "user", userText, false);
    updateTranscriptItemStatus(id, "DONE");

    // Save the text to send before clearing the input
    const textToSend = userText.trim();
    setUserText("");

    // Send text to LM Studio
    try {
      const response = await sendUserMessage(textToSend);

      if (response) {
        // Add the response to transcript
        const responseId = uuidv4();
        addTranscriptMessage(responseId, "assistant", response, false);
        updateTranscriptItemStatus(responseId, "DONE");

        // Use TTS to convert text to speech if in voice mode
        if (interactionMode === "voice" && isAudioEnabled) {
          await playTextToSpeech(response, responseId);
        }
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Unknown error sending message";
      console.error("Error sending message:", errorMessage);

      // Add error message to transcript
      const errorId = uuidv4();
      addTranscriptMessage(errorId, "assistant", `Error: ${errorMessage}`);
      updateTranscriptItemStatus(errorId, "DONE");
    }
  }, [
    userText,
    sessionStatus,
    stopTextToSpeech,
    addTranscriptMessage,
    updateTranscriptItemStatus,
    sendUserMessage,
    interactionMode,
    isAudioEnabled,
    playTextToSpeech,
  ]);

  // Handle toggle recording
  const handleToggleRecording = useCallback(async () => {
    if (sessionStatus !== "CONNECTED") return;

    if (isRecording) {
      await stopRecording();

      // The audio context will handle the transcript update and
      // send the transcribed text to the LM Studio API
    } else {
      // Stop any ongoing speech
      stopTextToSpeech();
      // If VAD is enabled, disable it temporarily to avoid conflicts
      if (vadEnabled) {
        dispatch(setVadEnabled(false));
        // Re-enable VAD after recording is complete
        setTimeout(() => dispatch(setVadEnabled(true)), 1000);
      }
      startRecording();
    }
  }, [
    sessionStatus,
    isRecording,
    stopRecording,
    stopTextToSpeech,
    startRecording,
    vadEnabled,
    dispatch,
  ]);

  const onToggleConnection = useCallback(() => {
    if (sessionStatus === "CONNECTED" || sessionStatus === "CONNECTING") {
      disconnect();
      // Clear transcript when disconnecting
      if (isRecording) {
        stopRecording();
      }
      stopTextToSpeech();
    } else {
      connect();
    }
  }, [
    sessionStatus,
    disconnect,
    isRecording,
    stopRecording,
    stopTextToSpeech,
    connect,
  ]);

  // Toggle audio settings panel
  const toggleAudioSettings = useCallback(() => {
    setShowAudioSettings((prev) => !prev);
  }, []);

  // Toggle connections panel
  const toggleConnections = useCallback(() => {
    setShowConnections((prev) => !prev);
  }, []);

  // Function to open the connection modal
  const handleCreateNewConnection = useCallback(() => {
    setIsConnectionModalOpen(true);
  }, []);

  // Function to handle when a new connection is created
  const handleConnectionCreated = useCallback(() => {
    // Refresh the connections list
    connect();
  }, [connect]);

  // Handle connection selection
  const handleSelectConnection = useCallback(
    async (connectionId: string) => {
      if (connectionId && sessionStatus === "CONNECTED") {
        setIsConnectionLoading(true);
        try {
          await activateConnectionById(connectionId);
        } finally {
          setIsConnectionLoading(false);
          // Close connections panel on mobile
          if (isMobile) {
            setShowConnections(false);
          }
        }
      }
    },
    [activateConnectionById, sessionStatus, isMobile],
  );

  // Check for mobile device
  useEffect(() => {
    let isMounted = true;

    if (typeof window !== "undefined") {
      const checkMobile = () => {
        if (isMounted) {
          const mobile = window.innerWidth < 768;
          dispatch(setIsMobile(mobile));
        }
      };

      checkMobile();
      window.addEventListener("resize", checkMobile);

      return () => {
        isMounted = false;
        window.removeEventListener("resize", checkMobile);
      };
    }
  }, [dispatch]);

  // Function to handle session selection
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await loadChatSession(sessionId);
    },
    [loadChatSession],
  );

  // Function to handle session deletion
  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      if (window.confirm("Are you sure you want to delete this session?")) {
        await deleteChatSessionById(sessionId);
      }
    },
    [deleteChatSessionById],
  );

  // Function to create a new session
  const handleCreateNewSession = useCallback(async () => {
    await createNewChatSession();
  }, [createNewChatSession]);

  // If mode is not selected yet, show the mode selection screen
  if (interactionMode === null) {
    return (
      <ModeSelection
        onSelectMode={(mode) => {
          dispatch(setInteractionMode(mode));
        }}
      />
    );
  }

  return (
    <ChatLayout
      sidebar={
        <ChatSidebar
          sessions={chatSessions}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onCreateNewSession={handleCreateNewSession}
          currentSessionId={currentSession?.session_id || null}
          isCollapsed={isSidebarCollapsed}
        />
      }
      onSidebarToggle={setIsSidebarCollapsed}
    >
      {/* Audio Settings Modal */}
      {showAudioSettings && (
        <AudioSettings
          onClose={() => setShowAudioSettings(false)}
          isVisible={showAudioSettings}
        />
      )}

      {/* Connections Panel (only show when needed) */}
      <SidePanel
        isOpen={showConnections}
        onClose={() => setShowConnections(false)}
        title="LLM Connections"
        width="md"
      >
        <div className="p-4 h-full overflow-auto scrollbar-thin">
          <ConnectionSelection
            connections={connections}
            activeConnection={activeConnection}
            onSelectConnection={handleSelectConnection}
            onCreateConnection={handleCreateNewConnection}
            isLoading={isConnectionLoading}
          />
        </div>
      </SidePanel>

      {/* Header Controls Bar */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200 mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              const newMode = interactionMode === "chat" ? "voice" : "chat";
              dispatch(setInteractionMode(newMode));
              const newVadState = newMode === "voice";
              dispatch(setVadEnabled(newVadState));
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              interactionMode === "chat"
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => {
              const newMode = interactionMode === "chat" ? "voice" : "chat";
              dispatch(setInteractionMode(newMode));
              const newVadState = newMode === "voice";
              dispatch(setVadEnabled(newVadState));
            }}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              interactionMode === "voice"
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            🎤 Voice
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              sessionStatus === "CONNECTED"
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                sessionStatus === "CONNECTED" ? "bg-green-500" : "bg-red-500"
              }`}
            />
            {sessionStatus}
          </div>

          <button
            onClick={onToggleConnection}
            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
              sessionStatus === "CONNECTED"
                ? "bg-red-100 text-red-700 hover:bg-red-200"
                : "bg-green-100 text-green-700 hover:bg-green-200"
            }`}
          >
            {sessionStatus === "CONNECTED" ? "Disconnect" : "Connect"}
          </button>

          <button
            onClick={toggleConnections}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Connections"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
          </button>

          <button
            onClick={toggleAudioSettings}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Settings"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <Transcript
        mode={interactionMode}
        userText={userText}
        setUserText={setUserText}
        onSendMessage={handleSendTextMessage}
        canSend={sessionStatus === "CONNECTED" && !isProcessingVoice}
        ttsPlayingMessageId={ttsPlayingMessageId}
        isRecording={isRecording}
        isProcessingVoice={isProcessingVoice}
        onToggleRecording={handleToggleRecording}
        vadEnabled={vadEnabled}
        onCreateNewSession={handleCreateNewSession}
      />

      {/* Voice Activity Detection for voice mode */}
      {interactionMode === "voice" &&
        sessionStatus === "CONNECTED" &&
        isAudioEnabled && (
          <VADProcessor
            isEnabled={
              vadEnabled &&
              sessionStatus === "CONNECTED" &&
              isAudioEnabled &&
              !isRecording
            }
            onVoiceProcessing={(processing) => {
              if (processing && ttsPlayingMessageId) {
                stopTextToSpeech();
              }
            }}
          />
        )}

      {/* Connection Modal */}
      <ConnectionModal
        isOpen={isConnectionModalOpen}
        onClose={() => setIsConnectionModalOpen(false)}
        onConnectionCreated={handleConnectionCreated}
      />
    </ChatLayout>
  );
}

function App() {
  return <AppContent />;
}

export default App;
