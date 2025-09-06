import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

export enum HttpStatus {
  OK = 200,
  CREATED = 201,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  UNPROCESSABLE_ENTITY = 422,
  INTERNAL_SERVER_ERROR = 500,
}

export interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestOptions {
  token?: string;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

export class ApiClient {
  private client: AxiosInstance;
  private defaultTimeout = 30000; // 30 seconds
  private maxRetries = 3;

  constructor(config: ApiConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || this.defaultTimeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': this.getUserAgent(),
        ...config.headers,
      },
    });

    this.setupInterceptors();
  }

  private getUserAgent(): string {
    const version = '1.0.0'; // You can get this from package.json
    const platform = Platform.OS;
    const platformVersion = Platform.Version;
    return `RoboPilot/${version} (${platform} ${platformVersion})`;
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response ${response.status} for ${response.config.url}`);
        return response;
      },
      async (error: AxiosError) => {
        console.error(`[API] Response error ${error.response?.status} for ${error.config?.url}:`, error);

        // Handle token refresh for 401 errors
        if (error.response?.status === HttpStatus.UNAUTHORIZED) {
          const refreshToken = await AsyncStorage.getItem('refreshToken');
          if (refreshToken && error.config) {
            try {
              // Attempt to refresh token
              const newToken = await this.refreshToken(refreshToken);

              // Update the failed request with new token
              error.config.headers = {
                ...error.config.headers,
                Authorization: `Bearer ${newToken}`,
              };

              // Retry the original request
              return this.client.request(error.config);
            } catch (refreshError) {
              console.error('[API] Token refresh failed:', refreshError);
              // Clear stored tokens
              await AsyncStorage.multiRemove(['token', 'refreshToken']);
              throw error;
            }
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken(refreshToken: string): Promise<string> {
    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { token, refresh_token } = response.data;

    // Store new tokens
    await AsyncStorage.setItem('token', token);
    if (refresh_token) {
      await AsyncStorage.setItem('refreshToken', refresh_token);
    }

    return token;
  }

  private getConfig(options?: RequestOptions): AxiosRequestConfig {
    const config: AxiosRequestConfig = {
      timeout: options?.timeout || this.defaultTimeout,
      headers: {
        ...options?.headers,
      },
    };

    if (options?.token) {
      config.headers!.Authorization = `Bearer ${options.token}`;
    }

    return config;
  }

  private async retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    retries: number = this.maxRetries
  ): Promise<AxiosResponse<T>> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error as AxiosError)) {
        console.log(`[API] Retrying request, ${retries} attempts remaining`);
        await this.delay(1000 * (this.maxRetries - retries + 1)); // Exponential backoff
        return this.retryRequest(requestFn, retries - 1);
      }
      throw error;
    }
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry on network errors or 5xx server errors
    return !error.response || (error.response.status >= 500 && error.response.status < 600);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // HTTP Methods
  async get<T = any>(url: string, options?: RequestOptions): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    return this.retryRequest(() => this.client.get<T>(url, config), options?.retries);
  }

  async post<T = any>(url: string, data?: any, options?: RequestOptions): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    return this.retryRequest(() => this.client.post<T>(url, data, config), options?.retries);
  }

  async put<T = any>(url: string, data?: any, options?: RequestOptions): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    return this.retryRequest(() => this.client.put<T>(url, data, config), options?.retries);
  }

  async patch<T = any>(url: string, data?: any, options?: RequestOptions): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    return this.retryRequest(() => this.client.patch<T>(url, data, config), options?.retries);
  }

  async delete<T = any>(url: string, options?: RequestOptions): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    return this.retryRequest(() => this.client.delete<T>(url, config), options?.retries);
  }

  // Utility methods
  async uploadFile<T = any>(
    url: string,
    file: FormData,
    options?: RequestOptions
  ): Promise<AxiosResponse<T>> {
    const config = this.getConfig(options);
    config.headers!['Content-Type'] = 'multipart/form-data';

    return this.retryRequest(() => this.client.post<T>(url, file, config), options?.retries);
  }

  // Check if we're online/server is reachable
  async healthCheck(): Promise<boolean> {
    try {
      await this.get('/health', { timeout: 5000, retries: 1 });
      return true;
    } catch (error) {
      console.warn('[API] Health check failed:', error);
      return false;
    }
  }

  // Get current token from storage
  async getStoredToken(): Promise<string | null> {
    return AsyncStorage.getItem('token');
  }

  // Set authorization header for all future requests
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Clear authorization header
  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }

  // Update base URL
  updateBaseURL(baseURL: string): void {
    this.client.defaults.baseURL = baseURL;
  }
}

// Create a default instance
export const apiClient = new ApiClient({
  baseURL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000',
});

// Response validator utility
export class ResponseValidator {
  static validateResponse<T>(response: AxiosResponse<T>, context?: string): T {
    if (response.status >= 200 && response.status < 300) {
      return response.data;
    }

    const errorMessage = `${context ? `${context}: ` : ''}HTTP ${response.status}`;
    console.error('[ResponseValidator]', errorMessage, response.data);
    throw new Error(errorMessage);
  }

  static handleError(error: any, context?: string): never {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message;
      const status = error.response?.status;
      const errorMsg = `${context ? `${context}: ` : ''}${status ? `HTTP ${status} - ` : ''}${message}`;
      throw new Error(errorMsg);
    }

    throw error;
  }
}
