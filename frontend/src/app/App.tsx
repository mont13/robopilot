"use client";

import { useCallback, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

// Context providers & hooks
import { useAudio } from "@/app/contexts/AudioContext";
import { useLMStudio } from "@/app/contexts/LMStudioContext";
import { useTranscript } from "@/app/contexts/TranscriptContext";

// Components
import AudioSettings from "./components/AudioSettings";
import BottomToolbar from "./components/BottomToolbar";
import SessionList from "./components/chat/SessionList";
import ModeSelection from "./components/ModeSelection";
import Transcript from "./components/Transcript";
import VADProcessor from "./components/VADProcessor";

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
  const [vadEnabled, setVadEnabled] = useState<boolean>(false);

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
        setVadEnabled(false);
        // Re-enable VAD after recording is complete
        setTimeout(() => setVadEnabled(true), 1000);
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
      // Load interaction mode from sessionStorage
      const savedMode = sessionStorage.getItem("interactionMode");
      if ((savedMode === "chat" || savedMode === "voice") && isMounted) {
        setInteractionMode(savedMode);
        // If voice mode and VAD was previously enabled, enable VAD
        if (savedMode === "voice") {
          const vadSetting = localStorage.getItem("vadEnabled");
          setVadEnabled(vadSetting === null ? true : vadSetting === "true");
        }
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
    [loadChatSession, isMobile],
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
          setInteractionMode(mode);
          if (typeof window !== "undefined") {
            sessionStorage.setItem("interactionMode", mode);
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
          onClick={() => {
            setInteractionMode(null);
            sessionStorage.removeItem("interactionMode");
          }}
        >
          <span className="font-bold text-base md:text-lg">Robotika</span>
        </div>
        <div className="flex items-center justify-end space-x-2 md:space-x-3">
          <button
            onClick={() => {
              const newMode = interactionMode === "chat" ? "voice" : "chat";
              setInteractionMode(newMode);
              // Toggle VAD when switching modes
              const newVadState = newMode === "voice";
              setVadEnabled(newVadState);
              if (typeof window !== "undefined") {
                localStorage.setItem("vadEnabled", String(newVadState));
              }
              if (typeof window !== "undefined") {
                sessionStorage.setItem("interactionMode", newMode);
              }
            }}
            className="text-xs md:text-sm bg-gray-200 hover:bg-gray-300 rounded-full px-2 py-1 flex items-center"
          >
            {interactionMode === "chat" ? "Voice" : "Chat"}
          </button>

          {(interactionMode === "chat" || interactionMode === "voice") && (
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
              viewBox="0 0 54 54"
              fill="currentColor"
            >
              <path d="M51.22,21h-5.052c-0.812,0-1.481-0.447-1.792-1.197s-0.153-1.54,0.42-2.114l3.572-3.571 c0.525-0.525,0.814-1.224,0.814-1.966c0-0.743-0.289-1.441-0.814-1.967l-4.553-4.553c-1.05-1.05-2.881-1.052-3.933,0l-3.571,3.571 c-0.574,0.573-1.366,0.733-2.114,0.421C33.447,9.313,33,8.644,33,7.832V2.78C33,1.247,31.753,0,30.22,0H23.78 C22.247,0,21,1.247,21,2.78v5.052c0,0.812-0.447,1.481-1.197,1.792c-0.748,0.313-1.54,0.152-2.114-0.421l-3.571-3.571 c-1.052-1.052-2.883-1.05-3.933,0l-4.553,4.553c-0.525,0.525-0.814,1.224-0.814,1.967c0,0.742,0.289,1.44,0.814,1.966l3.572,3.571 c0.573,0.574,0.73,1.364,0.42,2.114S8.644,21,7.832,21H2.78C1.247,21,0,22.247,0,23.78v6.439C0,31.753,1.247,33,2.78,33h5.052 c0.812,0,1.481,0.447,1.792,1.197s0.153,1.54-0.42,2.114l-3.572,3.571c-0.525,0.525-0.814,1.224-0.814,1.966 c0,0.743,0.289,1.441,0.814,1.967l4.553,4.553c1.051,1.051,2.881,1.053,3.933,0l3.571-3.572c0.574-0.573,1.363-0.731,2.114-0.42 c0.75,0.311,1.197,0.98,1.197,1.792v5.052c0,1.533,1.247,2.78,2.78,2.78h6.439c1.533,0,2.78-1.247,2.78-2.78v-5.052 c0-0.812,0.447-1.481,1.197-1.792c0.751-0.312,1.54-0.153,2.114,0.42l3.571,3.572c1.052,1.052,2.883,1.05,3.933,0l4.553-4.553 c0.525-0.525,0.814-1.224,0.814-1.967c0-0.742-0.289-1.44-0.814-1.966l-3.572-3.571c-0.573-0.574-0.73-1.364-0.42-2.114 S45.356,33,46.168,33h5.052c1.533,0,2.78-1.247,2.78-2.78V23.78C54,22.247,52.753,21,51.22,21z M52,30.22 C52,30.65,51.65,31,51.22,31h-5.052c-1.624,0-3.019,0.932-3.64,2.432c-0.622,1.5-0.295,3.146,0.854,4.294l3.572,3.571 c0.305,0.305,0.305,0.8,0,1.104l-4.553,4.553c-0.304,0.304-0.799,0.306-1.104,0l-3.571-3.572c-1.149-1.149-2.794-1.474-4.294-0.854 c-1.5,0.621-2.432,2.016-2.432,3.64v5.052C31,51.65,30.65,52,30.22,52H23.78C23.35,52,23,51.65,23,51.22v-5.052 c0-1.624-0.932-3.019-2.432-3.64c-0.503-0.209-1.021-0.311-1.533-0.311c-1.014,0-1.997,0.4-2.761,1.164l-3.571,3.572 c-0.306,0.306-0.801,0.304-1.104,0l-4.553-4.553c-0.305-0.305-0.305-0.8,0-1.104l3.572-3.571c1.148-1.148,1.476-2.794,0.854-4.294 C10.851,31.932,9.456,31,7.832,31H2.78C2.35,31,2,30.65,2,30.22V23.78C2,23.35,2.35,23,2.78,23h5.052 c1.624,0,3.019-0.932,3.64-2.432c0.622-1.5,0.295-3.146-0.854-4.294l-3.572-3.571c-0.305-0.305-0.305-0.8,0-1.104l4.553-4.553 c0.304-0.305,0.799-0.305,1.104,0l3.571,3.571c1.147,1.147,2.792,1.476,4.294,0.854C22.068,10.851,23,9.456,23,7.832V2.78 C23,2.35,23.35,2,23.78,2h6.439C30.65,2,31,2.35,31,2.78v5.052c0,1.624,0.932,3.019,2.432,3.64 c1.502,0.622,3.146,0.294,4.294-0.854l3.571-3.571c0.306-0.305,0.801-0.305,1.104,0l4.553,4.553c0.305,0.305,0.305,0.8,0,1.104 l-3.572,3.571c-1.148,1.148-1.476,2.794-0.854,4.294c0.621,1.5,2.016,2.432,3.64,2.432h5.052C51.65,23,52,23.35,52,23.78V30.22z" />
              <path d="M27,18c-4.963,0-9,4.037-9,9s4.037,9,9,9s9-4.037,9-9S31.963,18,27,18z M27,34c-3.859,0-7-3.141-7-7s3.141-7,7-7 s7,3.141,7,7S30.859,34,27,34z" />
            </svg>
          </button>
        </div>
      </div>

      {showAudioSettings && (
        <AudioSettings
          onClose={() => setShowAudioSettings(false)}
          isVisible={showAudioSettings}
        />
      )}

      <div className="flex flex-1 px-2 sm:px-4 pt-4 overflow-hidden relative">
        {showSessions && (interactionMode === "chat" || interactionMode === "voice") && (
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
          vadEnabled={vadEnabled}
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
                !isRecording &&
                !ttsPlayingMessageId
              }
            />
          )}
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
        vadEnabled={interactionMode === "voice" ? vadEnabled : undefined}
        setVadEnabled={interactionMode === "voice" ? setVadEnabled : undefined}
      />
    </div>
  );
}

function App() {
  return <AppContent />;
}

export default App;
