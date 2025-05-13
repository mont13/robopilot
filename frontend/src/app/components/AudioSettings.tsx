import { listModels } from "@/app/api/lmstudio";
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
  const [voices, setVoices] = useState<VoiceResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Get values from AudioContext
  const {
    selectedVoice,
    setSelectedVoice,
    speakerId,
    setSpeakerId,
    setTranscriptionLanguage,
  } = useAudio();
  const { models, loadedModel } = useLMStudio();

  useEffect(() => {
    if (isVisible) {
      loadVoices();
    }
  }, [isVisible]);

  const loadVoices = async () => {
    setIsLoading(true);
    try {
      const [voicesList, modelsList] = await Promise.all([
        listVoices(),
        listModels(),
      ]);
      setVoices(voicesList);

      // If no voice is selected yet but we have voices, select the first one
      if (!selectedVoice && voicesList.length > 0) {
        setSelectedVoice(voicesList[0].id);
        setTranscriptionLanguage("en"); // Default language
      }

      // If no model is loaded yet but we have models, select the first one
      if (!loadedModel && modelsList.length > 0) {
        setSelectedVoice(modelsList[0].id);
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
            <h4 className="text-lg font-semibold mb-2">Model Settings</h4>
            <div className="space-y-4">
              <div>
                <h5 className="text-md font-medium mb-1">Chat Model</h5>
                <ModelSelection
                  models={models}
                  loadedModel={loadedModel}
                  onSelectModel={(modelKey) => setSelectedVoice(modelKey)}
                  isLoading={isLoading}
                />
              </div>
              <div>
                <h5 className="text-md font-medium mb-1">Audio Voice</h5>
                <select
                  className="w-full p-2 rounded border bg-white dark:bg-gray-800 dark:border-gray-700"
                  value={selectedVoice || ""}
                  onChange={(e) => {
                    const selectedVoiceId = e.target.value;
                    setSelectedVoice(selectedVoiceId);
                    console.log(selectedVoiceId);

                    const languageCode = selectedVoiceId.split("_")[0];
                    console.log(languageCode);
                    setTranscriptionLanguage(languageCode);
                  }}
                  disabled={isLoading}
                >
                  <option value="" disabled>
                    Select a voice
                  </option>
                  {voices.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.id}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-lg font-semibold mb-2">Audio Settings</h4>
            <div className="space-y-4">
              <div>
                <h5 className="text-md font-medium mb-1">Speaker ID</h5>
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
