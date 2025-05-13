import React from "react";

interface ModeSelectionProps {
  onSelectMode: (mode: "chat" | "voice") => void;
}

const ModeSelection: React.FC<ModeSelectionProps> = ({ onSelectMode }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="bg-white p-4 sm:p-8 rounded-xl shadow-lg max-w-md w-full">
        <h1 className="text-xl sm:text-2xl font-bold text-center mb-4 sm:mb-6">
          Choose Interaction Mode
        </h1>

        <div className="space-y-3 sm:space-y-4">
          <button
            onClick={() => {
              sessionStorage.setItem("interactionMode", "chat");
              onSelectMode("chat");
            }}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white p-3 sm:p-4 rounded-lg flex items-center justify-center transition-colors"
          >
            <div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 sm:h-8 sm:w-8 mb-1 sm:mb-2 mx-auto"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="block text-base sm:text-lg font-medium">
                Chat Mode
              </span>
              <span className="text-xs sm:text-sm block mt-1">
                Type messages and receive text responses
              </span>
            </div>
          </button>

          <button
            onClick={() => {
              sessionStorage.setItem("interactionMode", "voice");
              onSelectMode("voice");
            }}
            className="w-full bg-green-500 hover:bg-green-600 text-white p-3 sm:p-4 rounded-lg flex items-center justify-center transition-colors"
          >
            <div>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 sm:h-8 sm:w-8 mb-1 sm:mb-2 mx-auto"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="block text-base sm:text-lg font-medium">
                Voice Mode
              </span>
              <span className="text-xs sm:text-sm block mt-1">
                Record voice messages and hear spoken responses
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModeSelection;
