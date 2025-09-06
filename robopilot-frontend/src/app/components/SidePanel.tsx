import React, { useEffect, useRef } from "react";

interface SidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  side?: "left" | "right";
  width?: "sm" | "md" | "lg" | "xl";
  showOverlay?: boolean;
}

const SidePanel: React.FC<SidePanelProps> = ({
  isOpen,
  onClose,
  title,
  children,
  side = "left",
  width = "md",
  showOverlay = true,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      // Prevent body scroll when panel is open
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(event.target as Node) &&
        isOpen
      ) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  const getWidthClass = () => {
    switch (width) {
      case "sm":
        return "w-80";
      case "md":
        return "w-96";
      case "lg":
        return "w-[28rem]";
      case "xl":
        return "w-[32rem]";
      default:
        return "w-96";
    }
  };

  const getAnimationClasses = () => {
    const baseClasses = "transform transition-all duration-300 ease-in-out";
    if (side === "left") {
      return `${baseClasses} ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`;
    } else {
      return `${baseClasses} ${
        isOpen ? "translate-x-0" : "translate-x-full"
      }`;
    }
  };

  return (
    <>
      {/* Overlay */}
      {showOverlay && (
        <div
          className={`fixed inset-0 bg-black transition-opacity duration-300 z-40 ${
            isOpen ? "opacity-50" : "opacity-0 pointer-events-none"
          }`}
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Side Panel */}
      <div
        ref={panelRef}
        className={`
          fixed top-0 ${side === "left" ? "left-0" : "right-0"} h-full
          bg-white shadow-2xl z-50 flex flex-col
          ${getWidthClass()}
          ${getAnimationClasses()}
        `}
        role="dialog"
        aria-modal="true"
        aria-labelledby="panel-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
          <h2
            id="panel-title"
            className="text-lg font-semibold text-gray-900 truncate"
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg transition-colors focus-ring"
            aria-label="Close panel"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {children}
        </div>
      </div>
    </>
  );
};

export default SidePanel;
