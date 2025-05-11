import React from "react";
import { ChatSession } from "@/app/api/lmstudio";

interface SessionListProps {
  sessions: ChatSession[];
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
  // Format the session name, limiting to certain length
  const formatSessionName = (session: ChatSession) => {
    const name = session.name || `Session ${new Date(session.created_at).toLocaleString()}`;
    return name.length > 30 ? `${name.substring(0, 27)}...` : name;
  };

  // Format the date to be more readable
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    
    // If the session was created today, just show the time
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Otherwise show the date
    return date.toLocaleDateString([], { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  return (
    <div className={`h-full flex flex-col ${className}`}>
      <div className="p-3 sm:p-4 border-b">
        <button
          onClick={onCreateNewSession}
          className="w-full bg-gray-900 text-white py-2 rounded-lg hover:bg-gray-800 transition-colors text-sm sm:text-base font-medium"
        >
          New Chat
        </button>
      </div>

      <div className="overflow-y-auto flex-1 px-1">
        {sessions.length === 0 ? (
          <div className="text-center text-gray-500 p-6 my-4">
            No chat sessions available
          </div>
        ) : (
          <ul>
            {sessions.map((session) => (
              <li key={session.id}>
                <div
                    className={`flex justify-between items-center p-3 sm:p-4 cursor-pointer hover:bg-gray-100 border-b ${
                      currentSessionId === session.id ? "bg-blue-50" : ""
                    }`}
                  >
                    <div
                      className="flex-1 mr-2"
                      onClick={() => onSelectSession(session.id)}
                    >
                      <div className="font-medium text-gray-900 text-xs sm:text-sm md:text-base truncate">
                        {formatSessionName(session)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(session.updated_at || session.created_at)}
                      </div>
                    </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    className="text-gray-500 hover:text-red-600 p-2 rounded-full hover:bg-gray-200"
                    aria-label="Delete session"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 sm:h-5 sm:w-5"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SessionList;