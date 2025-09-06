import React, { useState } from "react";
import type { AgentSessionInfo } from "@/app/api/agent";

interface SessionListProps {
  sessions: AgentSessionInfo[];
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onCreateNewSession: () => void;
  currentSessionId: string | null;
  className?: string;
}

const SessionList: React.FC<SessionListProps> = ({
  sessions,
  onSelectSession,
  onDeleteSession,
  onCreateNewSession,
  currentSessionId,
  className = "",
}) => {
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(
    null,
  );
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  // Format the session name, limiting to certain length
  const formatSessionName = (session: AgentSessionInfo) => {
    const name =
      session.session_name ||
      `Session ${new Date(session.created_at || "").toLocaleString()}`;
    return name.length > 35 ? `${name.substring(0, 32)}...` : name;
  };

  // Handle session deletion with loading state
  const handleDeleteSession = async (sessionId: string) => {
    setDeletingSessionId(sessionId);
    try {
      onDeleteSession(sessionId);
    } finally {
      setDeletingSessionId(null);
    }
  };

  // Format the date to be more readable
  const formatDate = (dateString?: string) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    // If less than 24 hours ago, show relative time
    if (diffInHours < 24) {
      if (diffInHours < 1) {
        const diffInMinutes = Math.floor(
          (now.getTime() - date.getTime()) / (1000 * 60),
        );
        return diffInMinutes < 1 ? "Just now" : `${diffInMinutes}m ago`;
      }
      return `${Math.floor(diffInHours)}h ago`;
    }

    // If the session was created today, just show the time
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    // Otherwise show the date
    return date.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  };

  // Get message count for session
  const getMessageCount = (session: AgentSessionInfo) => {
    return session.message_count || 0;
  };

  return (
    <div className={`h-full flex flex-col bg-white ${className}`}>
      {/* Header with New Chat Button */}
      <div className="p-4 border-b border-gray-100">
        <button
          onClick={onCreateNewSession}
          className="w-full btn btn-primary py-3 text-sm font-medium shadow-sm"
        >
          <svg
            className="w-4 h-4"
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
          New Chat
        </button>
      </div>

      {/* Sessions List */}
      <div className="overflow-y-auto flex-1 scrollbar-thin">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h3 className="text-sm font-medium text-gray-900 mb-1">
              No conversations yet
            </h3>
            <p className="text-xs text-gray-500">
              Start a new chat to begin your conversation
            </p>
          </div>
        ) : (
          <div className="p-2">
            {sessions.map((session) => {
              const isActive = currentSessionId === session.session_id;
              const isDeleting = deletingSessionId === session.session_id;
              const isHovered = hoveredSessionId === session.session_id;
              const messageCount = getMessageCount(session);

              return (
                <div
                  key={session.session_id}
                  className={`
                    group relative mb-2 rounded-lg transition-all duration-200 cursor-pointer
                    ${isActive ? "bg-blue-50 border border-blue-200 shadow-sm" : "hover:bg-gray-50 border border-transparent"}
                    ${isDeleting ? "opacity-50 pointer-events-none" : ""}
                  `}
                  onMouseEnter={() => setHoveredSessionId(session.session_id)}
                  onMouseLeave={() => setHoveredSessionId(null)}
                >
                  <div
                    className="flex items-start gap-3 p-3"
                    onClick={() =>
                      !isDeleting && onSelectSession(session.session_id)
                    }
                  >
                    {/* Session Icon */}
                    <div
                      className={`
                      w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5
                      ${isActive ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600 group-hover:bg-gray-200"}
                    `}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>

                    {/* Session Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h3
                          className={`text-sm font-medium truncate ${isActive ? "text-blue-900" : "text-gray-900"}`}
                        >
                          {formatSessionName(session)}
                        </h3>
                        {(isHovered || isActive) && !isDeleting && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSession(session.session_id);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 rounded transition-all duration-200 hover:bg-red-50"
                            aria-label="Delete session"
                          >
                            {isDeleting ? (
                              <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <svg
                                className="w-3 h-3"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            )}
                          </button>
                        )}
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span
                          className={`${isActive ? "text-blue-600" : "text-gray-500"}`}
                        >
                          {formatDate(session.updated_at || session.created_at)}
                        </span>
                        {messageCount > 0 && (
                          <span
                            className={`
                            px-1.5 py-0.5 rounded-full text-xs font-medium
                            ${isActive ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}
                          `}
                          >
                            {messageCount} msg{messageCount !== 1 ? "s" : ""}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Active Session Indicator */}
                  {isActive && (
                    <div className="absolute left-0 top-3 bottom-3 w-1 bg-blue-500 rounded-r-full" />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionList;
