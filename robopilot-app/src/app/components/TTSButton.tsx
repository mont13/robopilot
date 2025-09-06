import React from "react";
import { useAppSelector } from "@/app/lib/hooks";
import { selectTtsSettings } from "@/app/lib/features/settings/settingsSlice";

interface TTSButtonProps {
  messageId: string;
  text: string;
  isPlaying: boolean;
  onPlay: (text: string, messageId: string) => void;
  onStop: () => void;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const TTSButton: React.FC<TTSButtonProps> = ({
  messageId,
  text,
  isPlaying,
  onPlay,
  onStop,
  className = "",
  size = "sm",
}) => {
  const { ttsEnabled } = useAppSelector(selectTtsSettings);

  // Don't render if TTS is disabled globally
  if (!ttsEnabled) {
    return null;
  }

  const handleClick = () => {
    if (isPlaying) {
      onStop();
    } else {
      onPlay(text, messageId);
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case "sm":
        return "w-3 h-3";
      case "md":
        return "w-4 h-4";
      case "lg":
        return "w-5 h-5";
      default:
        return "w-3 h-3";
    }
  };

  const getButtonSizeClasses = () => {
    switch (size) {
      case "sm":
        return "p-1";
      case "md":
        return "p-1.5";
      case "lg":
        return "p-2";
      default:
        return "p-1";
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`
        ${getButtonSizeClasses()}
        rounded-full transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
        ${
          isPlaying
            ? "bg-blue-500 text-white hover:bg-blue-600"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800"
        }
        ${className}
      `}
      title={isPlaying ? "Stop speech" : "Play speech"}
      aria-label={isPlaying ? "Stop speech" : "Play speech"}
    >
      {isPlaying ? (
        <StopIcon className={getSizeClasses()} />
      ) : (
        <PlayIcon className={getSizeClasses()} />
      )}
    </button>
  );
};

// Play Icon
const PlayIcon = ({ className = "w-3 h-3" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="currentColor"
    viewBox="0 0 24 24"
    className={className}
  >
    <path d="M8 5v14l11-7z" />
  </svg>
);

// Stop Icon
const StopIcon = ({ className = "w-3 h-3" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="currentColor"
    viewBox="0 0 24 24"
    className={className}
  >
    <path d="M6 6h12v12H6z" />
  </svg>
);

export default TTSButton;
