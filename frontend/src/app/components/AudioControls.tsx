import React from "react";

interface AudioControlsProps {
  className?: string;
  isRecording: boolean;
  isProcessing: boolean;
  onToggleRecording: () => void;
  disabled?: boolean;
}

const AudioControls: React.FC<AudioControlsProps> = ({
  className = "",
  isRecording,
  isProcessing,
  onToggleRecording,
  disabled = false,
}) => {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <button
        onClick={onToggleRecording}
        disabled={disabled || isProcessing}
        className={`${
          isRecording
            ? "bg-red-500 hover:bg-red-600"
            : "bg-blue-500 hover:bg-blue-600"
        } text-white rounded-full p-4 transition-colors ${
          disabled || isProcessing
            ? "opacity-50 cursor-not-allowed"
            : "cursor-pointer"
        }`}
        title={isRecording ? "Stop Recording" : "Start Recording"}
      >
        {isProcessing ? (
          <LoadingIcon className="w-6 h-6 animate-spin" />
        ) : isRecording ? (
          <StopIcon className="w-6 h-6" />
        ) : (
          <MicrophoneIcon className="w-6 h-6" />
        )}
      </button>
    </div>
  );
};

// Icons
const MicrophoneIcon = ({ className = "w-6 h-6" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className={className}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
    />
  </svg>
);

const StopIcon = ({ className = "w-6 h-6" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    className={className}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M5.25 7.5A2.25 2.25 0 017.5 5.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25h-9a2.25 2.25 0 01-2.25-2.25v-9z"
    />
  </svg>
);

const LoadingIcon = ({ className = "w-6 h-6" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    className={className}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
    />
  </svg>
);

export default AudioControls;
