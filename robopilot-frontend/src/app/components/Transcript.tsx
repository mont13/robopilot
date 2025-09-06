"use client";

import { useLMStudio } from "@/app/contexts/LMStudioContext";
import { useTranscript } from "@/app/contexts/TranscriptContext";
import { useAudio } from "@/app/contexts/AudioContext";
import { TranscriptItem } from "@/app/types";

import { useCallback, useEffect, useRef, useState } from "react";
import AudioControls from "./AudioControls";
import MessageBubble from "./chat/MessageBubble";
import WelcomeScreen from "./WelcomeScreen";

export interface TranscriptProps {
  mode: "chat" | "voice";
  userText: string;
  setUserText: (val: string) => void;
  onSendMessage: () => void;
  canSend: boolean;
  ttsPlayingMessageId: string | null;
  isRecording: boolean;
  isProcessingVoice: boolean;
  onToggleRecording: () => void;
  vadEnabled?: boolean;
  onCreateNewSession?: () => void;
}

function Transcript({
  mode,
  userText,
  setUserText,
  onSendMessage,
  canSend,
  ttsPlayingMessageId,
  isRecording,
  isProcessingVoice,
  onToggleRecording,
  vadEnabled = false,
  onCreateNewSession,
}: TranscriptProps) {
  const { transcriptItems } = useTranscript();
  const { currentSession, messages, isStreaming } = useLMStudio();
  const { playTextToSpeech, stopTextToSpeech } = useAudio();
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const [prevLogs, setPrevLogs] = useState<TranscriptItem[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const scrollToBottom = useCallback(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcriptRef]);

  useEffect(() => {
    const hasNewMessage = transcriptItems.length > prevLogs.length;
    const hasUpdatedMessage = transcriptItems.some((newItem, index) => {
      const oldItem = prevLogs[index];
      return (
        oldItem &&
        (newItem.title !== oldItem.title || newItem.data !== oldItem.data)
      );
    });

    if (hasNewMessage || hasUpdatedMessage) {
      scrollToBottom();
    }

    setPrevLogs(transcriptItems);
  }, [transcriptItems, messages]);

  // Autofocus on text box input on load for chat mode
  useEffect(() => {
    if (mode === "chat" && canSend && inputRef.current) {
      inputRef.current.focus();
    }
  }, [canSend, mode]);

  return (
    <div className="flex flex-col flex-1 bg-white min-h-0 rounded-lg sm:shadow-sm sm:border sm:border-gray-200 overflow-hidden">
      <div className="relative flex-1 min-h-0">
        <div
          ref={transcriptRef}
          className="overflow-auto flex flex-col h-full scrollbar-thin px-2 sm:px-0"
        >
          {currentSession ? (
            // If we have a session, display its messages
            messages
              .filter((message) => message.role !== "system") // Filter out system messages
              .map((message, index) => {
                // We create a pseudo itemId for TTS detection
                const pseudoId = `session-message-${index}`;

                // Check if this message is currently having TTS played
                const isTTSPlaying = ttsPlayingMessageId === pseudoId;

                // Only the last assistant message should show streaming state
                const isLastAssistantMessage =
                  message.role === "assistant" && index === messages.length - 1;

                return (
                  <MessageBubble
                    key={`session-${index}`}
                    message={message}
                    index={index}
                    isTTSPlaying={isTTSPlaying}
                    isStreaming={isStreaming && isLastAssistantMessage}
                    onPlayTTS={playTextToSpeech}
                    onStopTTS={stopTextToSpeech}
                  />
                );
              })
          ) : (
            // If no session, show welcome screen
            <WelcomeScreen
              onCreateNewChat={onCreateNewSession || (() => {})}
              userText={userText}
              setUserText={setUserText}
              onSendMessage={onSendMessage}
              canSend={canSend}
            />
          )}
        </div>
      </div>

      {currentSession && (
        <div className="p-3 sm:p-4 md:p-6 flex items-center gap-x-3 shrink-0 border-t border-gray-200 bg-white safe-area-bottom">
          {mode === "chat" ? (
            <div className="flex items-center gap-3 w-full max-w-4xl mx-auto">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={userText}
                  onChange={(e) => setUserText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && canSend) {
                      onSendMessage();
                    }
                  }}
                  className="w-full px-4 py-4 sm:py-3 pr-14 sm:pr-12 rounded-xl sm:rounded-xl border border-gray-300 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-colors text-base sm:text-sm placeholder-gray-500 bg-white shadow-sm touch-manipulation"
                  placeholder="Message RoboPilot..."
                  disabled={!canSend}
                />
                <button
                  onClick={onSendMessage}
                  disabled={!canSend || !userText.trim()}
                  className="absolute right-2 sm:right-2 top-1/2 transform -translate-y-1/2 p-3 sm:p-2 text-gray-500 hover:text-gray-700 disabled:text-gray-300 disabled:cursor-not-allowed transition-colors touch-manipulation"
                >
                  <svg
                    className="w-6 h-6 sm:w-5 sm:h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                  </svg>
                </button>
              </div>
            </div>
          ) : (
            <div className="w-full flex justify-center max-w-4xl mx-auto">
              <AudioControls
                isRecording={isRecording}
                isProcessing={isProcessingVoice}
                onToggleRecording={onToggleRecording}
                disabled={!canSend}
                isVadActive={
                  vadEnabled &&
                  !isRecording &&
                  !isProcessingVoice &&
                  !ttsPlayingMessageId
                }
                className="mx-auto"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Transcript;
