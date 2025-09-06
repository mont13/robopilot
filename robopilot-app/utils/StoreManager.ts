import { create, StateCreator } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Store registry to manage multiple stores
const storeRegistry = new Map<string, any>();

// Interface for store registration
export interface StoreConfig<T = any> {
  name: string;
  store: T;
  persist?: boolean;
  storage?: any;
  version?: number;
  migrate?: (persistedState: any, version: number) => any;
}

// Generic store creator with persistence support
export function createPersistedStore<T>(
  stateCreator: StateCreator<T>,
  config: {
    name: string;
    version?: number;
    migrate?: (persistedState: any, version: number) => any;
    blacklist?: (keyof T)[];
    whitelist?: (keyof T)[];
  }
) {
  return create<T>()(
    persist(stateCreator, {
      name: config.name,
      storage: createJSONStorage(() => AsyncStorage),
      version: config.version || 1,
      migrate: config.migrate,
      partialize: (state) => {
        if (config.whitelist) {
          // Only persist whitelisted keys
          const persistedState: Partial<T> = {};
          config.whitelist.forEach(key => {
            if (key in state) {
              persistedState[key] = state[key];
            }
          });
          return persistedState;
        }

        if (config.blacklist) {
          // Persist all keys except blacklisted ones
          const persistedState = { ...state };
          config.blacklist.forEach(key => {
            delete persistedState[key];
          });
          return persistedState;
        }

        return state;
      },
    })
  );
}

// Register a store in the global registry
export function registerStore<T>(name: string, store: T): void {
  if (storeRegistry.has(name)) {
    console.warn(`[StoreManager] Store '${name}' is already registered. Overwriting.`);
  }

  storeRegistry.set(name, store);
  console.log(`[StoreManager] Registered store: ${name}`);
}

// Get a store from the registry
export function getStore<T = any>(name: string): T {
  const store = storeRegistry.get(name);

  if (!store) {
    throw new Error(`[StoreManager] Store '${name}' not found. Make sure it's registered.`);
  }

  return store;
}

// Check if a store exists
export function hasStore(name: string): boolean {
  return storeRegistry.has(name);
}

// Get all registered store names
export function getStoreNames(): string[] {
  return Array.from(storeRegistry.keys());
}

// Unregister a store
export function unregisterStore(name: string): boolean {
  const result = storeRegistry.delete(name);
  if (result) {
    console.log(`[StoreManager] Unregistered store: ${name}`);
  }
  return result;
}

// Clear all stores from registry
export function clearRegistry(): void {
  storeRegistry.clear();
  console.log('[StoreManager] Cleared all stores from registry');
}

// Store persistence utilities
export class StorePersistence {
  // Clear persisted data for a specific store
  static async clearStoreData(storeName: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(storeName);
      console.log(`[StorePersistence] Cleared data for store: ${storeName}`);
    } catch (error) {
      console.error(`[StorePersistence] Failed to clear data for store ${storeName}:`, error);
    }
  }

  // Clear all persisted store data
  static async clearAllStoreData(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const storeKeys = keys.filter(key =>
        // Filter keys that look like store keys (you might need to adjust this)
        key.includes('store') || key.includes('Store') ||
        getStoreNames().some(storeName => key.includes(storeName))
      );

      if (storeKeys.length > 0) {
        await AsyncStorage.multiRemove(storeKeys);
        console.log(`[StorePersistence] Cleared ${storeKeys.length} persisted stores`);
      }
    } catch (error) {
      console.error('[StorePersistence] Failed to clear all store data:', error);
    }
  }

  // Get persisted data for a store
  static async getStoreData(storeName: string): Promise<any> {
    try {
      const data = await AsyncStorage.getItem(storeName);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error(`[StorePersistence] Failed to get data for store ${storeName}:`, error);
      return null;
    }
  }

  // Check if store has persisted data
  static async hasPersistedData(storeName: string): Promise<boolean> {
    try {
      const data = await AsyncStorage.getItem(storeName);
      return data !== null;
    } catch (error) {
      console.error(`[StorePersistence] Failed to check persisted data for store ${storeName}:`, error);
      return false;
    }
  }

  // Get all persisted store keys
  static async getPersistedStoreKeys(): Promise<string[]> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys.filter(key =>
        getStoreNames().some(storeName => key.includes(storeName))
      );
    } catch (error) {
      console.error('[StorePersistence] Failed to get persisted store keys:', error);
      return [];
    }
  }
}

// Store debugging utilities
export class StoreDebugger {
  // Log current state of a store
  static logStore(name: string): void {
    try {
      const store = getStore(name);
      if (typeof store.getState === 'function') {
        console.log(`[StoreDebugger] ${name} state:`, store.getState());
      } else {
        console.log(`[StoreDebugger] ${name}:`, store);
      }
    } catch (error) {
      console.error(`[StoreDebugger] Failed to log store ${name}:`, error);
    }
  }

  // Log all registered stores
  static logAllStores(): void {
    console.log('[StoreDebugger] All registered stores:');
    getStoreNames().forEach(name => {
      this.logStore(name);
    });
  }

  // Get store state as plain object
  static getStoreState(name: string): any {
    try {
      const store = getStore(name);
      return typeof store.getState === 'function' ? store.getState() : store;
    } catch (error) {
      console.error(`[StoreDebugger] Failed to get state for store ${name}:`, error);
      return null;
    }
  }

  // Export all store states
  static exportAllStates(): Record<string, any> {
    const states: Record<string, any> = {};
    getStoreNames().forEach(name => {
      states[name] = this.getStoreState(name);
    });
    return states;
  }
}

// Store hydration utilities
export class StoreHydrator {
  // Wait for a store to be hydrated (if it uses persistence)
  static async waitForHydration(storeName: string, timeout: number = 5000): Promise<boolean> {
    return new Promise((resolve) => {
      const store = getStore(storeName);

      if (!store || typeof store.getState !== 'function') {
        resolve(false);
        return;
      }

      const state = store.getState();

      // Check if store has hydration status
      if ('isHydrated' in state && state.isHydrated === true) {
        resolve(true);
        return;
      }

      // Set up timeout
      const timeoutId = setTimeout(() => {
        resolve(false);
      }, timeout);

      // Subscribe to store changes
      const unsubscribe = store.subscribe((newState: any) => {
        if ('isHydrated' in newState && newState.isHydrated === true) {
          clearTimeout(timeoutId);
          unsubscribe();
          resolve(true);
        }
      });
    });
  }

  // Wait for multiple stores to be hydrated
  static async waitForMultipleHydration(
    storeNames: string[],
    timeout: number = 5000
  ): Promise<Record<string, boolean>> {
    const promises = storeNames.map(async (name) => ({
      name,
      hydrated: await this.waitForHydration(name, timeout)
    }));

    const results = await Promise.all(promises);
    return results.reduce((acc, { name, hydrated }) => {
      acc[name] = hydrated;
      return acc;
    }, {} as Record<string, boolean>);
  }
}

export default {
  registerStore,
  getStore,
  hasStore,
  getStoreNames,
  unregisterStore,
  clearRegistry,
  createPersistedStore,
  StorePersistence,
  StoreDebugger,
  StoreHydrator,
};
