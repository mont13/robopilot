"use client";

import { useLMStudio } from "@/app/contexts/LMStudioContext";
import { useTranscript } from "@/app/contexts/TranscriptContext";
import { TranscriptItem } from "@/app/types";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import AudioControls from "./AudioControls";

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
}: TranscriptProps) {
  const { transcriptItems } = useTranscript();
  const { currentSession, messages } = useLMStudio();
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
    <div className="flex flex-col flex-1 bg-white min-h-0 rounded-xl">
      <div className="relative flex-1 min-h-0">
        <div
          ref={transcriptRef}
          className="overflow-auto p-4 pt-12 flex flex-col gap-y-4 h-full"
        >
          {currentSession
            ? // If we have a session, display its messages
              messages
                .filter((message) => message.role !== "system") // Filter out system messages
                .map((message, index) => {
                  const isUser = message.role === "user";
                  const baseContainer = "flex justify-end flex-col";
                  const containerClasses = `${baseContainer} ${
                    isUser ? "items-end" : "items-start"
                  }`;

                  // We create a pseudo itemId for TTS detection
                  const pseudoId = `session-message-${index}`;

                  // Check if this message is currently having TTS played
                  const isTTSPlaying =
                    ttsPlayingMessageId === pseudoId && !isUser;

                  const bubbleBase = `max-w-lg p-3 rounded-xl ${
                    isUser
                      ? "bg-gray-900 text-gray-100"
                      : isTTSPlaying
                        ? "bg-blue-100 text-black border border-blue-300"
                        : "bg-gray-100 text-black"
                  }`;

                  const content = message.content || "";

                  // Format the timestamp from created_at if available
                  const timestamp = message.created_at
                    ? new Date(message.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : new Date().toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      });

                  return (
                    <div key={`session-${index}`} className={containerClasses}>
                      <div className={bubbleBase}>
                        <div
                          className={`text-xs ${
                            isUser ? "text-gray-400" : "text-gray-500"
                          } font-mono`}
                        >
                          {timestamp}
                        </div>
                        <div className="whitespace-pre-wrap">
                          <ReactMarkdown>{content}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  );
                })
            : // If no session, fall back to transcript items
              transcriptItems.map((item) => {
                const {
                  itemId,
                  type,
                  role,
                  timestamp,
                  title = "",
                  isHidden,
                } = item;

                if (isHidden || type !== "MESSAGE") {
                  return null;
                }

                const isUser = role === "user";
                const baseContainer = "flex justify-end flex-col";
                const containerClasses = `${baseContainer} ${
                  isUser ? "items-end" : "items-start"
                }`;

                // Check if this message is currently having TTS played
                const isTTSPlaying = ttsPlayingMessageId === itemId && !isUser;

                // Add a highlight effect for messages being read aloud
                const bubbleBase = `max-w-lg p-3 rounded-xl ${
                  isUser
                    ? "bg-gray-900 text-gray-100"
                    : isTTSPlaying
                      ? "bg-blue-100 text-black border border-blue-300"
                      : "bg-gray-100 text-black"
                }`;

                const isBracketedMessage =
                  title.startsWith("[") && title.endsWith("]");
                const messageStyle = isBracketedMessage
                  ? "italic text-gray-400"
                  : "";
                const displayTitle = isBracketedMessage
                  ? title.slice(1, -1)
                  : title;

                return (
                  <div key={itemId} className={containerClasses}>
                    <div className={bubbleBase}>
                      <div
                        className={`text-xs ${
                          isUser ? "text-gray-400" : "text-gray-500"
                        } font-mono`}
                      >
                        {timestamp}
                      </div>
                      <div className={`whitespace-pre-wrap ${messageStyle}`}>
                        <ReactMarkdown>{displayTitle}</ReactMarkdown>
                      </div>
                    </div>
                  </div>
                );
              })}
        </div>
      </div>

      <div className="p-4 flex items-center gap-x-2 shrink-0 border-t border-gray-200">
        {mode === "chat" ? (
          <>
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
              className="flex-1 px-4 py-2 focus:outline-hidden"
              placeholder="Type a message..."
            />
            <button
              onClick={onSendMessage}
              disabled={!canSend || !userText.trim()}
              className="bg-gray-400 text-white rounded-full px-3 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Image src="/arrow.svg" alt="Send" width={24} height={24} />
            </button>
          </>
        ) : (
          <div className="w-full flex justify-center">
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
    </div>
  );
}

export default Transcript;
