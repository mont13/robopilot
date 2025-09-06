import React, { useCallback, useState } from "react";
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
  const [selectedConnectionId, setSelectedConnectionId] = useState<string>("");

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

  // Handle connection selection
  const handleConnectionSelect = useCallback(
    (connectionId: string) => {
      setSelectedConnectionId(connectionId);
      onSelectConnection(connectionId);
    },
    [onSelectConnection],
  );

  // Create a new connection
  const handleCreateNewConnection = useCallback(() => {
    if (onCreateConnection) {
      onCreateConnection();
    }
  }, [onCreateConnection]);

  // Get provider icon
  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case "openai":
        return (
          <div className="w-6 h-6 bg-black rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">AI</span>
          </div>
        );
      case "gemini":
        return (
          <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">G</span>
          </div>
        );
      case "lmstudio":
        return (
          <div className="w-6 h-6 bg-purple-500 rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">LM</span>
          </div>
        );
      case "ollama":
        return (
          <div className="w-6 h-6 bg-green-500 rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">O</span>
          </div>
        );
      default:
        return (
          <div className="w-6 h-6 bg-gray-500 rounded flex items-center justify-center">
            <span className="text-white text-xs font-bold">?</span>
          </div>
        );
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          LLM Connections
          {connections.length > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({connections.length})
            </span>
          )}
        </h3>
        {onCreateConnection && (
          <button
            onClick={handleCreateNewConnection}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
            title="Create new connection"
          >
            <svg
              className="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Add
          </button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
            Loading connections...
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && connections.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
              />
            </svg>
          </div>
          <h3 className="text-sm font-medium text-gray-900 mb-1">
            No connections
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Create your first LLM connection to get started
          </p>
          {onCreateConnection && (
            <button
              onClick={handleCreateNewConnection}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg border border-blue-200 hover:border-blue-300 transition-colors"
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
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
              Create Connection
            </button>
          )}
        </div>
      )}

      {/* Connections List */}
      {!isLoading && connections.length > 0 && (
        <div className="space-y-3">
          {providers.map((provider) => (
            <div key={provider} className="space-y-2">
              {/* Provider Header */}
              <div className="flex items-center gap-2 px-2">
                {getProviderIcon(provider)}
                <h4 className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                  {provider}
                </h4>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              {/* Provider Connections */}
              <div className="space-y-1">
                {groupedConnections[provider].map((connection) => {
                  const isActive = activeConnection?.id === connection.id;
                  const isSelected = selectedConnectionId === connection.id;

                  return (
                    <button
                      key={connection.id}
                      onClick={() => handleConnectionSelect(connection.id)}
                      disabled={isLoading}
                      className={`
                        w-full p-3 rounded-lg text-left transition-all duration-200 group
                        ${
                          isActive
                            ? "bg-blue-50 border border-blue-200 shadow-sm"
                            : "bg-white border border-gray-200 hover:border-gray-300 hover:shadow-sm"
                        }
                        ${isSelected ? "ring-2 ring-blue-500 ring-opacity-20" : ""}
                        disabled:opacity-50 disabled:cursor-not-allowed
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h5
                              className={`text-sm font-medium truncate ${isActive ? "text-blue-900" : "text-gray-900"}`}
                            >
                              {connection.name}
                            </h5>
                            {isActive && (
                              <span className="badge badge-success text-xs">
                                Active
                              </span>
                            )}
                          </div>
                          <p
                            className={`text-xs truncate ${isActive ? "text-blue-600" : "text-gray-500"}`}
                          >
                            {connection.model_name}
                          </p>
                          {connection.base_url && (
                            <p className="text-xs text-gray-400 truncate mt-1">
                              {connection.base_url}
                            </p>
                          )}
                        </div>

                        {/* Connection Status */}
                        <div className="flex items-center gap-2 ml-3">
                          <div
                            className={`w-2 h-2 rounded-full ${connection.is_active ? "bg-green-500" : "bg-gray-300"}`}
                          />
                          <svg
                            className={`w-4 h-4 transition-transform duration-200 ${isActive ? "text-blue-500" : "text-gray-400 group-hover:text-gray-600"}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConnectionSelection;
