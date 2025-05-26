import { listConnections } from "@/app/api/connections";
import { listVoices, VoiceResponse } from "@/app/api/voice";
import { useAudio } from "@/app/contexts/AudioContext";
import { useLMStudio } from "@/app/contexts/LMStudioContext";
import React, { useEffect, useState } from "react";
// No need to import ConnectionSelection as we're using a plain select

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
  const { connections, activeConnection, activateConnectionById } = useLMStudio();
  
  // We don't need this since we're using a simple select now

  useEffect(() => {
    if (isVisible) {
      loadVoices();
    }
  }, [isVisible]);

  const loadVoices = async () => {
    setIsLoading(true);
    try {
      const [voicesList, connectionsList] = await Promise.all([
        listVoices(),
        listConnections(),
      ]);
      setVoices(voicesList);

      // If no voice is selected yet but we have voices, select the first one
      if (!selectedVoice && voicesList.length > 0) {
        setSelectedVoice(voicesList[0].id);
        setTranscriptionLanguage("en"); // Default language
      }

      // If no connection is active yet but we have connections, add a note in the console
      if (!activeConnection && connectionsList.length > 0) {
        // We don't auto-activate - user must explicitly select
        console.log("No active connection. Please select a connection from the dropdown.");
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-800 dark:text-white">
            Audio Settings
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            aria-label="Close"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        <div className="p-4 sm:p-6 dark:text-gray-200">
          <div className="mb-6">
            <h4 className="text-lg font-semibold mb-2 text-gray-800 dark:text-white">
              Model Settings
            </h4>
            <div className="space-y-4">
              <div>
                <h5 className="text-md font-medium mb-1 text-gray-700 dark:text-gray-300">
                  LLM Connection {!connections.length && "(None Available)"}
                </h5>
                <select
                  className="w-full p-2 rounded border bg-white dark:bg-gray-800 dark:border-gray-700"
                  value={activeConnection?.id || ""}
                  onChange={(e) => activateConnectionById(e.target.value)}
                  disabled={isLoading || connections.length === 0}
                >
                  <option value="" disabled>
                    Select a connection
                  </option>
                  {(() => {
                    // Group connections by provider
                    const groupedConnections = connections.reduce((acc, connection) => {
                      const provider = connection.provider;
                      if (!acc[provider]) {
                        acc[provider] = [];
                      }
                      acc[provider].push(connection);
                      return acc;
                    }, {} as Record<string, typeof connections>);
                    
                    // Get providers in alphabetical order
                    const providers = Object.keys(groupedConnections).sort();
                    
                    // If no connections, show message
                    if (providers.length === 0) {
                      return (
                        <option value="" disabled>
                          No connections available
                        </option>
                      );
                    }
                    
                    return providers.map(provider => (
                      <optgroup key={provider} label={provider.toUpperCase()}>
                        {groupedConnections[provider].map(connection => (
                          <option key={connection.id} value={connection.id}>
                            {connection.name} ({connection.model_name})
                            {connection.is_active ? " • Active" : ""}
                          </option>
                        ))}
                      </optgroup>
                    ));
                  })()}
                </select>
              </div>
              <div>
                <h5 className="text-md font-medium mb-1 text-gray-700 dark:text-gray-300">
                  Audio Voice
                </h5>
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
