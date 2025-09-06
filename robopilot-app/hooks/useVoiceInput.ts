import { useState, useRef, useCallback } from "react";
import * as Speech from "expo-speech";
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from "expo-speech-recognition";
import { Audio } from "expo-av";
import { Platform, Alert } from "react-native";
import apiService from "../services/api";

export interface VoiceInputOptions {
  language?: string;
  timeout?: number;
  onTranscriptionUpdate?: (text: string) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
}

export function useVoiceInput(options: VoiceInputOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);

  const audioRecording = useRef<Audio.Recording | null>(null);
  const recognitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    language = "en-US",
    timeout = 10000,
    onTranscriptionUpdate,
    onError,
    onStart,
    onEnd,
  } = options;

  // Setup speech recognition event listeners
  useSpeechRecognitionEvent("start", () => {
    setIsListening(true);
    setError(null);
    onStart?.();
  });

  useSpeechRecognitionEvent("end", () => {
    setIsListening(false);
    onEnd?.();
  });

  useSpeechRecognitionEvent("result", (event) => {
    const newTranscript = event.results[0]?.transcript || "";
    setTranscript(newTranscript);
    onTranscriptionUpdate?.(newTranscript);
  });

  useSpeechRecognitionEvent("error", (event) => {
    const errorMessage = event.error || "Speech recognition error";
    setError(errorMessage);
    setIsListening(false);
    onError?.(errorMessage);
  });

  const requestPermissions = async (): Promise<boolean> => {
    try {
      // Request microphone permissions
      const { status: recordingStatus } = await Audio.requestPermissionsAsync();

      if (recordingStatus !== "granted") {
        Alert.alert(
          "Permission Required",
          "Please grant microphone permissions to use voice input.",
        );
        return false;
      }

      // Request speech recognition permissions if available
      if (Platform.OS === "ios") {
        const speechStatus =
          await ExpoSpeechRecognitionModule.requestPermissionsAsync();
        if (speechStatus.status !== "granted") {
          Alert.alert(
            "Permission Required",
            "Please grant speech recognition permissions to use voice input.",
          );
          return false;
        }
      }

      return true;
    } catch (error) {
      console.error("Error requesting permissions:", error);
      return false;
    }
  };

  const startListening = useCallback(async () => {
    if (isListening || isProcessing) return;

    const hasPermissions = await requestPermissions();
    if (!hasPermissions) return;

    try {
      setError(null);
      setTranscript("");

      // Try to use expo-speech-recognition first (more accurate)
      if ((await ExpoSpeechRecognitionModule.getStateAsync()) === "inactive") {
        await ExpoSpeechRecognitionModule.start({
          lang: language,
          interimResults: true,
          maxAlternatives: 1,
          continuous: false,
        });

        // Set timeout for recognition
        recognitionTimeoutRef.current = setTimeout(() => {
          stopListening();
        }, timeout);
      } else {
        throw new Error("Speech recognition not available");
      }
    } catch (error) {
      console.log(
        "expo-speech-recognition not available, falling back to audio recording",
      );
      await startAudioRecording();
    }
  }, [isListening, isProcessing, language, timeout]);

  const startAudioRecording = async () => {
    try {
      setIsListening(true);
      setIsProcessing(false);
      onStart?.();

      // Configure audio recording
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync({
        android: {
          extension: ".wav",
          outputFormat: Audio.AndroidOutputFormat.PCM_16BIT,
          audioEncoder: Audio.AndroidAudioEncoder.PCM,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: ".wav",
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: "audio/wav",
          bitsPerSecond: 128000,
        },
      });

      audioRecording.current = recording;

      // Set timeout for recording
      recognitionTimeoutRef.current = setTimeout(() => {
        stopListening();
      }, timeout);
    } catch (error) {
      console.error("Failed to start recording:", error);
      setError("Failed to start voice recording");
      setIsListening(false);
      onError?.("Failed to start voice recording");
    }
  };

  const stopListening = useCallback(async () => {
    if (recognitionTimeoutRef.current) {
      clearTimeout(recognitionTimeoutRef.current);
      recognitionTimeoutRef.current = null;
    }

    try {
      // Stop speech recognition if it was used
      if (
        (await ExpoSpeechRecognitionModule.getStateAsync()) === "recognizing"
      ) {
        await ExpoSpeechRecognitionModule.stop();
      }
    } catch (error) {
      // Speech recognition wasn't active, handle audio recording instead
      if (audioRecording.current) {
        setIsProcessing(true);
        setIsListening(false);

        try {
          await audioRecording.current.stopAndUnloadAsync();
          const uri = audioRecording.current.getURI();

          if (uri) {
            // Convert to blob and transcribe
            const response = await fetch(uri);
            const audioBlob = await response.blob();

            const transcriptionResult = await apiService.transcribeAudio(
              audioBlob,
              language,
            );
            const finalTranscript = transcriptionResult.text || "";

            setTranscript(finalTranscript);
            onTranscriptionUpdate?.(finalTranscript);
          }
        } catch (error) {
          console.error("Error processing audio recording:", error);
          setError("Failed to process voice recording");
          onError?.("Failed to process voice recording");
        } finally {
          audioRecording.current = null;
          setIsProcessing(false);
          onEnd?.();
        }
      }
    }

    setIsListening(false);
  }, [language, onTranscriptionUpdate, onError, onEnd]);

  const speak = useCallback(
    async (text: string, options?: Speech.SpeechOptions) => {
      if (!text.trim()) return;

      try {
        // Stop any ongoing speech
        Speech.stop();

        // Start speaking
        Speech.speak(text, {
          language: language.replace("-", "_"), // expo-speech uses underscores
          pitch: 1.0,
          rate: 0.9,
          ...options,
        });
      } catch (error) {
        console.error("Error with text-to-speech:", error);
      }
    },
    [language],
  );

  const stopSpeaking = useCallback(() => {
    Speech.stop();
  }, []);

  const reset = useCallback(() => {
    setTranscript("");
    setError(null);
    if (recognitionTimeoutRef.current) {
      clearTimeout(recognitionTimeoutRef.current);
      recognitionTimeoutRef.current = null;
    }
  }, []);

  return {
    isListening,
    isProcessing,
    transcript,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    reset,
    isAvailable: true, // Always return true for mobile
  };
}
