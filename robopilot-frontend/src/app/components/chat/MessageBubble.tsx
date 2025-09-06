import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChevronDownIcon, ChevronRightIcon } from "@heroicons/react/24/outline";
import { EnhancedMessage, parseMessageContent } from "@/app/api/agent";
import TTSButton from "@/app/components/TTSButton";

interface MessageBubbleProps {
  message: EnhancedMessage;
  index: number;
  isTTSPlaying?: boolean;
  isStreaming?: boolean;
  onPlayTTS?: (text: string, messageId: string) => void;
  onStopTTS?: () => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  index,
  isTTSPlaying = false,
  isStreaming = false,
  onPlayTTS,
  onStopTTS,
}) => {
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const isUser = message.role === "user";

  // Parse the message content to extract thinking section
  const parsedContent = parseMessageContent(message.content);
  const pseudoId = `session-message-${index}`;

  const handleTTSPlay = (text: string, messageId: string) => {
    onPlayTTS?.(text, messageId);
  };

  const handleTTSStop = () => {
    onStopTTS?.();
  };

  return (
    <div
      className={`group w-full py-4 sm:py-6 px-2 sm:px-4 ${!isUser ? "bg-gray-50" : "bg-white"}`}
    >
      <div className="max-w-4xl mx-auto flex gap-3 sm:gap-4">
        {/* Avatar */}
        {!isUser && (
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0 mt-1">
            <svg
              className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}

        {isUser && (
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0 mt-1">
            <svg
              className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Role Label */}
          <div className="text-base sm:text-sm font-semibold text-gray-900 mb-2 sm:mb-2">
            {isUser ? "You" : "Assistant"}
          </div>

          {/* Thinking Section (only for assistant messages) */}
          {!isUser && parsedContent.thinking && (
            <div className="mb-4 bg-gray-50 border border-gray-200 rounded-lg sm:rounded-lg overflow-hidden">
              <button
                onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                className="w-full flex items-center justify-between p-4 sm:p-3 text-left hover:bg-gray-100 active:bg-gray-100 transition-colors duration-150 touch-manipulation"
              >
                <div className="flex items-center gap-3 sm:gap-2">
                  <div className="w-6 h-6 sm:w-5 sm:h-5 rounded bg-amber-100 flex items-center justify-center">
                    <svg
                      className="w-3.5 h-3.5 sm:w-3 sm:h-3 text-amber-600"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </div>
                  <span className="text-base sm:text-sm font-medium text-gray-700">
                    AI Thinking Process
                  </span>
                  <span className="text-sm sm:text-xs text-gray-500 bg-gray-200 px-2 py-1 sm:px-2 sm:py-0.5 rounded-full">
                    {parsedContent.thinking.split(" ").length} words
                  </span>
                </div>
                <div className="flex items-center">
                  {isThinkingExpanded ? (
                    <ChevronDownIcon className="w-5 h-5 sm:w-4 sm:h-4 text-gray-500" />
                  ) : (
                    <ChevronRightIcon className="w-5 h-5 sm:w-4 sm:h-4 text-gray-500" />
                  )}
                </div>
              </button>

              {isThinkingExpanded && (
                <div className="px-4 sm:px-3 pb-4 sm:pb-3">
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 sm:p-3">
                    <div className="text-base sm:text-sm text-amber-800 leading-relaxed">
                      <div className="font-mono whitespace-pre-wrap mb-3 sm:mb-2 text-sm sm:text-xs text-amber-600">
                        {/* AI's internal reasoning process */}
                      </div>
                      <div className="whitespace-pre-wrap font-mono text-sm sm:text-xs">
                        {parsedContent.thinking}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Message Content */}
          <div className="relative">
            {/* TTS Button - positioned for assistant messages */}
            {!isUser && onPlayTTS && onStopTTS && (
              <div className="absolute -top-1 right-0 opacity-0 sm:group-hover:opacity-100 transition-opacity duration-200">
                <TTSButton
                  messageId={pseudoId}
                  text={parsedContent.response}
                  isPlaying={isTTSPlaying}
                  onPlay={handleTTSPlay}
                  onStop={handleTTSStop}
                  size="sm"
                />
              </div>
            )}

            {/* Message text */}
            <div className="prose prose-gray max-w-none leading-relaxed text-base sm:text-base">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="mb-4 last:mb-0 leading-7 text-base">
                      {children}
                    </p>
                  ),
                  code: ({ children }) => (
                    <code className="px-2 py-1 sm:px-1.5 sm:py-0.5 rounded bg-gray-100 text-gray-800 text-sm font-mono">
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="p-4 rounded-lg text-sm font-mono overflow-x-auto bg-gray-100 text-gray-800 border my-4 touch-manipulation">
                      {children}
                    </pre>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-6 sm:ml-6 space-y-2 my-4">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-6 sm:ml-6 space-y-2 my-4">
                      {children}
                    </ol>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
                      {children}
                    </blockquote>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold mt-6 mb-4">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-bold mt-5 mb-3">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-md font-bold mt-4 mb-2">{children}</h3>
                  ),
                }}
              >
                {parsedContent.response || "Processing..."}
              </ReactMarkdown>
            </div>

            {/* TTS Playing Indicator */}
            {isTTSPlaying && (
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-blue-200 bg-blue-50 rounded px-4 sm:px-3 py-3 sm:py-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span className="text-sm sm:text-xs text-blue-600 font-medium">
                  Speaking...
                </span>
              </div>
            )}

            {/* Streaming Indicator */}
            {isStreaming && !isUser && (
              <div className="flex items-center gap-2 mt-4">
                <div className="flex gap-1">
                  <div
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
                <span className="text-sm sm:text-xs text-gray-500">
                  Assistant is typing...
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
