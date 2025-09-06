import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { AuthProvider, AuthProviderModel } from "../schemas/AuthProvider";
import { License, LicenseModel } from "../schemas/License";
import { LicenseResponse, MeResponse } from "../schemas/responses/ApiResponse";
import { User, UserModel } from "../schemas/User";
import { apiClient, ResponseValidator } from "../utils/ApiClient";
import { getStore, registerStore } from "../utils/StoreManager";

export interface UserState {
  // User data
  user: User | null;
  authProviders: AuthProvider[];
  license: License | null;

  // UI state
  isLoading: boolean;
  isHydrated: boolean;
  hasActiveAuthProviderConnection: boolean;
  showAuthProviderConnectionError: boolean;

  // Token usage tracking
  tokenUsage: {
    currentUsage: number;
    usageLimit: number;
    resetDate?: string;
  };

  // Actions for user management
  setUserData: (user: User | null) => Promise<void>;
  setAuthProviders: (authProviders: AuthProvider[]) => void;
  setLicense: (license: License | null) => void;
  setTokenUsage: (usage: {
    currentUsage: number;
    usageLimit: number;
    resetDate?: string;
  }) => void;

  // User operations
  updateSettings: (
    keyOrSettings: keyof User | Partial<User>,
    value?: any,
  ) => Promise<void>;
  updateUser: (data: User, isSilent?: boolean) => Promise<void>;
  refreshToken: (token: string) => Promise<void>;
  resetPassword: (email: string) => Promise<boolean>;
  deleteAccount: () => Promise<void>;

  // Auth provider operations
  refreshAuthProviders: () => void;
  setAuthProviderConnectionError: () => void;
  resetAuthProviderConnectionError: () => void;
  showAuthProviderConnectionErrorModal: () => boolean;

  // License operations
  getUserLicense: () => Promise<void>;
  getUserLicenseStats: () => Promise<void>;

  // Utility actions
  reset: () => void;
  setLoading: (loading: boolean) => void;
  setHydrated: (hydrated: boolean) => void;
}

const initialState = {
  user: null,
  authProviders: [],
  license: null,
  isLoading: false,
  isHydrated: false,
  hasActiveAuthProviderConnection: false,
  showAuthProviderConnectionError: false,
  tokenUsage: {
    currentUsage: 0,
    usageLimit: 0,
  },
};

