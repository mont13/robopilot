import { useState, useEffect } from 'react';
import { Alert, Platform } from 'react-native';
import * as Speech from 'expo-speech';

// Note: react-native-wakeword might need additional setup for production use
// For this demo, we'll simulate wake word detection

export interface UseVoiceInputReturn {
  isListening: boolean;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  transcriptText: string;
}

export function useVoiceInput(): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcriptText, setTranscriptText] = useState('');

  useEffect(() => {
    checkSpeechAvailability();
  }, []);

  const checkSpeechAvailability = async () => {
    try {
      // Check if speech recognition is available
      if (Platform.OS === 'web') {
        const isAvailable = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        setIsSupported(isAvailable);
      } else {
        // On mobile platforms, we'll assume it's supported
        setIsSupported(true);
      }
    } catch (error) {
      console.error('Error checking speech availability:', error);
      setIsSupported(false);
    }
  };

  const startListening = async () => {
    if (!isSupported) {
      Alert.alert('Error', 'Speech recognition is not supported on this device');
      return;
    }

    try {
      setIsListening(true);
      setTranscriptText('');

      if (Platform.OS === 'web') {
        startWebSpeechRecognition();
      } else {
        // For mobile platforms, we'll simulate speech recognition
        // In a real implementation, you would integrate with expo-speech-recognition
        simulateSpeechRecognition();
      }
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      Alert.alert('Error', 'Failed to start voice recognition');
      setIsListening(false);
    }
  };

  const stopListening = () => {
    setIsListening(false);
  };

  const startWebSpeechRecognition = () => {
    if (Platform.OS !== 'web') return;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setTranscriptText(transcript);
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      Alert.alert('Error', 'Voice recognition failed. Please try again.');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const simulateSpeechRecognition = () => {
    // Simulate speech recognition for demo purposes
    setTimeout(() => {
      const sampleTranscripts = [
        "Hello, how are you?",
        "What's the weather like today?",
        "Can you help me with something?",
        "Tell me a joke",
        "What time is it?"
      ];
      const randomTranscript = sampleTranscripts[Math.floor(Math.random() * sampleTranscripts.length)];
      setTranscriptText(randomTranscript);
      setIsListening(false);
    }, 2000);
  };

  return {
    isListening,
    isSupported,
    startListening,
    stopListening,
    transcriptText,
  };
}