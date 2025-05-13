"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { v4 as uuidv4 } from "uuid";
import { synthesizeSpeech, transcribeAudio } from "@/app/api/voice";
import { useEvent } from "./EventContext";
import { useLMStudio } from "./LMStudioContext";
import { useTranscript } from "./TranscriptContext";
import WavRecorder from "@/app/utils/wavRecorder";

// Define interfaces for context state and props
interface AudioContextState {
  // Audio recording state
  isRecording: boolean;
  isProcessingVoice: boolean;
  setIsProcessingVoice: (isProcessing: boolean) => void;
  startRecording: () => void;
  stopRecording: () => Promise<void>;

  // Text-to-speech state
  ttsPlayingMessageId: string | null;
  playTextToSpeech: (text: string, messageId: string) => Promise<void>;
  stopTextToSpeech: () => void;

  // Voice settings
  selectedVoice: string | null;
  setSelectedVoice: (voice: string | null) => void;
  speakerId: number;
  setSpeakerId: (id: number) => void;

  // Voice Activity Detection (VAD)
  processAudioData: (audioBlob: Blob, processingId: string) => Promise<void>;

  // Transcription language
  setTranscriptionLanguage: (language: string) => void;
}

interface AudioProviderProps {
  children: ReactNode;
}

// Create the context
const AudioContext = createContext<AudioContextState | undefined>(undefined);

