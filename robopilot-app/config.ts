import Constants from 'expo-constants';

// Environment configuration
export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    retries: 3,
  },

  // Authentication
  auth: {
    tokenKey: 'auth_token',
    refreshTokenKey: 'refresh_token',
    tokenExpirationTime: 24 * 60 * 60 * 1000, // 24 hours in milliseconds
  },

  // App Information
  app: {
    name: 'RoboPilot',
    version: Constants.expoConfig?.version || '1.0.0',
    buildNumber: Constants.expoConfig?.ios?.buildNumber || Constants.expoConfig?.android?.versionCode || '1',
    bundleId: Constants.expoConfig?.ios?.bundleIdentifier || Constants.expoConfig?.android?.package || 'com.robopilot.mobile',
  },

  // Storage
  storage: {
    maxLocalLogs: 1000,
    logRetentionDays: 30,
    maxCacheSize: 50 * 1024 * 1024, // 50MB
  },

  // Network
  network: {
    connectionTimeout: 10000, // 10 seconds
    readTimeout: 30000, // 30 seconds
    maxRetries: 3,
    retryDelay: 1000, // 1 second
  },

  // Features
  features: {
    enableAnalytics: true,
    enableCrashReporting: true,
    enablePushNotifications: true,
    enableBiometrics: true,
    enableOfflineMode: true,
  },

  // UI
  ui: {
    theme: {
      primary: '#007AFF',
      secondary: '#5856D6',
      success: '#4CAF50',
      warning: '#FF9500',
      error: '#F44336',
      info: '#17A2B8',
    },
    animations: {
      duration: 250,
      easing: 'ease-in-out',
    },
  },

  // Voice & Audio
  voice: {
    defaultLanguage: 'en-US',
    maxRecordingDuration: 60000, // 60 seconds
    audioQuality: 'high',
    enableVAD: true, // Voice Activity Detection
  },

  // Development
  development: {
    enableReduxLogger: __DEV__,
    enableNetworkLogger: __DEV__,
    showPerformanceMonitor: __DEV__,
    enableHotReload: __DEV__,
  },

  // Security
  security: {
    enableCertificatePinning: !__DEV__,
    enableJailbreakDetection: !__DEV__,
    enableTamperDetection: !__DEV__,
    biometricPromptTitle: 'Authenticate',
    biometricPromptSubtitle: 'Use your fingerprint or face to continue',
  },

  // Limits
  limits: {
    maxFileUploadSize: 10 * 1024 * 1024, // 10MB
    maxMessageLength: 4000,
    maxSessionDuration: 2 * 60 * 60 * 1000, // 2 hours
    rateLimitRequests: 100,
    rateLimitWindow: 60 * 1000, // 1 minute
  },

  // Logging
  logging: {
    level: __DEV__ ? 'debug' : 'info',
    enableRemoteLogging: true,
    enableLocalStorage: true,
    autoSendInterval: 30000, // 30 seconds
    maxRetries: 3,
  },

  // Platform specific
  ios: {
    statusBarStyle: 'dark-content',
    enableBackgroundAppRefresh: true,
  },

  android: {
    enableProguard: !__DEV__,
    targetSdkVersion: 34,
    minSdkVersion: 21,
  },
};

// Environment-specific overrides
if (__DEV__) {
  // Development overrides
  config.api.baseUrl = process.env.EXPO_PUBLIC_DEV_API_URL || config.api.baseUrl;
  config.logging.level = 'debug';
  config.features.enableAnalytics = false;
} else {
  // Production overrides
  config.api.baseUrl = process.env.EXPO_PUBLIC_PROD_API_URL || config.api.baseUrl;
  config.logging.level = 'info';
  config.development.enableReduxLogger = false;
  config.development.enableNetworkLogger = false;
}

// Validation
const validateConfig = () => {
  if (!config.api.baseUrl) {
    console.warn('API base URL is not configured');
  }

  if (!config.app.name) {
    console.warn('App name is not configured');
  }
};

// Run validation
validateConfig();

export default config;
