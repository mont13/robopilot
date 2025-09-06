import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LicenseModel, License } from '../schemas/License';
import { registerStore } from '../utils/StoreManager';

export interface AppPersistState {
  // Authentication state
  token: string | null;
  refreshToken: string | null;
  isUserLoggedIn: boolean;
  lastLoginTimestamp: number | null;

  // App preferences
  theme: 'light' | 'dark' | 'system';
  language: string;

  // License information
  license: License | null;

  // Token usage tracking
  tokenUsage: {
    currentUsage: number;
    usageLimit: number;
    resetDate?: string;
  };

  // Device/App info
  appVersion: string;
  deviceId: string | null;
  firstLaunch: boolean;
  onboardingCompleted: boolean;

  // Network/API settings
  apiBaseUrl: string;
  apiTimeout: number;

  // Privacy/Analytics
  analyticsEnabled: boolean;
  crashReportingEnabled: boolean;

  // UI state that should persist
  hasSeenWhatsNew: boolean;
  lastSeenVersion: string | null;

  // Actions
  setToken: (token: string | null) => void;
  setRefreshToken: (refreshToken: string | null) => void;
  setUserLoggedIn: (isLoggedIn: boolean) => void;
  setLastLoginTimestamp: (timestamp: number | null) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLanguage: (language: string) => void;
  setLicense: (license: License | null) => void;
  setTokenUsage: (usage: { currentUsage: number; usageLimit: number; resetDate?: string }) => void;
  setAppVersion: (version: string) => void;
  setDeviceId: (deviceId: string | null) => void;
  setFirstLaunch: (firstLaunch: boolean) => void;
  setOnboardingCompleted: (completed: boolean) => void;
  setApiBaseUrl: (url: string) => void;
  setApiTimeout: (timeout: number) => void;
  setAnalyticsEnabled: (enabled: boolean) => void;
  setCrashReportingEnabled: (enabled: boolean) => void;
  setHasSeenWhatsNew: (seen: boolean) => void;
  setLastSeenVersion: (version: string | null) => void;

  // Utility actions
  logout: () => Promise<void>;
  clearAllData: () => Promise<void>;
  reset: () => void;

  // Computed getters
  isTokenExpired: () => boolean;
  shouldShowOnboarding: () => boolean;
  shouldShowWhatsNew: () => boolean;
}

const initialState = {
  // Authentication
  token: null,
  refreshToken: null,
  isUserLoggedIn: false,
  lastLoginTimestamp: null,

  // App preferences
  theme: 'system' as const,
  language: 'en',

  // License
  license: null,
  tokenUsage: {
    currentUsage: 0,
    usageLimit: 0,
  },

  // Device/App info
  appVersion: '1.0.0',
  deviceId: null,
  firstLaunch: true,
  onboardingCompleted: false,

  // Network settings
  apiBaseUrl: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000',
  apiTimeout: 30000, // 30 seconds

  // Privacy
  analyticsEnabled: true,
  crashReportingEnabled: true,

  // UI state
  hasSeenWhatsNew: false,
  lastSeenVersion: null,
};

const useAppPersistStore = create<AppPersistState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Token management
      setToken: (token: string | null) => {
        set({ token });
        if (token) {
          set({ lastLoginTimestamp: Date.now() });
        }
      },

      setRefreshToken: (refreshToken: string | null) => {
        set({ refreshToken });
      },

      setUserLoggedIn: (isUserLoggedIn: boolean) => {
        set({ isUserLoggedIn });
        if (isUserLoggedIn && !get().lastLoginTimestamp) {
          set({ lastLoginTimestamp: Date.now() });
        }
      },

      setLastLoginTimestamp: (lastLoginTimestamp: number | null) => {
        set({ lastLoginTimestamp });
      },

      // App preferences
      setTheme: (theme: 'light' | 'dark' | 'system') => {
        set({ theme });
      },

      setLanguage: (language: string) => {
        set({ language });
      },

      // License management
      setLicense: (license: License | null) => {
        set({ license: license ? new LicenseModel(license) : null });
      },

      setTokenUsage: (tokenUsage) => {
        set({ tokenUsage });
      },

      // App info
      setAppVersion: (appVersion: string) => {
        set({ appVersion });
      },

      setDeviceId: (deviceId: string | null) => {
        set({ deviceId });
      },

      setFirstLaunch: (firstLaunch: boolean) => {
        set({ firstLaunch });
      },

      setOnboardingCompleted: (onboardingCompleted: boolean) => {
        set({ onboardingCompleted });
      },

      // Network settings
      setApiBaseUrl: (apiBaseUrl: string) => {
        set({ apiBaseUrl });
      },

      setApiTimeout: (apiTimeout: number) => {
        set({ apiTimeout });
      },

      // Privacy settings
      setAnalyticsEnabled: (analyticsEnabled: boolean) => {
        set({ analyticsEnabled });
      },

      setCrashReportingEnabled: (crashReportingEnabled: boolean) => {
        set({ crashReportingEnabled });
      },

      // UI state
      setHasSeenWhatsNew: (hasSeenWhatsNew: boolean) => {
        set({ hasSeenWhatsNew });
      },

      setLastSeenVersion: (lastSeenVersion: string | null) => {
        set({ lastSeenVersion });
      },

      // Utility actions
      logout: async () => {
        // Clear authentication data
        await AsyncStorage.multiRemove(['token', 'refreshToken']);

        set({
          token: null,
          refreshToken: null,
          isUserLoggedIn: false,
          lastLoginTimestamp: null,
          license: null,
          tokenUsage: {
            currentUsage: 0,
            usageLimit: 0,
          },
        });

        console.log('[AppPersistStore] User logged out');
      },

      clearAllData: async () => {
        // Clear all stored data
        try {
          await AsyncStorage.clear();
          set(initialState);
          console.log('[AppPersistStore] All data cleared');
        } catch (error) {
          console.error('[AppPersistStore] Error clearing data:', error);
        }
      },

      reset: () => {
        set(initialState);
      },

      // Computed getters
      isTokenExpired: () => {
        const { token, lastLoginTimestamp } = get();
        if (!token || !lastLoginTimestamp) return true;

        // Consider token expired after 24 hours (adjust as needed)
        const expirationTime = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        return Date.now() - lastLoginTimestamp > expirationTime;
      },

      shouldShowOnboarding: () => {
        const { firstLaunch, onboardingCompleted } = get();
        return firstLaunch && !onboardingCompleted;
      },

      shouldShowWhatsNew: () => {
        const { appVersion, lastSeenVersion, hasSeenWhatsNew } = get();
        return appVersion !== lastSeenVersion && !hasSeenWhatsNew;
      },
    }),
    {
      name: 'app-persist-store',
      storage: createJSONStorage(() => AsyncStorage),
      version: 1,
      // Persist everything except computed values
      partialize: (state) => {
        const { isTokenExpired, shouldShowOnboarding, shouldShowWhatsNew, ...persistedState } = state;
        return persistedState;
      },
      // Migration function for future versions
      migrate: (persistedState: any, version: number) => {
        if (version === 0) {
          // Migration from version 0 to 1
          return {
            ...persistedState,
            // Add any new fields with default values
            crashReportingEnabled: persistedState.crashReportingEnabled ?? true,
            hasSeenWhatsNew: persistedState.hasSeenWhatsNew ?? false,
          };
        }
        return persistedState;
      },
    }
  )
);

// Register the store in the registry
registerStore('AppPersistStore', useAppPersistStore);

export default useAppPersistStore;
