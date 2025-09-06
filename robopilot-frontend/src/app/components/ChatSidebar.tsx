"use client";

import React, { useState } from "react";
import type { AgentSessionInfo } from "@/app/api/agent";

interface ChatSidebarProps {
  sessions: AgentSessionInfo[];
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onCreateNewSession: () => void;
  currentSessionId: string | null;
  isCollapsed?: boolean;
  className?: string;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  onSelectSession,
  onDeleteSession,
  onCreateNewSession,
  currentSessionId,
  isCollapsed = false,
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

    if (isCollapsed) return name.substring(0, 2).toUpperCase();
    return name.length > 28 ? `${name.substring(0, 25)}...` : name;
  };

  // Handle session deletion with loading state
  const handleDeleteSession = async (
    sessionId: string,
    event: React.MouseEvent,
  ) => {
    event.stopPropagation();
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
        return diffInMinutes < 1 ? "Just now" : `${diffInMinutes}m`;
      }
      return `${Math.floor(diffInHours)}h`;
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
    });
  };

  // Get message count for session
  const getMessageCount = (session: AgentSessionInfo) => {
    return session.message_count || 0;
  };

  if (isCollapsed) {
    return (
      <div
        className={`h-full flex flex-col overflow-hidden sidebar-no-horizontal ${className}`}
      >
        {/* Collapsed New Chat Button */}
        <div className="px-2 pt-2 pb-3 flex-shrink-0">
          <button
            onClick={onCreateNewSession}
            className="w-full h-10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors group"
            title="New Chat"
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
          </button>
        </div>

        {/* Collapsed Sessions List */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 pb-2 scrollbar-dark">
          <div className="space-y-1">
            {sessions.map((session) => {
              const isActive = currentSessionId === session.session_id;
              const isDeleting = deletingSessionId === session.session_id;
              const sessionName = session.session_name || "Unnamed Session";

              return (
                <div key={session.session_id} className="relative group">
                  <button
                    onClick={() =>
                      !isDeleting && onSelectSession(session.session_id)
                    }
                    className={`
                      w-full h-10 flex items-center justify-center rounded-lg transition-all duration-200 relative
                      ${
                        isActive
                          ? "bg-gray-700 text-white shadow-sm"
                          : "text-gray-400 hover:text-white hover:bg-gray-800"
                      }
                      ${isDeleting ? "opacity-50 pointer-events-none" : ""}
                    `}
                  >
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z"
                        clipRule="evenodd"
                      />
                    </svg>

                    {/* Active indicator */}
                    {isActive && (
                      <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-white rounded-r-full" />
                    )}
                  </button>

                  {/* Tooltip */}
                  <div className="absolute left-full ml-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
                    <div className="bg-gray-800 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap border border-gray-600">
                      {sessionName}
                      {getMessageCount(session) > 0 && (
                        <span className="text-gray-300 ml-1">
                          ({getMessageCount(session)} messages)
                        </span>
                      )}
                      <div className="absolute left-0 top-1/2 transform -translate-x-1 -translate-y-1/2 w-2 h-2 bg-gray-800 border-l border-b border-gray-600 rotate-45"></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`h-full flex flex-col overflow-hidden sidebar-no-horizontal ${className}`}
    >
      {/* New Chat Button */}
      <div className="p-3 sm:p-3 flex-shrink-0">
        <button
          onClick={onCreateNewSession}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 sm:py-2.5 bg-gray-800 hover:bg-gray-700 active:bg-gray-600 text-white rounded-lg transition-colors font-medium text-base sm:text-sm touch-manipulation"
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
          New Chat
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-6 sm:p-6 text-center text-gray-400">
            <div className="w-14 h-14 sm:w-12 sm:h-12 bg-gray-800 rounded-full flex items-center justify-center mb-4 sm:mb-3">
              <svg
                className="w-7 h-7 sm:w-6 sm:h-6"
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
            <p className="text-base sm:text-sm">No conversations yet</p>
            <p className="text-sm sm:text-xs mt-2 sm:mt-1 text-gray-500">
              Start a new chat to begin
            </p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 pb-3 sm:pb-3 scrollbar-dark">
            <div className="space-y-2 sm:space-y-1">
              {sessions.map((session) => {
                const isActive = currentSessionId === session.session_id;
                const isDeleting = deletingSessionId === session.session_id;
                const isHovered = hoveredSessionId === session.session_id;
                const messageCount = getMessageCount(session);

                return (
                  <div
                    key={session.session_id}
                    className={`
                      group relative rounded-lg transition-all duration-200 cursor-pointer touch-manipulation
                      ${
                        isActive
                          ? "bg-gray-700 text-white shadow-sm"
                          : "text-gray-300 hover:text-white hover:bg-gray-800 active:bg-gray-750"
                      }
                      ${isDeleting ? "opacity-50 pointer-events-none" : ""}
                    `}
                    onMouseEnter={() => setHoveredSessionId(session.session_id)}
                    onMouseLeave={() => setHoveredSessionId(null)}
                  >
                    <div
                      className="flex items-center gap-3 p-4 sm:p-3 pr-12 sm:pr-8"
                      onClick={() =>
                        !isDeleting && onSelectSession(session.session_id)
                      }
                    >
                      {/* Session Icon */}
                      <div className="w-6 h-6 sm:w-5 sm:h-5 flex-shrink-0 flex items-center justify-center">
                        <svg
                          className="w-5 h-5 sm:w-4 sm:h-4"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>

                      {/* Session Content */}
                      <div className="flex-1 min-w-0">
                        <div
                          className={`text-base sm:text-sm font-medium truncate mb-1 sm:mb-0.5 ${isActive ? "text-white" : "text-gray-200"}`}
                          title={session.session_name || "Unnamed Session"}
                        >
                          {formatSessionName(session)}
                        </div>
                        <div className="flex items-center justify-between text-sm sm:text-xs">
                          <span
                            className={`${isActive ? "text-gray-300" : "text-gray-400"}`}
                          >
                            {formatDate(
                              session.updated_at || session.created_at,
                            )}
                          </span>
                        </div>
                      </div>

                      {/* Message count positioned on the right */}
                      {messageCount > 0 && (
                        <div className="flex-shrink-0 ml-2">
                          <span
                            className={`px-2 py-1 sm:px-1.5 sm:py-0.5 rounded-full text-sm sm:text-xs font-medium ${isActive ? "bg-gray-600 text-gray-200" : "bg-gray-700 text-gray-300"}`}
                          >
                            {messageCount}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Delete Button */}
                    {(isHovered || isActive) && !isDeleting && (
                      <button
                        onClick={(e) =>
                          handleDeleteSession(session.session_id, e)
                        }
                        className="absolute right-3 sm:right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 sm:group-hover:opacity-100 p-2 sm:p-1 text-gray-400 hover:text-red-400 hover:bg-red-900/20 rounded transition-all duration-200 touch-manipulation"
                        aria-label="Delete session"
                      >
                        <svg
                          className="w-4 h-4 sm:w-3.5 sm:h-3.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    )}

                    {/* Active Session Indicator */}
                    {isActive && (
                      <div className="absolute left-0 top-3 sm:top-2 bottom-3 sm:bottom-2 w-1 bg-white rounded-r-full" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSidebar;
