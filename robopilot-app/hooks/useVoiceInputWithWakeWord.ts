import { useState, useRef, useCallback, useEffect } from "react";
import * as Speech from "expo-speech";
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from "expo-speech-recognition";
import { Audio } from "expo-av";
import { Platform, Alert } from "react-native";
import { WakeWord } from "react-native-wakeword";
import apiService from "../services/api";

export interface VoiceInputWithWakeWordOptions {
  language?: string;
  timeout?: number;
  wakeWords?: string[];
  enableWakeWord?: boolean;
  vadSensitivity?: number;
  onTranscriptionUpdate?: (text: string) => void;
  onError?: (error: string) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onWakeWordDetected?: (wakeWord: string) => void;
}

export function useVoiceInputWithWakeWord(options: VoiceInputWithWakeWordOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isWakeWordActive, setIsWakeWordActive] = useState(false);
  const [detectedWakeWord, setDetectedWakeWord] = useState<string | null>(null);

  const audioRecording = useRef<Audio.Recording | null>(null);
  const recognitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const wakeWordInstance = useRef<any>(null);

  const {
    language = "en-US",
    timeout = 10000,
    wakeWords = ["hey robopilot", "ok robopilot"],
    enableWakeWord = true,
    vadSensitivity = 0.5,
    onTranscriptionUpdate,
    onError,
    onStart,
    onEnd,
    onWakeWordDetected,
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

  // Initialize wake word detection
  useEffect(() => {
    if (enableWakeWord) {
      initializeWakeWord();
    }

    return () => {
      cleanupWakeWord();
    };
  }, [enableWakeWord]);

  const initializeWakeWord = async () => {
    try {
      const hasPermissions = await requestPermissions();
      if (!hasPermissions) return;

      // Initialize wake word detection
      wakeWordInstance.current = new WakeWord({
        sensitivity: vadSensitivity,
        wakeWords: wakeWords,
        onWakeWordDetected: (word: string) => {
          console.log("Wake word detected:", word);
          setDetectedWakeWord(word);
          onWakeWordDetected?.(word);

          // Automatically start listening after wake word detection
          startListening();
        },
        onError: (error: string) => {
          console.error("Wake word detection error:", error);
          setError(`Wake word error: ${error}`);
          onError?.(error);
        },
      });

      // Start wake word monitoring
      await startWakeWordDetection();
    } catch (error) {
      console.error("Failed to initialize wake word detection:", error);
      setError("Failed to initialize wake word detection");
    }
  };

  const cleanupWakeWord = () => {
    if (wakeWordInstance.current) {
      try {
        wakeWordInstance.current.stop();
        wakeWordInstance.current = null;
      } catch (error) {
        console.error("Error cleaning up wake word:", error);
      }
    }
  };

  const startWakeWordDetection = async () => {
    if (!wakeWordInstance.current || isWakeWordActive) return;

    try {
      await wakeWordInstance.current.start();
      setIsWakeWordActive(true);
    } catch (error) {
      console.error("Failed to start wake word detection:", error);
      setError("Failed to start wake word detection");
    }
  };

  const stopWakeWordDetection = async () => {
    if (!wakeWordInstance.current || !isWakeWordActive) return;

    try {
      await wakeWordInstance.current.stop();
      setIsWakeWordActive(false);
    } catch (error) {
      console.error("Failed to stop wake word detection:", error);
    }
  };

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
        try {
          const speechStatus =
            await ExpoSpeechRecognitionModule.requestPermissionsAsync();
          if (speechStatus.status !== "granted") {
            Alert.alert(
              "Permission Required",
              "Please grant speech recognition permissions to use voice input.",
            );
            return false;
          }
        } catch (error) {
          console.warn("Speech recognition permissions not available:", error);
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
      setDetectedWakeWord(null);

      // Temporarily stop wake word detection during active listening
      if (enableWakeWord) {
        await stopWakeWordDetection();
      }

      // Try to use expo-speech-recognition first (more accurate)
      try {
        const state = await ExpoSpeechRecognitionModule.getStateAsync();
        if (state === "inactive") {
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
      } catch (speechError) {
        console.log(
          "expo-speech-recognition not available, falling back to audio recording",
        );
        await startAudioRecording();
      }
    } catch (error) {
      console.error("Failed to start listening:", error);
      setError("Failed to start voice input");
      onError?.("Failed to start voice input");

      // Restart wake word detection if it was enabled
      if (enableWakeWord) {
        setTimeout(() => startWakeWordDetection(), 1000);
      }
    }
  }, [isListening, isProcessing, language, timeout, enableWakeWord]);

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

      // Restart wake word detection if it was enabled
      if (enableWakeWord) {
        setTimeout(() => startWakeWordDetection(), 1000);
      }
    }
  };

  const stopListening = useCallback(async () => {
    if (recognitionTimeoutRef.current) {
      clearTimeout(recognitionTimeoutRef.current);
      recognitionTimeoutRef.current = null;
    }

    try {
      // Stop speech recognition if it was used
      try {
        const state = await ExpoSpeechRecognitionModule.getStateAsync();
        if (state === "recognizing") {
          await ExpoSpeechRecognitionModule.stop();
        }
      } catch (speechError) {
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
    } catch (error) {
      console.error("Error stopping listening:", error);
    } finally {
      setIsListening(false);

      // Restart wake word detection after a short delay
      if (enableWakeWord) {
        setTimeout(() => startWakeWordDetection(), 1500);
      }
    }
  }, [language, onTranscriptionUpdate, onError, onEnd, enableWakeWord]);

  const speak = useCallback(
    async (text: string, options?: Speech.SpeechOptions) => {
      if (!text.trim()) return;

      try {
        // Stop any ongoing speech and listening
        Speech.stop();
        if (isListening) {
          await stopListening();
        }

        // Temporarily stop wake word detection during TTS
        if (enableWakeWord) {
          await stopWakeWordDetection();
        }

        // Start speaking
        Speech.speak(text, {
          language: language.replace("-", "_"), // expo-speech uses underscores
          pitch: 1.0,
          rate: 0.9,
          onDone: () => {
            // Restart wake word detection after TTS finishes
            if (enableWakeWord) {
              setTimeout(() => startWakeWordDetection(), 1000);
            }
          },
          onError: (error) => {
            console.error("TTS error:", error);
            // Restart wake word detection on error
            if (enableWakeWord) {
              setTimeout(() => startWakeWordDetection(), 1000);
            }
          },
          ...options,
        });
      } catch (error) {
        console.error("Error with text-to-speech:", error);
        // Restart wake word detection on error
        if (enableWakeWord) {
          setTimeout(() => startWakeWordDetection(), 1000);
        }
      }
    },
    [language, isListening, stopListening, enableWakeWord],
  );

  const stopSpeaking = useCallback(() => {
    Speech.stop();
    // Restart wake word detection when TTS is manually stopped
    if (enableWakeWord) {
      setTimeout(() => startWakeWordDetection(), 500);
    }
  }, [enableWakeWord]);

  const reset = useCallback(() => {
    setTranscript("");
    setError(null);
    setDetectedWakeWord(null);
    if (recognitionTimeoutRef.current) {
      clearTimeout(recognitionTimeoutRef.current);
      recognitionTimeoutRef.current = null;
    }
  }, []);

  const toggleWakeWordDetection = useCallback(async () => {
    if (isWakeWordActive) {
      await stopWakeWordDetection();
    } else {
      await startWakeWordDetection();
    }
  }, [isWakeWordActive]);

  return {
    // Voice recognition state
    isListening,
    isProcessing,
    transcript,
    error,

    // Wake word state
    isWakeWordActive,
    detectedWakeWord,

    // Actions
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    reset,

    // Wake word controls
    startWakeWordDetection,
    stopWakeWordDetection,
    toggleWakeWordDetection,

    // Status
    isAvailable: true,
  };
}
