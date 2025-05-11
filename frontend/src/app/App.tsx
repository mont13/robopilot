"use client";

import React, { useEffect, useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

// Context providers & hooks
import { useAudio } from "@/app/contexts/AudioContext";
import { useEvent } from "@/app/contexts/EventContext";
import { useLMStudio } from "@/app/contexts/LMStudioContext";
import { useTranscript } from "@/app/contexts/TranscriptContext";

// Components
import AudioSettings from "./components/AudioSettings";
import BottomToolbar from "./components/BottomToolbar";
import ModelSelection from "./components/chat/ModelSelection";
import SessionList from "./components/chat/SessionList";
import ModeSelection from "./components/ModeSelection";
import Transcript from "./components/Transcript";

function AppContent() {
  const { addTranscriptMessage, updateTranscriptItemStatus } = useTranscript();

  const { logClientEvent } = useEvent();

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
    models,
    loadedModel,
    currentSession,
    loadChatSession,
    deleteChatSessionById,
    createNewChatSession,
  } = useLMStudio();

  // Interaction mode state
  const [interactionMode, setInteractionMode] = useState<
    "chat" | "voice" | null
  >(null);

  // UI state
  const [userText, setUserText] = useState<string>("");
  const [showAudioSettings, setShowAudioSettings] = useState<boolean>(false);
  const [showSessions, setShowSessions] = useState<boolean>(false);
  const [isAudioEnabled, setIsAudioEnabled] = useState<boolean>(true);
  const [isMobile, setIsMobile] = useState<boolean>(false);

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
      startRecording();
    }
  }, [
    sessionStatus,
    isRecording,
    stopRecording,
    stopTextToSpeech,
    startRecording,
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

  // Toggle sessions panel
  const toggleSessions = useCallback(() => {
    setShowSessions((prev) => !prev);
  }, []);

  // Check if we're on mobile and load saved settings from local storage
  useEffect(() => {
    let isMounted = true;

    if (typeof window !== "undefined") {
      // Load interaction mode from localStorage
      const savedMode = localStorage.getItem("interactionMode");
      if ((savedMode === "chat" || savedMode === "voice") && isMounted) {
        setInteractionMode(savedMode);
      }

      // Load audio enabled setting
      const savedAudioEnabled = localStorage.getItem("audioEnabled");
      if (savedAudioEnabled !== null && isMounted) {
        setIsAudioEnabled(savedAudioEnabled === "true");
      }

      // Check for mobile device
      const checkMobile = () => {
        if (isMounted) {
          setIsMobile(window.innerWidth < 768);
        }
      };

      checkMobile();
      window.addEventListener("resize", checkMobile);

      return () => {
        isMounted = false;
        window.removeEventListener("resize", checkMobile);
      };
    }
  }, []);

  // Handle sessions panel on mobile
  useEffect(() => {
    // Don't auto-close sessions panel when initially connected
    if (isMobile && showSessions && sessionStatus === "CONNECTED") {
      // We don't want to auto-hide just because we're connected
      // Only hide if the user explicitly selects a session
    }

    return () => {};
  }, [isMobile, showSessions, sessionStatus]);

  // Function to handle session selection
  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await loadChatSession(sessionId);

      // Only auto-hide on mobile when explicitly selecting a session
      if (isMobile && window.innerWidth < 768) {
        // Add a slight delay to allow the user to see the selection happened
        setTimeout(() => {
          setShowSessions(false);
        }, 500);
      }
    },
    [loadChatSession, isMobile]
  );

  // Function to handle session deletion
  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      if (window.confirm("Are you sure you want to delete this session?")) {
        await deleteChatSessionById(sessionId);
      }
    },
    [deleteChatSessionById]
  );

  // Function to create a new session
  const handleCreateNewSession = useCallback(async () => {
    await createNewChatSession();
  }, [createNewChatSession]);

  // Handle model selection
  const handleModelSelect = useCallback(
    (modelKey: string) => {
      logClientEvent({
        type: "model_selected",
        modelKey,
      });
    },
    [logClientEvent]
  );

  // If mode is not selected yet, show the mode selection screen
  if (interactionMode === null) {
    return (
      <ModeSelection
        onSelectMode={(mode) => {
          setInteractionMode(mode);
          if (typeof window !== "undefined") {
            localStorage.setItem("interactionMode", mode);
          }
        }}
      />
    );
  }

  return (
    <div className="text-base flex flex-col h-screen bg-gray-100 text-gray-800 relative">
      <div className="p-2 md:p-3 text-lg font-semibold flex justify-between items-center shadow-sm">
        <div
          className="flex items-center cursor-pointer"
          onClick={() => window.location.reload()}
        >
          <span className="font-bold text-base md:text-lg">Robotika</span>
        </div>
        <div className="flex items-center space-x-2 md:space-x-3">
          <button
            onClick={() => {
              const newMode = interactionMode === "chat" ? "voice" : "chat";
              setInteractionMode(newMode);
              if (typeof window !== "undefined") {
                localStorage.setItem("interactionMode", newMode);
              }
            }}
            className="text-xs md:text-sm bg-gray-200 hover:bg-gray-300 rounded-full px-2 py-1 flex items-center"
          >
            {interactionMode === "chat" ? "Voice" : "Chat"}
          </button>

          {interactionMode === "chat" && (
            <button
              onClick={toggleSessions}
              className="text-gray-700 hover:text-gray-900 p-1 rounded-full hover:bg-gray-200"
              aria-label="Sessions"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
              </svg>
            </button>
          )}

          <button
            onClick={toggleAudioSettings}
            className="text-gray-700 hover:text-gray-900 p-1 rounded-full hover:bg-gray-200"
            aria-label="Audio Settings"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106a1.532 1.532 0 01-.948 2.287c-1.56.38-1.56 2.6 0 2.98a1.532 1.532 0 01.948 2.286c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.948c.38 1.56 2.6 1.56 2.98 0a1.532 1.532 0 012.286-.948c1.372.836 2.942-.734 2.106-2.106a1.532 1.532 0 01.948-2.287c1.56-.38 1.56-2.6 0-2.98a1.532 1.532 0 01-.948-2.286c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.948zM10 13a3 3 0 100-6 3 3 0 000 6z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {models.length > 0 && (
            <div className="w-32 md:w-48 lg:w-56 hidden sm:block">
              <ModelSelection
                models={models}
                loadedModel={loadedModel}
                onSelectModel={handleModelSelect}
                isLoading={sessionStatus === "CONNECTING"}
              />
            </div>
          )}
        </div>
      </div>

      {showAudioSettings && (
        <AudioSettings
          onClose={() => setShowAudioSettings(false)}
          isVisible={showAudioSettings}
        />
      )}

      <div className="flex flex-1 px-2 sm:px-4 pt-4 overflow-hidden relative">
        {showSessions && interactionMode === "chat" && (
          <div className="w-full sm:w-2/5 md:w-1/3 lg:w-1/4 bg-white rounded-lg mr-0 sm:mr-2 overflow-hidden shadow-lg absolute sm:relative z-10 top-0 left-0 h-full">
            <div className="flex items-center justify-between p-2 sm:hidden bg-gray-100 border-b">
              <h3 className="font-medium">Chat Sessions</h3>
              <button
                onClick={toggleSessions}
                className="text-gray-600 p-1 rounded hover:bg-gray-200"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
            <SessionList
              sessions={chatSessions}
              onSelectSession={handleSelectSession}
              onDeleteSession={handleDeleteSession}
              onCreateNewSession={handleCreateNewSession}
              currentSessionId={currentSession?.id || null}
              className="h-full sm:h-full"
            />
          </div>
        )}
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
        />
      </div>

      <BottomToolbar
        sessionStatus={sessionStatus}
        onToggleConnection={onToggleConnection}
        isAudioEnabled={isAudioEnabled}
        setIsAudioEnabled={(value) => {
          setIsAudioEnabled(value);
          if (typeof window !== "undefined") {
            localStorage.setItem("audioEnabled", String(value));
          }
        }}
      />
    </div>
  );
}

function App() {
  return <AppContent />;
}

export default App;
