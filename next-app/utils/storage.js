/**
 * Safe storage utility for Next.js
 * Handles SSR gracefully and provides fallbacks when storage isn't available
 */

// Mock storage implementation when real storage isn't available
const createMockStorage = () => {
  const store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString(); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach(key => delete store[key]); },
    key: (i) => Object.keys(store)[i] || null,
    get length() { return Object.keys(store).length; }
  };
};

// Singleton to avoid recreating the mock on every import
let mockStorage = null;

/**
 * Safely get access to localStorage or a mock implementation
 */
export function getLocalStorage() {
  if (typeof window === 'undefined') {
    // Server-side rendering
    if (!mockStorage) mockStorage = createMockStorage();
    return mockStorage;
  }
  
  try {
    // Test if storage is actually available and working
    localStorage.setItem('__storage_test__', 'test');
    localStorage.removeItem('__storage_test__');
    return localStorage;
  } catch (e) {
    console.warn('localStorage not available:', e);
    if (!mockStorage) mockStorage = createMockStorage();
    return mockStorage;
  }
}

/**
 * Safely get access to sessionStorage or a mock implementation
 */
export function getSessionStorage() {
  if (typeof window === 'undefined') {
    // Server-side rendering
    if (!mockStorage) mockStorage = createMockStorage();
    return mockStorage;
  }
  
  try {
    // Test if storage is actually available and working
    sessionStorage.setItem('__storage_test__', 'test');
    sessionStorage.removeItem('__storage_test__');
    return sessionStorage;
  } catch (e) {
    console.warn('sessionStorage not available:', e);
    if (!mockStorage) mockStorage = createMockStorage();
    return mockStorage;
  }
}

/**
 * Safe wrapper for cookies
 */
export function getCookie(name) {
  if (typeof document === 'undefined') return null;
  
  try {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  } catch (e) {
    console.warn('Cookie access error:', e);
    return null;
  }
}

export function setCookie(name, value, days = 7) {
  if (typeof document === 'undefined') return false;
  
  try {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
    return true;
  } catch (e) {
    console.warn('Cookie set error:', e);
    return false;
  }
}

/**
 * Detect if storage is available in the current environment
 */
export function isStorageAvailable() {
  return typeof window !== 'undefined' && (() => {
    try {
      localStorage.setItem('__storage_test__', 'test');
      localStorage.removeItem('__storage_test__');
      return true;
    } catch (e) {
      return false;
    }
  })();
}
