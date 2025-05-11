import { listVoices, VoiceResponse } from "@/app/api/voice";
import { useAudio } from "@/app/contexts/AudioContext";
import { useLMStudio } from "@/app/contexts/LMStudioContext";
import React, { useEffect, useState } from "react";
import ModelSelection from "./chat/ModelSelection";

interface AudioSettingsProps {
  onClose: () => void;
  isVisible: boolean;
}

const AudioSettings: React.FC<AudioSettingsProps> = ({
  onClose,
  isVisible,
}) => {
  const [, setVoices] = useState<VoiceResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Get values from AudioContext
  const { selectedVoice, setSelectedVoice, speakerId, setSpeakerId } =
    useAudio();
  const { models, loadedModel } = useLMStudio();

  useEffect(() => {
    if (isVisible) {
      loadVoices();
    }
  }, [isVisible]);

  const loadVoices = async () => {
    setIsLoading(true);
    try {
      const voicesList = await listVoices();
      setVoices(voicesList);

      // If no voice is selected yet but we have voices, select the first one
      if (!selectedVoice && voicesList.length > 0) {
        setSelectedVoice(voicesList[0].id);
      }
    } catch (error) {
      console.error("Error loading voices:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = () => {
    // The audio context now handles saving to cookies automatically
    onClose();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="px-4 sm:px-6 py-4 border-b">
          <h3 className="text-lg font-medium">Audio Settings</h3>
        </div>

        <div className="p-4 sm:p-6">
          <div className="mb-6">
            <h4 className="text-lg font-semibold mb-2">Chat Model Settings</h4>
            <ModelSelection
              models={models}
              loadedModel={loadedModel}
              onSelectModel={(modelKey) =>
                console.log({ type: "model_selected", modelKey })
              }
              isLoading={isLoading}
            />
          </div>

          <div className="mb-6">
            <h4 className="text-lg font-semibold mb-2">Audio Settings</h4>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Speaker ID
              </label>
              <div className="flex items-center">
                <input
                  type="range"
                  min="0"
                  max="9"
                  value={speakerId}
                  onChange={(e) => setSpeakerId(Number(e.target.value))}
                  className="flex-1 mr-2 w-full"
                />
                <span className="text-sm bg-gray-100 px-2 py-1 rounded whitespace-nowrap">
                  {speakerId}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Different speaker IDs can change the character of the voice
              </p>
            </div>
          </div>
        </div>

        <div className="px-4 sm:px-6 py-4 bg-gray-50 flex flex-col sm:flex-row sm:justify-end gap-2 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded w-full sm:w-auto"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!selectedVoice}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded disabled:opacity-50 hover:bg-blue-700 w-full sm:w-auto"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default AudioSettings;
