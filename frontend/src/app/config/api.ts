/**
 * API configuration for the application
 */

// Use the environment variable NEXT_PUBLIC_API_URL if defined,
// otherwise fall back to localhost for development
export const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8009";
