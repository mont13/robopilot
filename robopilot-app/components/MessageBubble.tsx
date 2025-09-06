import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Platform,
  Animated,
  ActivityIndicator,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { ConversationMessage } from "../types/api";
import * as Haptics from "expo-haptics";

interface MessageBubbleProps {
  message: ConversationMessage;
  index: number;
  onPlayTTS?: (text: string, messageId: string) => void;
  onStopTTS?: () => void;
  isTTSPlaying?: boolean;
  isStreaming?: boolean;
  showTimestamp?: boolean;
}

// Helper function to parse message content and extract thinking section
const parseMessageContent = (content: string) => {
  const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/;
  const match = content.match(thinkingRegex);

  if (match) {
    return {
      thinking: match[1].trim(),
      response: content.replace(thinkingRegex, "").trim(),
    };
  }

  return {
    thinking: null,
    response: content,
  };
};

export default function MessageBubble({
  message,
  index,
  onPlayTTS,
  onStopTTS,
  isTTSPlaying = false,
  isStreaming = false,
  showTimestamp = true,
}: MessageBubbleProps) {
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const isUser = message.role === "user";
  const pseudoId = `session-message-${index}`;

  // Parse message content
  const parsedContent = parseMessageContent(message.content);

  const handleTTSPress = async () => {
    if (!onPlayTTS || !onStopTTS) return;

    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    if (isTTSPlaying) {
      onStopTTS();
    } else {
      onPlayTTS(parsedContent.response, pseudoId);
    }
  };

  const handleThinkingToggle = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setIsThinkingExpanded(!isThinkingExpanded);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <View
      style={[
        styles.container,
        isUser ? styles.userContainer : styles.assistantContainer,
        !isUser && styles.assistantBackground,
      ]}
    >
      <View style={styles.messageWrapper}>
        {/* Avatar */}
        <View
          style={[
            styles.avatar,
            isUser ? styles.userAvatar : styles.assistantAvatar,
          ]}
        >
          <Ionicons name={isUser ? "person" : "bulb"} size={16} color="white" />
        </View>

        {/* Message Content */}
        <View style={styles.contentWrapper}>
          {/* Role Label */}
          <Text style={styles.roleLabel}>{isUser ? "You" : "Assistant"}</Text>

          {/* Thinking Section - Only for assistant messages */}
          {!isUser && parsedContent.thinking && (
            <View style={styles.thinkingContainer}>
              <TouchableOpacity
                style={styles.thinkingHeader}
                onPress={handleThinkingToggle}
              >
                <View style={styles.thinkingIcon}>
                  <Ionicons name="bulb" size={12} color="#D97706" />
                </View>
                <Text style={styles.thinkingHeaderText}>
                  AI Thinking Process
                </Text>
                <View style={styles.thinkingBadge}>
                  <Text style={styles.thinkingBadgeText}>
                    {parsedContent.thinking.split(" ").length} words
                  </Text>
                </View>
                <Ionicons
                  name={isThinkingExpanded ? "chevron-down" : "chevron-forward"}
                  size={16}
                  color="#6B7280"
                />
              </TouchableOpacity>

              {isThinkingExpanded && (
                <View style={styles.thinkingContent}>
                  <View style={styles.thinkingTextContainer}>
                    <Text style={styles.thinkingText}>
                      {parsedContent.thinking}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          )}

          {/* Message Bubble */}
          <View
            style={[
              styles.bubble,
              isUser ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            {/* TTS Button for assistant messages */}
            {!isUser && onPlayTTS && onStopTTS && (
              <TouchableOpacity
                style={[
                  styles.ttsButton,
                  isTTSPlaying && styles.ttsButtonActive,
                ]}
                onPress={handleTTSPress}
              >
                <Ionicons
                  name={isTTSPlaying ? "stop" : "play"}
                  size={12}
                  color={isTTSPlaying ? "#EF4444" : "#6B7280"}
                />
              </TouchableOpacity>
            )}

            {/* Message Text */}
            <Text
              style={[
                styles.messageText,
                isUser ? styles.userText : styles.assistantText,
              ]}
            >
              {parsedContent.response || "Processing..."}
            </Text>

            {/* Footer with timestamp */}
            {showTimestamp && (
              <View style={styles.footer}>
                <Text
                  style={[
                    styles.timestamp,
                    isUser ? styles.userTimestamp : styles.assistantTimestamp,
                  ]}
                >
                  {formatTimestamp(message.timestamp)}
                </Text>
              </View>
            )}

            {/* TTS Playing Indicator */}
            {isTTSPlaying && (
              <View style={styles.ttsIndicator}>
                <View style={styles.soundWaveContainer}>
                  <View style={[styles.soundWave, styles.wave1]} />
                  <View style={[styles.soundWave, styles.wave2]} />
                  <View style={[styles.soundWave, styles.wave3]} />
                </View>
                <Text style={styles.ttsIndicatorText}>Speaking...</Text>
              </View>
            )}

            {/* Streaming Indicator */}
            {isStreaming && !isUser && (
              <View style={styles.streamingIndicator}>
                <View style={styles.streamingDots}>
                  <View style={[styles.streamingDot, { animationDelay: 0 }]} />
                  <View
                    style={[styles.streamingDot, { animationDelay: 150 }]}
                  />
                  <View
                    style={[styles.streamingDot, { animationDelay: 300 }]}
                  />
                </View>
                <Text style={styles.streamingText}>Assistant is typing...</Text>
              </View>
            )}
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  userContainer: {
    alignItems: "flex-end",
  },
  assistantContainer: {
    alignItems: "flex-start",
  },
  assistantBackground: {
    backgroundColor: "#F9FAFB",
  },
  messageWrapper: {
    flexDirection: "row",
    gap: 12,
    maxWidth: "90%",
    alignItems: "flex-start",
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
  userAvatar: {
    backgroundColor: "#6B7280",
  },
  assistantAvatar: {
    backgroundColor: "#1F2937",
  },
  contentWrapper: {
    flex: 1,
    gap: 8,
  },
  roleLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 4,
  },
  thinkingContainer: {
    backgroundColor: "#F3F4F6",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    overflow: "hidden",
    marginBottom: 8,
  },
  thinkingHeader: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    gap: 8,
  },
  thinkingIcon: {
    width: 20,
    height: 20,
    backgroundColor: "#FEF3C7",
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  thinkingHeaderText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#374151",
    flex: 1,
  },
  thinkingBadge: {
    backgroundColor: "#E5E7EB",
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  thinkingBadgeText: {
    fontSize: 12,
    color: "#6B7280",
  },
  thinkingContent: {
    paddingHorizontal: 12,
    paddingBottom: 12,
  },
  thinkingTextContainer: {
    backgroundColor: "#FEF9E7",
    borderWidth: 1,
    borderColor: "#F3E8FF",
    borderRadius: 8,
    padding: 12,
  },
  thinkingText: {
    fontSize: 13,
    fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
    lineHeight: 18,
    color: "#92400E",
  },
  bubble: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    position: "relative",
    ...Platform.select({
      ios: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  userBubble: {
    backgroundColor: "#3B82F6",
    borderBottomRightRadius: 6,
  },
  assistantBubble: {
    backgroundColor: "white",
    borderBottomLeftRadius: 6,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  ttsButton: {
    position: "absolute",
    top: -2,
    right: 8,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "rgba(107, 114, 128, 0.1)",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1,
  },
  ttsButtonActive: {
    backgroundColor: "rgba(239, 68, 68, 0.1)",
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: "white",
  },
  assistantText: {
    color: "#1F2937",
  },
  footer: {
    marginTop: 8,
    alignItems: "flex-end",
  },
  timestamp: {
    fontSize: 12,
    opacity: 0.7,
  },
  userTimestamp: {
    color: "white",
  },
  assistantTimestamp: {
    color: "#6B7280",
  },
  ttsIndicator: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#DBEAFE",
    backgroundColor: "#EFF6FF",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 6,
    gap: 8,
  },
  soundWaveContainer: {
    flexDirection: "row",
    gap: 2,
  },
  soundWave: {
    width: 2,
    backgroundColor: "#3B82F6",
    borderRadius: 1,
  },
  wave1: {
    height: 12,
  },
  wave2: {
    height: 8,
  },
  wave3: {
    height: 16,
  },
  ttsIndicatorText: {
    fontSize: 12,
    color: "#3B82F6",
    fontWeight: "500",
  },
  streamingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 12,
    gap: 8,
  },
  streamingDots: {
    flexDirection: "row",
    gap: 2,
  },
  streamingDot: {
    width: 4,
    height: 4,
    backgroundColor: "#9CA3AF",
    borderRadius: 2,
    opacity: 0.6,
  },
  streamingText: {
    fontSize: 12,
    color: "#6B7280",
    fontStyle: "italic",
  },
});
