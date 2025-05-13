import React, { useEffect, useCallback } from "react";
import { useMicVAD, utils } from "@ricky0123/vad-react";
import { useAudio } from "@/app/contexts/AudioContext";
import { v4 as uuidv4 } from "uuid";
import { useTranscript } from "@/app/contexts/TranscriptContext";
import { useEvent } from "@/app/contexts/EventContext";

interface VADProcessorProps {
  isEnabled: boolean;
  onVoiceProcessing?: (processing: boolean) => void;
}

const VADProcessor: React.FC<VADProcessorProps> = ({
  isEnabled,
  onVoiceProcessing,
}) => {
  const { addTranscriptMessage, updateTranscriptItemStatus } = useTranscript();
  const {
    isProcessingVoice,
    setIsProcessingVoice,
    ttsPlayingMessageId,
    stopTextToSpeech,
    processAudioData,
  } = useAudio();
  const { logClientEvent } = useEvent();

  // Create a callback for speech end detection
  const handleSpeechEnd = useCallback(
    async (audio: Float32Array) => {
      if (!isEnabled) return;

      // Don't process if we're already processing voice or playing TTS
      if (isProcessingVoice || ttsPlayingMessageId) return;

      try {
        // Log the speech detection
        logClientEvent({
          type: "speech_detected",
          audioLength: audio.length,
        });

        // Stop any ongoing TTS
        stopTextToSpeech();

        // Add a processing message to the transcript
        const processingId = uuidv4();
        addTranscriptMessage(processingId, "user", "[Processing audio...]");

        // Signal that we're processing voice
        setIsProcessingVoice(true);
        if (onVoiceProcessing) onVoiceProcessing(true);

        // Convert audio to WAV format
        const wavBuffer = utils.encodeWAV(audio);
        const audioBlob = new Blob([wavBuffer], { type: "audio/wav" });

        // Process the audio data (this function will be implemented in AudioContext)
        await processAudioData(audioBlob, processingId);
      } catch (error) {
        console.error("VAD speech processing error:", error);
        logClientEvent({
          type: "vad_error",
          error: error instanceof Error ? error.message : String(error),
        });
      } finally {
        if (onVoiceProcessing) onVoiceProcessing(false);
        // Note: We don't need to set isProcessingVoice to false here
        // as it's handled inside processAudioData already
      }
    },
    [
      isEnabled,
      isProcessingVoice,
      ttsPlayingMessageId,
      stopTextToSpeech,
      addTranscriptMessage,
      updateTranscriptItemStatus,
      setIsProcessingVoice,
      processAudioData,
      logClientEvent,
    ],
  );

  // Configure the VAD hook
  const vad = useMicVAD({
    // Only start if enabled and not currently processing or playing
    startOnLoad: false,
    model: "v5",
    // Higher speech threshold for less false positives
    positiveSpeechThreshold: 0.45,
    // Minimum frames to consider valid speech (prevents short noises)
    minSpeechFrames: 2,
    // Callback when speech ends
    onSpeechEnd: handleSpeechEnd,
    // Audio tweaks for better quality
    additionalAudioConstraints: {},
  });

  // Control VAD based on props
  useEffect(() => {
    if (isEnabled && !ttsPlayingMessageId && !isProcessingVoice) {
      if (!vad.listening && !vad.loading) {
        vad.start();
        logClientEvent({
          type: "vad_started",
        });
      }
    } else {
      if (vad.listening) {
        vad.pause();
        logClientEvent({
          type: "vad_paused",
        });
      }
    }
  }, [isEnabled, ttsPlayingMessageId, isProcessingVoice, vad, logClientEvent]);

  return null; // This is a non-visual component
};

export default VADProcessor;
