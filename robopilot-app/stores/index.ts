// Main store exports
export { default as useUserStore } from './useUserStore';
export { default as useAppPersistStore } from './useAppPersistStore';
export { default as useLogStore } from './useLogStore';

// Store types
export type { UserState } from './useUserStore';
export type { AppPersistState } from './useAppPersistStore';
export type { LogState, LogEntry } from './useLogStore';

// Store utilities
export {
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
} from '../utils/StoreManager';

// Schema exports for convenience
export { UserModel } from '../schemas/User';
export { AuthProviderModel } from '../schemas/AuthProvider';
export { LicenseModel } from '../schemas/License';

export type { User } from '../schemas/User';
export type { AuthProvider } from '../schemas/AuthProvider';
export type { License } from '../schemas/License';

// Response types
export type {
  BaseResponse,
  ErrorResponse,
  SuccessResponse,
  MeResponse,
  LicenseResponse,
  AuthResponse,
  TokenResponse,
  ApiResponse,
  ValidationError,
  ValidationErrorResponse,
} from '../schemas/responses/ApiResponse';

// API client
export { apiClient, ResponseValidator } from '../utils/ApiClient';
export type { ApiConfig, RequestOptions } from '../utils/ApiClient';

// Re-export useful utilities
export { startAutoSend, stopAutoSend } from './useLogStore';
