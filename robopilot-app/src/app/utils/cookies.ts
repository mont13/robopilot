// Cookie utility functions for storing and retrieving user preferences

/**
 * Set a cookie with a given name, value and optional expiry days
 * @param name - Cookie name
 * @param value - Cookie value
 * @param days - Number of days until expiry (default: 30)
 */
export function setCookie(name: string, value: string, days: number = 30): void {
  const date = new Date();
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
  const expires = `expires=${date.toUTCString()}`;
  document.cookie = `${name}=${value};${expires};path=/`;
}

/**
 * Get a cookie value by name
 * @param name - Cookie name
 * @returns The cookie value or empty string if not found
 */
export function getCookie(name: string): string {
  const nameEQ = `${name}=`;
  const cookies = document.cookie.split(';');
  
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i];
    while (cookie.charAt(0) === ' ') {
      cookie = cookie.substring(1);
    }
    
    if (cookie.indexOf(nameEQ) === 0) {
      return cookie.substring(nameEQ.length);
    }
  }
  
  return '';
}

/**
 * Delete a cookie by name
 * @param name - Cookie name
 */
export function deleteCookie(name: string): void {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

/**
 * Store an object as a JSON string in a cookie
 * @param name - Cookie name
 * @param value - Object to store
 * @param days - Number of days until expiry (default: 30)
 */
export function setObjectCookie<T>(name: string, value: T, days: number = 30): void {
  try {
    const jsonValue = JSON.stringify(value);
    setCookie(name, jsonValue, days);
  } catch (error) {
    console.error(`Error storing object in cookie ${name}:`, error);
  }
}

/**
 * Get an object from a cookie
 * @param name - Cookie name
 * @param defaultValue - Default value to return if cookie not found
 * @returns The parsed object or defaultValue if not found/invalid
 */
export function getObjectCookie<T>(name: string, defaultValue: T): T {
  try {
    const cookieValue = getCookie(name);
    if (!cookieValue) return defaultValue;
    return JSON.parse(cookieValue) as T;
  } catch (error) {
    console.error(`Error parsing cookie ${name}:`, error);
    return defaultValue;
  }
}