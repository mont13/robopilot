import React, { useCallback } from "react";
import { LLMConnectionResponse } from "@/app/api/connections";

interface ConnectionSelectionProps {
  connections: LLMConnectionResponse[];
  activeConnection: LLMConnectionResponse | null;
  onSelectConnection: (connectionId: string) => void;
  isLoading: boolean;
  onCreateConnection?: () => void;
}

const ConnectionSelection: React.FC<ConnectionSelectionProps> = ({
  connections,
  activeConnection,
  onSelectConnection,
  isLoading,
  onCreateConnection,
}) => {
  // Group connections by provider
  const groupedConnections = connections.reduce(
    (acc, connection) => {
      const provider = connection.provider;
      if (!acc[provider]) {
        acc[provider] = [];
      }
      acc[provider].push(connection);
      return acc;
    },
    {} as Record<string, LLMConnectionResponse[]>,
  );

  // Get providers in alphabetical order
  const providers = Object.keys(groupedConnections).sort();

  // Create a new connection - placeholder function that would typically open a form
  const handleCreateNewConnection = useCallback(() => {
    if (onCreateConnection) {
      onCreateConnection();
    }
  }, [onCreateConnection]);

  return (
    <div className="w-full space-y-3">
      <div className="flex flex-col sm:flex-row gap-2">
        <select
          className="w-full sm:flex-grow p-2.5 rounded-md border border-gray-300 bg-white dark:bg-white dark:border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-sm shadow-sm"
          value={activeConnection?.id || ""}
          onChange={(e) => onSelectConnection(e.target.value)}
          disabled={isLoading}
          aria-label="Select connection"
        >
          <option value="" disabled>
            {isLoading ? "Loading connections..." : "Select a connection"}
          </option>

          {providers.map((provider) => (
            <optgroup key={provider} label={provider.toUpperCase()}>
              {groupedConnections[provider].map((connection) => (
                <option key={connection.id} value={connection.id}>
                  {connection.name} ({connection.model_name})
                  {connection.is_active ? " • Active" : ""}
                </option>
              ))}
            </optgroup>
          ))}

          {connections.length === 0 && (
            <option value="" disabled>
              No connections available
            </option>
          )}
        </select>
        <button
          onClick={handleCreateNewConnection}
          disabled={isLoading}
          className="w-full sm:w-auto px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-sm"
          title="Create new connection"
          aria-label="Create new connection"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mr-1.5"
          >
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>New Connection</span>
        </button>
      </div>
      {connections.length === 0 && !isLoading && (
        <div className="text-sm text-gray-500 dark:text-gray-400 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
          <p>
            No connections available. Create a new connection to get started.
          </p>
        </div>
      )}
      {isLoading && (
        <div className="text-sm text-gray-500 dark:text-gray-400 flex items-center justify-center py-2">
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Loading connections...
        </div>
      )}
    </div>
  );
};

export default ConnectionSelection;