const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // User data setters
      setUserData: async (user: User | null) => {
        set({ user: user ? new UserModel(user) : null });
      },

      setAuthProviders: (authProviders: AuthProvider[]) => {
        const providers = authProviders.map(
          (provider) => new AuthProviderModel(provider),
        );

        // Check if at least one auth provider has the user logged in
        const hasActiveConnection = providers.some(
          (provider) => provider.userIsLogged,
        );

        set({
          authProviders: providers,
          hasActiveAuthProviderConnection:
            hasActiveConnection || providers.length === 0,
        });

        // Auto-reset error state if we now have a valid connection
        if (hasActiveConnection && get().showAuthProviderConnectionError) {
          get().resetAuthProviderConnectionError();
        }
      },

      setLicense: (license: License | null) => {
        set({ license: license ? new LicenseModel(license) : null });
      },

      setTokenUsage: (usage) => {
        set({ tokenUsage: usage });
      },

      // Auth provider connection modal methods
      setAuthProviderConnectionError: () => {
        set({ showAuthProviderConnectionError: true });
      },

      resetAuthProviderConnectionError: () => {
        set({ showAuthProviderConnectionError: false });
      },

      showAuthProviderConnectionErrorModal: () => {
        const { user, authProviders, hasActiveAuthProviderConnection } = get();
        if (
          user !== null &&
          Array.isArray(authProviders) &&
          authProviders.length > 0 &&
          !hasActiveAuthProviderConnection
        ) {
          set({ showAuthProviderConnectionError: true });
          return true;
        }
        return false;
      },

      // Token refresh
      refreshToken: async (refreshToken: string) => {
        set({ isLoading: true });

        try {
          const response = await apiClient.post<MeResponse>(
            "/auth/me",
            {},
            {
              token: refreshToken,
            },
          );

          const data = ResponseValidator.validateResponse(
            response,
            "Refresh token",
          );

          if (data) {
            get().setAuthProviders(data.authProviders);
            const user = new UserModel(data.user);
            set({ user });

            // Don't show error if we have successful response with auth providers
            if (data.authProviders.some((provider) => provider.userIsLogged)) {
              get().resetAuthProviderConnectionError();
            }
          }
        } catch (error: any) {
          console.log("[UserStore] Token refresh failed:", error);

          // Check error type to decide action
          const isAuthError =
            error?.response?.status === 401 ||
            error?.response?.status === 403 ||
            error?.response?.status === 422;

          const isNetworkError =
            !error?.response ||
            error?.code === "NETWORK_ERROR" ||
            error?.message?.includes("Network Error");

          if (isAuthError) {
            // Auth error - logout immediately
            console.log("[UserStore] Auth error detected, logging out user");
            const useAppPersistStore = getStore("AppPersistStore");
            set({ user: null });
            useAppPersistStore.setState({
              token: null,
              isUserLoggedIn: false,
            });
          } else if (isNetworkError) {
            // Network error - keep user logged in
            console.log("[UserStore] Network error, keeping user logged in");
          } else {
            // Unknown error - logout for safety
            console.log("[UserStore] Unknown error, logging out user");
            const useAppPersistStore = getStore("AppPersistStore");
            set({ user: null });
            useAppPersistStore.setState({
              token: null,
              isUserLoggedIn: false,
            });
          }

          // Log the error
          try {
            const useLogStore = getStore("LogStore");
            await useLogStore
              .getState()
              .sendLog(
                "error",
                `Error refreshing token: ${
                  error instanceof Error ? error.message : "Unknown error"
                }`,
              );
          } catch (logError) {
            console.warn("[UserStore] Failed to log error:", logError);
          }
        } finally {
          set({ isLoading: false });
        }
      },

      // Update user settings
      updateSettings: async <K extends keyof User>(
        keyOrSettings: K | Partial<User>,
        value?: User[K],
      ): Promise<void> => {
        const user = get().user;

        if (!user) return;

        let cloneUser = new UserModel(user).clone();

        // Handle case where first argument is an object with multiple settings
        if (typeof keyOrSettings === "object" && value === undefined) {
          // Update multiple settings at once
          console.log("[UserStore] Updating multiple settings:", keyOrSettings);
          Object.entries(keyOrSettings).forEach(([key, val]) => {
            if (Object.keys(user).includes(key) && val !== undefined) {
              (cloneUser as any)[key] = val;
            }
          });
        }
        // Handle traditional single key-value update
        else if (typeof keyOrSettings === "string") {
          const key = keyOrSettings;
          console.log("[UserStore] Updating setting:", key, value);

          if (!Object.keys(user).includes(key) || value === undefined) return;

          cloneUser[key] = value;
        }

        // First update the local user state immediately for fast UI response
        set({ user: cloneUser });

        // Then send the update to the server
        try {
          await get().updateUser(cloneUser, true);
        } catch (error) {
          console.error("[UserStore] Error updating settings:", error);
          // Revert the local state in case of error
          set({ user: new UserModel(user) });
        }
      },

      // Update user on server
      updateUser: async (newUser: User, silent: boolean = false) => {
        const token = await AsyncStorage.getItem("token");
        const user = get().user;

        if (!token || !user) return;

        if (!silent) {
          set({ isLoading: true });
        }

        try {
          const response = await apiClient.put<MeResponse>(
            `/auth/user/${user.id}`,
            newUser,
            {
              token,
            },
          );

          const data = ResponseValidator.validateResponse(
            response,
            "Update user",
          );

          if (data) {
            await get().setUserData(new UserModel(data.user));
            get().setAuthProviders(data.authProviders);
            set({ user: new UserModel(data.user) });
          }
        } catch (error) {
          try {
            const useLogStore = getStore("LogStore");
            await useLogStore
              .getState()
              .sendLog(
                "error",
                `Error updating user: ${
                  error instanceof Error ? error.message : "Unknown error"
                }`,
              );
          } catch (logError) {
            console.warn("[UserStore] Failed to log error:", logError);
          }
        } finally {
          if (!silent) {
            set({ isLoading: false });
          }
        }
      },

      // Reset password
      resetPassword: async (email: string) => {
        set({ isLoading: true });

        try {
          const response = await apiClient.post("/auth/reset-password", {
            email,
          });
          const data = ResponseValidator.validateResponse(
            response,
            "Reset password",
          );
          return !!data;
        } catch (error) {
          try {
            const useLogStore = getStore("LogStore");
            await useLogStore
              .getState()
              .sendLog(
                "error",
                `Error resetting password: ${
                  error instanceof Error ? error.message : "Unknown error"
                }`,
              );
          } catch (logError) {
            console.warn("[UserStore] Failed to log error:", logError);
          }
          return false;
        } finally {
          set({ isLoading: false });
        }
      },

      // Refresh auth providers
      refreshAuthProviders: () => {
        AsyncStorage.getItem("token").then((token) => {
          if (token) get().refreshToken(token);
        });
      },

      // Get user license
      getUserLicense: async () => {
        const token = await AsyncStorage.getItem("token");
        console.log("[UserStore] Getting user license...");

        if (!token) {
          console.log("[UserStore] No token found, aborting");
          return;
        }

        set({ isLoading: true });

        try {
          console.log("[UserStore] Making API request for license");
          const response = await apiClient.get<LicenseResponse>(
            "/auth/licenses/user",
            { token },
          );

          console.log("[UserStore] License response:", response);

          if (response.status === 200 && response.data) {
            const result = response.data;
            get().setLicense(new LicenseModel(result.license));
          }
        } catch (error) {
          console.error("[UserStore] Error getting user license:", error);
        } finally {
          console.log("[UserStore] License check completed");
          set({ isLoading: false });
        }
      },

      // Get user license stats
      getUserLicenseStats: async () => {
        const token = await AsyncStorage.getItem("token");
        console.log("[UserStore] Getting user license stats...");

        if (!token) {
          console.log("[UserStore] No token found, aborting");
          return;
        }

        set({ isLoading: true });

        try {
          console.log("[UserStore] Making API request for license stats");
          const response = await apiClient.get<LicenseResponse>(
            "/auth/licenses/user/stats",
            { token },
          );

          console.log("[UserStore] License stats response:", response);

          if (response.status === 200 && response.data) {
            const result = response.data;

            console.log("[UserStore] License stats:", result);

            // Update license data
            if (result.license) {
              console.log("[UserStore] Updating license data:", result.license);
              get().setLicense(new LicenseModel(result.license));
            }

            // Update usage stats if available
            if (result.usageStats) {
              console.log(
                "[UserStore] Updating license usage stats:",
                result.usageStats,
              );
              get().setTokenUsage({
                currentUsage: result.usageStats.currentUsage,
                usageLimit: result.usageStats.usageLimit,
                resetDate: result.usageStats.resetDate,
              });
            }
          }
        } catch (error) {
          console.error("[UserStore] Error getting user license stats:", error);
        } finally {
          console.log("[UserStore] License stats check completed");
          set({ isLoading: false });
        }
      },

      // Delete account
      deleteAccount: async () => {
        const token = await AsyncStorage.getItem("token");
        const user = get().user;

        if (!token || !user) return;

        set({ isLoading: true });

        try {
          await apiClient.delete(`/auth/user/${user.id}`, { token });

          set({ user: null });
          await AsyncStorage.multiRemove(["token", "refreshToken"]);
        } catch (error) {
          console.error("Error deleting account:", error);
        } finally {
          set({ isLoading: false });
        }
      },

      // Utility actions
      reset: () => {
        set(initialState);
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setHydrated: (hydrated: boolean) => {
        set({ isHydrated: hydrated });
      },
    }),
    {
      name: "user-store",
      storage: createJSONStorage(() => AsyncStorage),
      version: 1,
      // Only persist essential user data, not UI state
      partialize: (state) => ({
        user: state.user,
        authProviders: state.authProviders,
        license: state.license,
        tokenUsage: state.tokenUsage,
        hasActiveAuthProviderConnection: state.hasActiveAuthProviderConnection,
      }),
      // Set hydration flag when store is rehydrated
      onRehydrateStorage: () => (state) => {
        state?.setHydrated(true);
      },
    },
  ),
);

// Register the store in the registry
registerStore("UserStore", useUserStore);

export default useUserStore;
