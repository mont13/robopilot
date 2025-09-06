import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { apiClient } from "../utils/ApiClient";
import { registerStore } from "../utils/StoreManager";

export interface LogEntry {
  id: string;
  level: "debug" | "info" | "warn" | "error" | "fatal";
  message: string;
  timestamp: string;
  context?: string;
  userId?: string;
  deviceInfo?: {
    platform: string;
    version: string;
    model?: string;
  };
  appInfo?: {
    version: string;
    buildNumber?: string;
  };
  metadata?: Record<string, any>;
  stackTrace?: string;
  sent: boolean;
  retryCount: number;
}

export interface LogState {
  // Local logs
  logs: LogEntry[];
  maxLocalLogs: number;

  // Sending state
  isSending: boolean;
  lastSentTimestamp: number | null;

  // Settings
  logLevel: "debug" | "info" | "warn" | "error" | "fatal";
  enableRemoteLogging: boolean;
  enableLocalStorage: boolean;
  autoSendInterval: number; // milliseconds
  maxRetries: number;

  // Actions
  addLog: (
    level: LogEntry["level"],
    message: string,
    context?: string,
    metadata?: any,
  ) => void;
  sendLog: (
    level: LogEntry["level"],
    message: string,
    context?: string,
    metadata?: any,
  ) => Promise<void>;
  sendPendingLogs: () => Promise<void>;
  clearLogs: () => void;
  clearSentLogs: () => void;

  // Settings
  setLogLevel: (level: LogEntry["level"]) => void;
  setEnableRemoteLogging: (enabled: boolean) => void;
  setEnableLocalStorage: (enabled: boolean) => void;
  setAutoSendInterval: (interval: number) => void;
  setMaxRetries: (maxRetries: number) => void;

  // Utility
  getPendingLogs: () => LogEntry[];
  getLogsByLevel: (level: LogEntry["level"]) => LogEntry[];
  getLogsByDateRange: (startDate: Date, endDate: Date) => LogEntry[];
  exportLogs: () => string;

  // Internal
  setSending: (sending: boolean) => void;
  setLastSentTimestamp: (timestamp: number) => void;
}

const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  fatal: 4,
};

const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const getDeviceInfo = () => {
  const { Platform } = require("react-native");
  return {
    platform: Platform.OS,
    version: Platform.Version.toString(),
  };
};

const getAppInfo = () => {
  // You can get these from your app.json or package.json
  return {
    version: "1.0.0",
    buildNumber: "1",
  };
};

const shouldLogLevel = (
  currentLevel: LogEntry["level"],
  targetLevel: LogEntry["level"],
): boolean => {
  return LOG_LEVELS[targetLevel] >= LOG_LEVELS[currentLevel];
};

