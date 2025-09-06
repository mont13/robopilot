"use client";

import React from "react";

interface WelcomeScreenProps {
  onCreateNewChat: () => void;
  userText?: string;
  setUserText?: (text: string) => void;
  onSendMessage?: () => void;
  canSend?: boolean;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onCreateNewChat,
  userText = "",
  setUserText,
  onSendMessage,
  canSend = false,
}) => {
  const suggestions = [
    {
      icon: "💡",
      title: "Generate Ideas",
      description: "Help me brainstorm creative solutions for a project",
    },
    {
      icon: "📝",
      title: "Write Content",
      description: "Draft an email, essay, or creative writing piece",
    },
    {
      icon: "🔍",
      title: "Analyze & Research",
      description: "Explain complex topics or analyze information",
    },
    {
      icon: "💻",
      title: "Code & Debug",
      description: "Help with programming tasks and troubleshooting",
    },
  ];

  return (
    <div className="flex-1 flex flex-col justify-center p-4 sm:p-6">
      <div className="max-w-3xl w-full text-center mx-auto">
        {/* Main Logo/Title */}
        <div className="mb-6 sm:mb-8">
          <div className="w-20 h-20 sm:w-16 sm:h-16 bg-gray-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-10 h-10 sm:w-8 sm:h-8 text-white"
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
          <h1 className="text-2xl sm:text-3xl font-semibold text-gray-900 mb-3 sm:mb-2">
            How can I help you today?
          </h1>
          <p className="text-gray-600 text-base sm:text-lg px-4 sm:px-0">
            Start a conversation or try one of these suggestions
          </p>
        </div>

        {/* Suggestion Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={onCreateNewChat}
              className="p-4 sm:p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-sm active:bg-gray-50 transition-all duration-200 text-left group touch-manipulation"
            >
              <div className="flex items-start gap-4 sm:gap-3">
                <div className="text-3xl sm:text-2xl flex-shrink-0 mt-1">
                  {suggestion.icon}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2 sm:mb-1 group-hover:text-gray-700 text-base sm:text-base">
                    {suggestion.title}
                  </h3>
                  <p className="text-base sm:text-sm text-gray-600 group-hover:text-gray-500">
                    {suggestion.description}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Start Conversation Button */}
        <button
          onClick={onCreateNewChat}
          className="inline-flex items-center gap-2 px-8 py-4 sm:px-6 sm:py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 active:bg-gray-700 transition-colors duration-200 font-medium text-base sm:text-base touch-manipulation"
        >
          <svg
            className="w-5 h-5 sm:w-4 sm:h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Start New Conversation
        </button>

        {/* Footer Info */}
        <div className="mt-8 sm:mt-12 text-sm sm:text-xs text-gray-400 space-y-1 px-4 sm:px-0">
          <p>
            RoboPilot can make mistakes. Consider checking important
            information.
          </p>
          <p>Your conversations may be used to improve the service.</p>
        </div>
      </div>

      {/* ChatGPT-style Input Area */}
      {setUserText && onSendMessage && (
        <div className="w-full max-w-4xl mx-auto px-4 sm:px-4 pb-4 sm:pb-6 pt-4 safe-area-bottom">
          <div className="relative">
            <input
              type="text"
              value={userText}
              onChange={(e) => setUserText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && canSend && userText.trim()) {
                  onSendMessage();
                }
              }}
              className="w-full px-6 py-4 sm:py-4 pr-16 sm:pr-14 rounded-2xl border border-gray-300 focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-colors text-base placeholder-gray-500 bg-white shadow-lg touch-manipulation"
              placeholder="Message RoboPilot..."
              disabled={!canSend}
            />
            <button
              onClick={() => {
                if (canSend && userText.trim()) {
                  onSendMessage();
                }
              }}
              disabled={!canSend || !userText.trim()}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 p-3 sm:p-2.5 bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors rounded-xl touch-manipulation"
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
      )}
    </div>
  );
};

export default WelcomeScreen;
