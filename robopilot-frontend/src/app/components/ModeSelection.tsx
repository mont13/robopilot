import React, { useState } from "react";

interface ModeSelectionProps {
  onSelectMode: (mode: "chat" | "voice") => void;
}

const ModeSelection: React.FC<ModeSelectionProps> = ({ onSelectMode }) => {
  const [selectedMode, setSelectedMode] = useState<"chat" | "voice" | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(false);

  const handleModeSelect = async (mode: "chat" | "voice") => {
    if (isLoading) return;

    setSelectedMode(mode);
    setIsLoading(true);

    // Add a small delay for visual feedback
    setTimeout(() => {
      sessionStorage.setItem("interactionMode", mode);
      onSelectMode(mode);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 opacity-20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-gradient-to-br from-purple-100 to-purple-200 opacity-20 blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Robotika
          </h1>
          <p className="text-gray-600 text-lg">
            Choose how you&apos;d like to interact with AI
          </p>
        </div>

        {/* Mode Selection Cards */}
        <div className="space-y-4">
          {/* Chat Mode */}
          <button
            onClick={() => handleModeSelect("chat")}
            disabled={isLoading}
            className={`
              w-full p-6 rounded-2xl border-2 transition-all duration-300 text-left
              ${
                selectedMode === "chat"
                  ? "border-blue-500 bg-blue-50 shadow-lg scale-105"
                  : "border-gray-200 bg-white hover:border-blue-300 hover:shadow-md hover:scale-[1.02]"
              }
              ${isLoading && selectedMode !== "chat" ? "opacity-50" : ""}
              focus-ring disabled:cursor-not-allowed
            `}
          >
            <div className="flex items-start gap-4">
              <div
                className={`
                w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300
                ${selectedMode === "chat" ? "bg-blue-500 text-white" : "bg-blue-100 text-blue-600"}
              `}
              >
                {selectedMode === "chat" && isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg
                    className="w-6 h-6"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  Chat Mode
                </h3>
                <p className="text-gray-600 mb-3">
                  Type messages and receive text responses
                </p>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Fast typing experience</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Perfect for detailed conversations</span>
                </div>
              </div>
            </div>
          </button>

          {/* Voice Mode */}
          <button
            onClick={() => handleModeSelect("voice")}
            disabled={isLoading}
            className={`
              w-full p-6 rounded-2xl border-2 transition-all duration-300 text-left
              ${
                selectedMode === "voice"
                  ? "border-green-500 bg-green-50 shadow-lg scale-105"
                  : "border-gray-200 bg-white hover:border-green-300 hover:shadow-md hover:scale-[1.02]"
              }
              ${isLoading && selectedMode !== "voice" ? "opacity-50" : ""}
              focus-ring disabled:cursor-not-allowed
            `}
          >
            <div className="flex items-start gap-4">
              <div
                className={`
                w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300
                ${selectedMode === "voice" ? "bg-green-500 text-white" : "bg-green-100 text-green-600"}
              `}
              >
                {selectedMode === "voice" && isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg
                    className="w-6 h-6"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-1">
                  Voice Mode
                </h3>
                <p className="text-gray-600 mb-3">
                  Record voice messages and hear spoken responses
                </p>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Natural conversation flow</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>Hands-free interaction</span>
                </div>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>You can switch between modes anytime in the app</p>
        </div>
      </div>
    </div>
  );
};

export default ModeSelection;