const useLogStore = create<LogState>()(
  persist(
    (set, get) => ({
      // Initial state
      logs: [],
      maxLocalLogs: 1000,
      isSending: false,
      lastSentTimestamp: null,
      logLevel: "info",
      enableRemoteLogging: true,
      enableLocalStorage: true,
      autoSendInterval: 30000, // 30 seconds
      maxRetries: 3,

      // Add log entry
      addLog: (
        level: LogEntry["level"],
        message: string,
        context?: string,
        metadata?: any,
      ) => {
        const { logLevel, enableLocalStorage, maxLocalLogs } = get();

        // Check if we should log this level
        if (!shouldLogLevel(logLevel, level)) {
          return;
        }

        const logEntry: LogEntry = {
          id: generateId(),
          level,
          message,
          timestamp: new Date().toISOString(),
          context,
          deviceInfo: getDeviceInfo(),
          appInfo: getAppInfo(),
          metadata,
          sent: false,
          retryCount: 0,
        };

        // Add stack trace for errors
        if (level === "error" || level === "fatal") {
          logEntry.stackTrace = new Error().stack;
        }

        if (enableLocalStorage) {
          set((state) => {
            const newLogs = [...state.logs, logEntry];

            // Keep only the most recent logs
            if (newLogs.length > maxLocalLogs) {
              newLogs.splice(0, newLogs.length - maxLocalLogs);
            }

            return { logs: newLogs };
          });
        }

        // Console log for development
        if (__DEV__) {
          const contextStr = context ? `[${context}] ` : "";
          const metadataStr = metadata ? ` ${JSON.stringify(metadata)}` : "";
          console.log(
            `[${level.toUpperCase()}] ${contextStr}${message}${metadataStr}`,
          );
        }
      },

      // Send log immediately
      sendLog: async (
        level: LogEntry["level"],
        message: string,
        context?: string,
        metadata?: any,
      ) => {
        const { enableRemoteLogging, addLog } = get();

        // Always add to local logs first
        addLog(level, message, context, metadata);

        if (!enableRemoteLogging) {
          return;
        }

        const logEntry: LogEntry = {
          id: generateId(),
          level,
          message,
          timestamp: new Date().toISOString(),
          context,
          deviceInfo: getDeviceInfo(),
          appInfo: getAppInfo(),
          metadata,
          sent: false,
          retryCount: 0,
        };

        try {
          await apiClient.post("/api/logs", {
            logs: [logEntry],
          });

          // Mark as sent in local storage
          set((state) => ({
            logs: state.logs.map((log) =>
              log.id === logEntry.id ? { ...log, sent: true } : log,
            ),
          }));
        } catch (error) {
          console.warn("[LogStore] Failed to send log immediately:", error);
          // The log is already in local storage, it will be retried later
        }
      },

      // Send all pending logs
      sendPendingLogs: async () => {
        const { logs, enableRemoteLogging, isSending, maxRetries } = get();

        if (!enableRemoteLogging || isSending) {
          return;
        }

        const pendingLogs = logs.filter(
          (log) => !log.sent && log.retryCount < maxRetries,
        );

        if (pendingLogs.length === 0) {
          return;
        }

        set({ isSending: true });

        try {
          await apiClient.post("/api/logs", {
            logs: pendingLogs,
          });

          // Mark all as sent
          set((state) => ({
            logs: state.logs.map((log) =>
              pendingLogs.find((pending) => pending.id === log.id)
                ? { ...log, sent: true }
                : log,
            ),
            lastSentTimestamp: Date.now(),
          }));

          console.log(
            `[LogStore] Successfully sent ${pendingLogs.length} logs`,
          );
        } catch (error) {
          console.warn("[LogStore] Failed to send pending logs:", error);

          // Increment retry count for failed logs
          set((state) => ({
            logs: state.logs.map((log) =>
              pendingLogs.find((pending) => pending.id === log.id)
                ? { ...log, retryCount: log.retryCount + 1 }
                : log,
            ),
          }));
        } finally {
          set({ isSending: false });
        }
      },

      // Clear all logs
      clearLogs: () => {
        set({ logs: [] });
      },

      // Clear only sent logs
      clearSentLogs: () => {
        set((state) => ({
          logs: state.logs.filter((log) => !log.sent),
        }));
      },

      // Settings
      setLogLevel: (logLevel) => {
        set({ logLevel });
      },

      setEnableRemoteLogging: (enableRemoteLogging) => {
        set({ enableRemoteLogging });
      },

      setEnableLocalStorage: (enableLocalStorage) => {
        set({ enableLocalStorage });
      },

      setAutoSendInterval: (autoSendInterval) => {
        set({ autoSendInterval });
      },

      setMaxRetries: (maxRetries) => {
        set({ maxRetries });
      },

      // Utility methods
      getPendingLogs: () => {
        const { logs, maxRetries } = get();
        return logs.filter((log) => !log.sent && log.retryCount < maxRetries);
      },

      getLogsByLevel: (level: LogEntry["level"]) => {
        return get().logs.filter((log) => log.level === level);
      },

      getLogsByDateRange: (startDate: Date, endDate: Date) => {
        return get().logs.filter((log) => {
          const logDate = new Date(log.timestamp);
          return logDate >= startDate && logDate <= endDate;
        });
      },

      exportLogs: () => {
        const { logs } = get();
        return JSON.stringify(logs, null, 2);
      },

      // Internal methods
      setSending: (isSending) => {
        set({ isSending });
      },

      setLastSentTimestamp: (lastSentTimestamp) => {
        set({ lastSentTimestamp });
      },
    }),
    {
      name: "log-store",
      storage: createJSONStorage(() => AsyncStorage),
      version: 1,
      // Only persist logs and settings, not sending state
      partialize: (state) => ({
        logs: state.logs,
        logLevel: state.logLevel,
        enableRemoteLogging: state.enableRemoteLogging,
        enableLocalStorage: state.enableLocalStorage,
        autoSendInterval: state.autoSendInterval,
        maxRetries: state.maxRetries,
        lastSentTimestamp: state.lastSentTimestamp,
      }),
    },
  ),
);

// Register the store in the registry
registerStore("LogStore", useLogStore);

// Auto-send logs periodically
let autoSendInterval: NodeJS.Timeout | null = null;

const startAutoSend = () => {
  if (autoSendInterval) {
    clearInterval(autoSendInterval);
  }

  const store = useLogStore.getState();

  autoSendInterval = setInterval(async () => {
    const currentStore = useLogStore.getState();
    if (currentStore.enableRemoteLogging && !currentStore.isSending) {
      await currentStore.sendPendingLogs();
    }
  }, store.autoSendInterval);
};

const stopAutoSend = () => {
  if (autoSendInterval) {
    clearInterval(autoSendInterval);
    autoSendInterval = null;
  }
};

// Start auto-send when store is created
if (useLogStore.getState().enableRemoteLogging) {
  startAutoSend();
}

// Export utility functions
export { startAutoSend, stopAutoSend };

export default useLogStore;
