import React, { useState } from "react";
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Platform,
  Keyboard,
  Text,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useVoiceInputWithWakeWord } from "../hooks/useVoiceInputWithWakeWord";
import { InputMode } from "../types/api";
import * as Haptics from "expo-haptics";

interface InputBarProps {
  mode: InputMode;
  onModeChange: (mode: InputMode) => void;
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  enableWakeWord?: boolean;
  wakeWords?: string[];
  showSessionIndicator?: boolean;
  sessionStatus?: "connected" | "connecting" | "disconnected";
}

export default function InputBar({
  mode,
  onModeChange,
  onSendMessage,
  isLoading = false,
  disabled = false,
  placeholder = "Message RoboPilot...",
  enableWakeWord = true,
  wakeWords = ["hey robopilot", "ok robopilot"],
  showSessionIndicator = false,
  sessionStatus = "disconnected",
}: InputBarProps) {
  const [textInput, setTextInput] = useState("");

  const {
    isListening,
    isProcessing,
    transcript,
    isWakeWordActive,
    detectedWakeWord,
    startListening,
    stopListening,
    toggleWakeWordDetection,
    reset: resetVoice,
  } = useVoiceInputWithWakeWord({
    enableWakeWord: mode === "voice" && enableWakeWord,
    wakeWords,
    onTranscriptionUpdate: (text) => {
      if (text) {
        onSendMessage(text);
        resetVoice();
      }
    },
    onError: (error) => {
      Alert.alert("Voice Error", error);
    },
    onWakeWordDetected: (wakeWord) => {
      console.log("Wake word detected:", wakeWord);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    },
  });

  const handleSendText = () => {
    if (textInput.trim() && !isLoading && !disabled) {
      onSendMessage(textInput.trim());
      setTextInput("");
      Keyboard.dismiss();
    }
  };

  const handleVoiceToggle = async () => {
    if (!disabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

      if (isListening) {
        stopListening();
      } else {
        startListening();
      }
    }
  };

  const handleModeToggle = async () => {
    if (!disabled) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      const newMode: InputMode = mode === "keyboard" ? "voice" : "keyboard";
      onModeChange(newMode);
    }
  };

  const getVoiceButtonColor = () => {
    if (disabled) return "#9CA3AF";
    if (isListening) return "#EF4444";
    if (isProcessing) return "#F59E0B";
    if (isWakeWordActive) return "#10B981";
    return "#3B82F6";
  };

  const getVoiceButtonIcon = () => {
    if (isProcessing) return "hourglass-outline";
    if (isListening) return "stop";
    if (isWakeWordActive && !isListening) return "ear";
    return "mic";
  };

  const getStatusText = () => {
    if (detectedWakeWord) return `Wake word: "${detectedWakeWord}"`;
    if (isProcessing) return "Processing speech...";
    if (isListening) return "Listening...";
    if (isWakeWordActive && !isListening) return "Wake word detection active";
    return null;
  };

  const getSessionStatusColor = () => {
    switch (sessionStatus) {
      case "connected":
        return "#10B981";
      case "connecting":
        return "#F59E0B";
      default:
        return "#EF4444";
    }
  };

  if (mode === "voice") {
    return (
      <View style={styles.container}>
        {/* Session Status Indicator */}
        {showSessionIndicator && (
          <View style={styles.sessionIndicator}>
            <View
              style={[
                styles.sessionStatusDot,
                { backgroundColor: getSessionStatusColor() },
              ]}
            />
            <Text style={styles.sessionStatusText}>
              {sessionStatus.charAt(0).toUpperCase() + sessionStatus.slice(1)}
            </Text>
          </View>
        )}

        <View style={styles.voiceContainer}>
          {/* Mode Toggle Button */}
          <TouchableOpacity
            style={[styles.modeButton, disabled && styles.disabled]}
            onPress={handleModeToggle}
            disabled={disabled}
          >
            <Ionicons
              name="chatbubbles"
              size={20}
              color={disabled ? "#9CA3AF" : "#6B7280"}
            />
          </TouchableOpacity>

          {/* Wake Word Toggle Button */}
          {enableWakeWord && (
            <TouchableOpacity
              style={[
                styles.wakeWordButton,
                isWakeWordActive && styles.wakeWordActive,
                disabled && styles.disabled,
              ]}
              onPress={toggleWakeWordDetection}
              disabled={disabled}
            >
              <Ionicons
                name={isWakeWordActive ? "ear" : "ear-outline"}
                size={16}
                color={isWakeWordActive ? "#10B981" : "#6B7280"}
              />
            </TouchableOpacity>
          )}

          {/* Voice Recording Button */}
          <TouchableOpacity
            style={[
              styles.voiceButton,
              {
                backgroundColor: getVoiceButtonColor(),
                transform: isListening
                  ? [{ scale: 1.15 }]
                  : isWakeWordActive
                    ? [{ scale: 1.05 }]
                    : [{ scale: 1 }],
              },
              disabled && styles.disabled,
            ]}
            onPress={handleVoiceToggle}
            disabled={disabled || isProcessing}
          >
            {isProcessing ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Ionicons name={getVoiceButtonIcon()} size={28} color="white" />
            )}
          </TouchableOpacity>

          {/* Settings Button */}
          <TouchableOpacity
            style={[styles.settingsButton, disabled && styles.disabled]}
            onPress={() => {
              // Handle settings press
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
            disabled={disabled}
          >
            <Ionicons
              name="settings-outline"
              size={18}
              color={disabled ? "#9CA3AF" : "#6B7280"}
            />
          </TouchableOpacity>
        </View>

        {/* Enhanced Status Container */}
        <View style={styles.statusContainer}>
          {/* Status Text */}
          {getStatusText() && (
            <Text
              style={[
                styles.statusText,
                detectedWakeWord && styles.wakeWordText,
                isProcessing && styles.processingText,
                isListening && styles.listeningText,
              ]}
            >
              {getStatusText()}
            </Text>
          )}

          {/* Visual Indicators */}
          {isListening && (
            <View style={styles.listeningIndicator}>
              <View style={[styles.pulse, styles.pulse1]} />
              <View style={[styles.pulse, styles.pulse2]} />
              <View style={[styles.pulse, styles.pulse3]} />
              <View style={[styles.pulse, styles.pulse4]} />
            </View>
          )}

          {/* Processing Indicator */}
          {isProcessing && (
            <View style={styles.processingIndicator}>
              <ActivityIndicator size="small" color="#F59E0B" />
              <Text style={styles.processingText}>Transcribing...</Text>
            </View>
          )}

          {/* Wake Word Indicator */}
          {isWakeWordActive && !isListening && !isProcessing && (
            <View style={styles.wakeWordIndicator}>
              <View style={styles.wakeWordDot} />
              <Text style={styles.wakeWordActiveText}>
                Listening for wake word
              </Text>
            </View>
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Session Status Indicator */}
      {showSessionIndicator && (
        <View style={styles.sessionIndicator}>
          <View
            style={[
              styles.sessionStatusDot,
              { backgroundColor: getSessionStatusColor() },
            ]}
          />
          <Text style={styles.sessionStatusText}>
            {sessionStatus.charAt(0).toUpperCase() + sessionStatus.slice(1)}
          </Text>
        </View>
      )}

      <View style={styles.textContainer}>
        {/* Mode Toggle Button */}
        <TouchableOpacity
          style={[styles.modeButton, disabled && styles.disabled]}
          onPress={handleModeToggle}
          disabled={disabled}
        >
          <Ionicons
            name="mic"
            size={20}
            color={disabled ? "#9CA3AF" : "#6B7280"}
          />
        </TouchableOpacity>

        {/* Text Input */}
        <View style={styles.inputWrapper}>
          <TextInput
            style={[styles.textInput, disabled && styles.disabled]}
            value={textInput}
            onChangeText={setTextInput}
            placeholder={placeholder}
            placeholderTextColor="#9CA3AF"
            multiline
            maxLength={2000}
            editable={!disabled && !isLoading}
            returnKeyType="send"
            onSubmitEditing={handleSendText}
            blurOnSubmit={false}
          />

          {/* Character Count */}
          {textInput.length > 1500 && (
            <Text style={styles.characterCount}>{textInput.length}/2000</Text>
          )}
        </View>

        {/* Send Button */}
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!textInput.trim() || disabled || isLoading) &&
              styles.sendButtonDisabled,
          ]}
          onPress={handleSendText}
          disabled={!textInput.trim() || disabled || isLoading}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color="white" />
          ) : (
            <Ionicons name="send" size={20} color="white" />
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: "white",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: -2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  sessionIndicator: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
    gap: 6,
  },
  sessionStatusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  sessionStatusText: {
    fontSize: 12,
    color: "#6B7280",
    fontWeight: "500",
  },
  textContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 12,
  },
  voiceContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
    paddingVertical: 8,
  },
  modeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#F9FAFB",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  inputWrapper: {
    flex: 1,
    position: "relative",
  },
  textInput: {
    minHeight: 44,
    maxHeight: 120,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#F9FAFB",
    borderRadius: 24,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    fontSize: 16,
    color: "#1F2937",
    textAlignVertical: "center",
  },
  characterCount: {
    position: "absolute",
    right: 12,
    bottom: 6,
    fontSize: 10,
    color: "#9CA3AF",
    backgroundColor: "white",
    paddingHorizontal: 4,
    borderRadius: 2,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#1F2937",
    alignItems: "center",
    justifyContent: "center",
    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  sendButtonDisabled: {
    backgroundColor: "#D1D5DB",
  },
  voiceButton: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: "center",
    justifyContent: "center",
    elevation: 6,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
  },
  wakeWordButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  wakeWordActive: {
    backgroundColor: "#ECFDF5",
    borderColor: "#10B981",
  },
  settingsButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  statusContainer: {
    minHeight: 32,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 12,
    gap: 8,
  },
  statusText: {
    fontSize: 13,
    color: "#6B7280",
    textAlign: "center",
    fontWeight: "500",
  },
  wakeWordText: {
    color: "#10B981",
    fontWeight: "600",
  },
  processingText: {
    color: "#F59E0B",
    fontWeight: "600",
  },
  listeningText: {
    color: "#EF4444",
    fontWeight: "600",
  },
  listeningIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  pulse: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#EF4444",
  },
  pulse1: {
    opacity: 1,
  },
  pulse2: {
    opacity: 0.8,
  },
  pulse3: {
    opacity: 0.6,
  },
  pulse4: {
    opacity: 0.4,
  },
  processingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  wakeWordIndicator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  wakeWordDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#10B981",
  },
  wakeWordActiveText: {
    fontSize: 12,
    color: "#10B981",
    fontWeight: "500",
  },
  disabled: {
    opacity: 0.5,
  },
});
