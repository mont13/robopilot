import { LLMConnectionResponse } from "@/app/api/connections";
import React from "react";

interface ModelSelectionProps {
  connections: LLMConnectionResponse[];
  activeConnection: LLMConnectionResponse | null;
  onSelectConnection: (connectionId: string) => void;
  isLoading: boolean;
}

const ModelSelection: React.FC<ModelSelectionProps> = ({
  connections,
  activeConnection,
  onSelectConnection,
  isLoading,
}) => {
  return (
    <select
      className="w-full p-2 rounded border bg-white dark:bg-gray-800 dark:border-gray-700"
      value={activeConnection?.id || ""}
      onChange={(e) => onSelectConnection(e.target.value)}
      disabled={isLoading}
    >
      <option value="" disabled>
        Select a connection
      </option>
      {connections.map((connection) => (
        <option key={connection.id} value={connection.id}>
          {connection.name} ({connection.provider} / {connection.model_name})
        </option>
      ))}
    </select>
  );
};

export default ModelSelection;
