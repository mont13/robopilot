export interface BaseResponse {
  success: boolean;
  message?: string;
  timestamp?: string;
  requestId?: string;
}

export interface ErrorResponse extends BaseResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    field?: string;
  };
}

export interface SuccessResponse<T = any> extends BaseResponse {
  success: true;
  data: T;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    hasNext?: boolean;
    hasPrev?: boolean;
  };
}

export interface MeResponse {
  user: import('../User').User;
  authProviders: import('../AuthProvider').AuthProvider[];
}

export interface LicenseResponse {
  license: import('../License').License;
  usageStats?: {
    currentUsage: number;
    usageLimit: number;
    resetDate?: string;
  };
}

export interface AuthResponse {
  user: import('../User').User;
  token: string;
  refreshToken?: string;
  expiresIn?: number;
  authProviders: import('../AuthProvider').AuthProvider[];
}

export interface TokenResponse {
  token: string;
  refreshToken?: string;
  expiresIn?: number;
}

export type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse;

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationErrorResponse extends ErrorResponse {
  error: ErrorResponse['error'] & {
    validationErrors: ValidationError[];
  };
}

// Type guards
export function isSuccessResponse<T>(response: ApiResponse<T>): response is SuccessResponse<T> {
  return response.success === true;
}

export function isErrorResponse(response: ApiResponse): response is ErrorResponse {
  return response.success === false;
}

export function isValidationErrorResponse(response: ApiResponse): response is ValidationErrorResponse {
  return isErrorResponse(response) && 'validationErrors' in response.error;
}