// Provider component
export function AudioProvider({ children }: AudioProviderProps) {
  const { sendUserMessage } = useLMStudio();
  const { addTranscriptMessage, updateTranscriptItemStatus } = useTranscript();
  const { logClientEvent } = useEvent();

  // Recording state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState<boolean>(false);
  const [wavRecorder] = useState<WavRecorder>(new WavRecorder());

  // TTS state
  const [ttsPlayingMessageId, setTtsPlayingMessageId] = useState<string | null>(
    null,
  );
  const [audioPlayer, setAudioPlayer] = useState<HTMLAudioElement | null>(null);

  // Voice settings
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [transcriptionLanguage, setTranscriptionLanguage] = useState<string>("en");
  const [speakerId, setSpeakerId] = useState<number>(0);

  // Load voice settings from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedVoice = localStorage.getItem("selectedVoice");
      if (savedVoice) {
        setSelectedVoice(savedVoice);
      }

      const savedSpeakerId = localStorage.getItem("speakerId");
      if (savedSpeakerId !== null) {
        setSpeakerId(parseInt(savedSpeakerId, 10) || 0);
      }
    }
  }, []);

  // Save voice settings to localStorage when they change
  useEffect(() => {
    if (typeof window !== "undefined" && selectedVoice) {
      localStorage.setItem("selectedVoice", selectedVoice);
    }
  }, [selectedVoice]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("speakerId", speakerId.toString());
    }
  }, [speakerId]);

  // Initialize WAV recorder and audio player
  useEffect(() => {
    if (typeof window !== "undefined") {
      // Initialize WAV recorder - use a slight delay to ensure browser is ready
      setTimeout(() => {
        WavRecorder.initialize().catch((error) => {
          console.error("Failed to initialize WAV recorder:", error);
          logClientEvent({
            type: "audio_initialization_error",
            error: error instanceof Error ? error.message : String(error),
          });
        });
      }, 1000);

      // Initialize audio player
      if (!audioPlayer) {
        const player = new Audio();
        setAudioPlayer(player);

        // Clean up when component unmounts
        return () => {
          player.pause();
          player.src = "";
        };
      }
    }
  }, [audioPlayer]);

  // Function to play text using TTS
  const playTextToSpeech = useCallback(
    async (text: string, messageId: string) => {
      if (!selectedVoice || !audioPlayer) return;

      try {
        // Set the message ID that's currently being played
        setTtsPlayingMessageId(messageId);

        // Use the synthesizeSpeech API
        const audioBuffer = await synthesizeSpeech({
          text,
          voice_id: selectedVoice,
          speaker_id: speakerId,
        });

        // Convert ArrayBuffer to Blob
        const blob = new Blob([audioBuffer], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);

        // Play the audio
        audioPlayer.src = url;
        await audioPlayer.play();

        // Clean up when finished
        audioPlayer.onended = () => {
          setTtsPlayingMessageId(null);
          URL.revokeObjectURL(url);
        };

        // Also handle other ways the audio might stop
        audioPlayer.onerror = () => {
          setTtsPlayingMessageId(null);
          URL.revokeObjectURL(url);
        };

        audioPlayer.onpause = () => {
          // Only clear if it's actually ended, not just paused temporarily
          if (audioPlayer.currentTime >= audioPlayer.duration - 0.1) {
            setTtsPlayingMessageId(null);
            URL.revokeObjectURL(url);
          }
        };
      } catch (error) {
        console.error("TTS playback error:", error);
        setTtsPlayingMessageId(null);
      }
    },
    [selectedVoice, speakerId, audioPlayer],
  );

  // Function to stop TTS playback
  const stopTextToSpeech = useCallback(() => {
    if (audioPlayer) {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      setTtsPlayingMessageId(null);
    }
  }, [audioPlayer]);

  // Function to start recording audio
  const startRecording = useCallback(() => {
    if (typeof window === "undefined" || isRecording) {
      return;
    }

    wavRecorder
      .startRecording()
      .then(() => {
        setIsRecording(true);
        logClientEvent({
          type: "recording_started",
        });
      })
      .catch((error) => {
        console.error("Could not start recording:", error);
        logClientEvent({
          type: "recording_error",
          error: error instanceof Error ? error.message : String(error),
        });
      });
  }, [isRecording, logClientEvent, wavRecorder]);

  // Function to stop recording and process audio
  const stopRecording = useCallback(async () => {
    if (!isRecording) {
      return;
    }

    return new Promise<void>((resolve) => {
      setIsProcessingVoice(true);

      // Add a stopping indicator to the transcript
      const processingId = uuidv4();
      addTranscriptMessage(processingId, "user", "[Processing audio...]");

      wavRecorder
        .stopRecording()
        .then(async (audioBlob) => {
          try {
            // Process the audio data using our shared method
            await processAudioData(audioBlob, processingId);
          } catch (error) {
            console.error("Error processing voice:", error);
            updateTranscriptItemStatus(processingId, "DONE");

            logClientEvent({
              type: "voice_processing_error",
              error: error instanceof Error ? error.message : "Unknown error",
            });
          } finally {
            setIsRecording(false);
            resolve();
          }
        })
        .catch((error) => {
          console.error("Error stopping recording:", error);
          updateTranscriptItemStatus(processingId, "DONE");
          setIsProcessingVoice(false);
          setIsRecording(false);
          resolve();
        });
    });
  }, [
    isRecording,
    addTranscriptMessage,
    updateTranscriptItemStatus,
    logClientEvent,
    wavRecorder,
  ]);

  // Function to process audio data from VAD or recorder
  const processAudioData = useCallback(
    async (audioBlob: Blob, processingId: string) => {
      setIsProcessingVoice(true);

      try {
        // Use the real transcription API with WAV format
        const transcriptionResult = await transcribeAudio(
          audioBlob,
          transcriptionLanguage,
          "wav",
        );
        const transcribedText = transcriptionResult.text;

        // Update the processing message with the transcribed text
        updateTranscriptItemStatus(
          processingId,
          "IN_PROGRESS",
          transcribedText,
        );
        updateTranscriptItemStatus(processingId, "DONE");

        // Now send to LLM
        const response = await sendUserMessage(transcribedText);

        if (response) {
          // Add assistant response to transcript
          const responseId = uuidv4();
          addTranscriptMessage(responseId, "assistant", response, false);
          updateTranscriptItemStatus(responseId, "DONE");

          // Convert response to speech
          await playTextToSpeech(response, responseId);
        }
      } catch (error) {
        console.error("Error processing voice:", error);

        // Show error in transcript
        updateTranscriptItemStatus(processingId, "DONE");

        logClientEvent({
          type: "voice_processing_error",
          error: error instanceof Error ? error.message : "Unknown error",
        });
      } finally {
        setIsProcessingVoice(false);
      }
    },
    [
      addTranscriptMessage,
      updateTranscriptItemStatus,
      sendUserMessage,
      logClientEvent,
      playTextToSpeech,
    ],
  );

  // Provide the context value
  const contextValue: AudioContextState = {
    isRecording,
    isProcessingVoice,
    setIsProcessingVoice,
    startRecording,
    stopRecording,
    ttsPlayingMessageId,
    playTextToSpeech,
    stopTextToSpeech,
    selectedVoice,
    setSelectedVoice,
    speakerId,
    setSpeakerId,
    processAudioData,
    setTranscriptionLanguage,
  };

  return (
    <AudioContext.Provider value={contextValue}>
      {children}
    </AudioContext.Provider>
  );
}

// Custom hook to use the audio context
export function useAudio() {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error("useAudio must be used within an AudioProvider");
  }
  return context;
}
