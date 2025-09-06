import React, { useState, useEffect, useRef } from "react";
import {
  View,
  FlatList,
  StyleSheet,
  Alert,
  Text,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Haptics from "expo-haptics";

import MessageBubble from "../components/MessageBubble";
import InputBar from "../components/InputBar";
import apiService from "../services/api";
import { useVoiceInputWithWakeWord } from "../hooks/useVoiceInputWithWakeWord";
import {
  ConversationMessage,
  ConversationHistory,
  InputMode,
  CreateSessionResponse,
  AgentExecutionRequest,
} from "../types/api";

const STORAGE_KEYS = {
  MESSAGES: "chat_messages",
  SESSION_ID: "session_id",
  INPUT_MODE: "input_mode",
};

export default function HomeScreen() {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [inputMode, setInputMode] = useState<InputMode>("keyboard");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentPlayingId, setCurrentPlayingId] = useState<string | null>(null);
  const [enableWakeWord, setEnableWakeWord] = useState(true);

  const flatListRef = useRef<FlatList>(null);

  const { speak, stopSpeaking, isWakeWordActive, detectedWakeWord } =
    useVoiceInputWithWakeWord({
      enableWakeWord: inputMode === "voice" && enableWakeWord,
      wakeWords: ["hey robopilot", "ok robopilot", "robopilot"],
      onError: (error) => {
        Alert.alert("Voice Error", error);
      },
      onWakeWordDetected: (wakeWord) => {
        console.log("Wake word detected in main app:", wakeWord);
      },
    });

  // Load persisted data on app start
  useEffect(() => {
    loadPersistedData();
    checkConnection();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);

  const loadPersistedData = async () => {
    try {
      const [savedMessages, savedSessionId, savedInputMode] = await Promise.all(
        [
          AsyncStorage.getItem(STORAGE_KEYS.MESSAGES),
          AsyncStorage.getItem(STORAGE_KEYS.SESSION_ID),
          AsyncStorage.getItem(STORAGE_KEYS.INPUT_MODE),
        ],
      );

      if (savedMessages) {
        setMessages(JSON.parse(savedMessages));
      }

      if (savedSessionId) {
        setCurrentSessionId(savedSessionId);
        // Try to load session from server
        await loadSessionHistory(savedSessionId);
      }

      if (savedInputMode) {
        setInputMode(savedInputMode as InputMode);
      }
    } catch (error) {
      console.error("Error loading persisted data:", error);
    }
  };

  const checkConnection = async () => {
    try {
      const healthy = await apiService.healthCheck();
      setIsConnected(healthy);
    } catch (error) {
      console.error("Connection check failed:", error);
      setIsConnected(false);
    }
  };

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const history = await apiService.getSessionHistory(sessionId);
      if (history && history.messages) {
        setMessages(history.messages);
        await AsyncStorage.setItem(
          STORAGE_KEYS.MESSAGES,
          JSON.stringify(history.messages),
        );
      }
    } catch (error) {
      console.error("Error loading session history:", error);
    }
  };

  const saveMessagesToStorage = async (
    updatedMessages: ConversationMessage[],
  ) => {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.MESSAGES,
        JSON.stringify(updatedMessages),
      );
    } catch (error) {
      console.error("Error saving messages:", error);
    }
  };

  const createNewSession = async () => {
    try {
      setIsLoading(true);

      // Check connection first
      const healthy = await apiService.healthCheck();
      if (!healthy) {
        Alert.alert(
          "Connection Error",
          "Unable to connect to the server. Please check your connection.",
        );
        return;
      }

      const response: CreateSessionResponse = await apiService.createSession();

      setCurrentSessionId(response.sessionId);
      setMessages([]);

      // Save to storage
      await AsyncStorage.setItem(STORAGE_KEYS.SESSION_ID, response.sessionId);
      await AsyncStorage.removeItem(STORAGE_KEYS.MESSAGES);

      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error("Error creating new session:", error);
      Alert.alert("Error", "Failed to create new session. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    // Ensure we have a session
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const response = await apiService.createSession();
        sessionId = response.sessionId;
        setCurrentSessionId(sessionId);
        await AsyncStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
      } catch (error) {
        Alert.alert("Error", "Failed to create session");
        return;
      }
    }

    // Add user message immediately
    const userMessage: ConversationMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: messageText.trim(),
      timestamp: new Date().toISOString(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    await saveMessagesToStorage(updatedMessages);

    setIsLoading(true);

    try {
      // Prepare request
      const request: AgentExecutionRequest = {
        message: messageText.trim(),
        sessionId,
      };

      // Send to API
      const response = await apiService.sendMessage(request);

      // Add assistant response
      const assistantMessage: ConversationMessage = {
        id: response.messageId || `assistant_${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);
      await saveMessagesToStorage(finalMessages);

      // Auto-play TTS for voice mode
      if (inputMode === "voice") {
        handlePlayTTS(response.response, assistantMessage.id);
      }

      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.error("Error sending message:", error);

      // Add error message
      const errorMessage: ConversationMessage = {
        id: `error_${Date.now()}`,
        role: "assistant",
        content:
          "Sorry, I encountered an error processing your message. Please try again.",
        timestamp: new Date().toISOString(),
      };

      const errorMessages = [...updatedMessages, errorMessage];
      setMessages(errorMessages);
      await saveMessagesToStorage(errorMessages);

      Alert.alert(
        "Error",
        "Failed to send message. Please check your connection and try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputModeChange = async (newMode: InputMode) => {
    setInputMode(newMode);
    await AsyncStorage.setItem(STORAGE_KEYS.INPUT_MODE, newMode);

    // Stop any ongoing TTS when switching modes
    if (currentPlayingId) {
      stopSpeaking();
      setCurrentPlayingId(null);
    }
  };

  const handlePlayTTS = async (text: string, messageId: string) => {
    if (currentPlayingId) {
      stopSpeaking();
      setCurrentPlayingId(null);

      // If same message, just stop
      if (currentPlayingId === messageId) {
        return;
      }
    }

    setCurrentPlayingId(messageId);

    try {
      await speak(text, {
        onDone: () => {
          setCurrentPlayingId(null);
        },
        onError: () => {
          setCurrentPlayingId(null);
        },
      });
    } catch (error) {
      console.error("TTS Error:", error);
      setCurrentPlayingId(null);
    }
  };

  const handleStopTTS = () => {
    stopSpeaking();
    setCurrentPlayingId(null);
  };

  const renderMessage = ({ item }: { item: ConversationMessage }) => (
    <MessageBubble
      message={item}
      onPlayTTS={handlePlayTTS}
      onStopTTS={handleStopTTS}
      isPlaying={currentPlayingId === item.id}
    />
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.headerContent}>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>RoboPilot</Text>
          <View style={styles.statusRow}>
            <View
              style={[
                styles.connectionStatus,
                isConnected ? styles.connected : styles.disconnected,
              ]}
            >
              <View
                style={[
                  styles.statusDot,
                  isConnected ? styles.connectedDot : styles.disconnectedDot,
                ]}
              />
              <Text
                style={[
                  styles.statusText,
                  isConnected ? styles.connectedText : styles.disconnectedText,
                ]}
              >
                {isConnected ? "Connected" : "Offline"}
              </Text>
            </View>
            {inputMode === "voice" && isWakeWordActive && (
              <View style={[styles.connectionStatus, styles.wakeWordStatus]}>
                <View style={[styles.statusDot, styles.wakeWordDot]} />
                <Text style={[styles.statusText, styles.wakeWordText]}>
                  Wake Word Active
                </Text>
              </View>
            )}
          </View>
        </View>

        <TouchableOpacity
          style={[styles.newChatButton, isLoading && styles.disabled]}
          onPress={createNewSession}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator size="small" color="#3B82F6" />
          ) : (
            <Ionicons name="add" size={24} color="#3B82F6" />
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Ionicons name="chatbubble-ellipses-outline" size={80} color="#D1D5DB" />
      <Text style={styles.emptyTitle}>Welcome to RoboPilot</Text>
      <Text style={styles.emptySubtitle}>
        Start a conversation by sending a message or using voice input
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="white" />

      {renderHeader()}

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        style={styles.messagesList}
        contentContainerStyle={[
          styles.messagesContainer,
          messages.length === 0 && styles.emptyContainer,
        ]}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={renderEmptyState}
        onContentSizeChange={() => {
          if (messages.length > 0) {
            flatListRef.current?.scrollToEnd({ animated: false });
          }
        }}
      />

      <InputBar
        mode={inputMode}
        onModeChange={handleInputModeChange}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={!isConnected}
        enableWakeWord={enableWakeWord}
        wakeWords={["hey robopilot", "ok robopilot", "robopilot"]}
        placeholder={
          !isConnected
            ? "Connect to server first..."
            : isWakeWordActive && inputMode === "voice"
              ? "Listening for wake word..."
              : "Message RoboPilot..."
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "white",
  },
  header: {
    backgroundColor: "white",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
    paddingBottom: 12,
  },
  headerContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  titleContainer: {
    flex: 1,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 4,
  },
  connectionStatus: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 6,
  },
  connected: {
    backgroundColor: "#ECFDF5",
  },
  disconnected: {
    backgroundColor: "#FEF2F2",
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  connectedDot: {
    backgroundColor: "#10B981",
  },
  disconnectedDot: {
    backgroundColor: "#EF4444",
  },
  statusText: {
    fontSize: 12,
    fontWeight: "500",
  },
  connectedText: {
    color: "#065F46",
  },
  disconnectedText: {
    color: "#991B1B",
  },
  wakeWordStatus: {
    backgroundColor: "#EFF6FF",
  },
  wakeWordDot: {
    backgroundColor: "#3B82F6",
  },
  wakeWordText: {
    color: "#1E40AF",
  },
  newChatButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#EFF6FF",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#DBEAFE",
  },
  messagesList: {
    flex: 1,
  },
  messagesContainer: {
    paddingVertical: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
  },
  emptyState: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: "600",
    color: "#374151",
    marginTop: 16,
    marginBottom: 8,
    textAlign: "center",
  },
  emptySubtitle: {
    fontSize: 16,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 24,
  },
  disabled: {
    opacity: 0.5,
  },
});
