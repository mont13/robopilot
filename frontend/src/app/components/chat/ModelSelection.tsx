import { ModelInfo } from "@/app/api/lmstudio";
import React from "react";

interface ModelSelectionProps {
  models: ModelInfo[];
  loadedModel: ModelInfo | null;
  onSelectModel: (modelKey: string) => void;
  isLoading: boolean;
}

const ModelSelection: React.FC<ModelSelectionProps> = ({
  models,
  loadedModel,
  onSelectModel,
  isLoading,
}) => {
  return (
    <select
      className="w-full p-2 rounded border bg-white dark:bg-gray-800 dark:border-gray-700"
      value={loadedModel?.name || ""}
      onChange={(e) => onSelectModel(e.target.value)}
      disabled={isLoading}
    >
      <option value="" disabled>
        Select a model
      </option>
      {models.map((model) => (
        <option key={model.name} value={model.name}>
          {model.name}
        </option>
      ))}
    </select>
  );
};

export default ModelSelection;
