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
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
}

export function getStorageItem(key, defaultValue = null) {
  if (!isStorageAvailable()) {
    return defaultValue;
  }
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (e) {
    console.warn(`Error reading ${key} from storage:`, e);
    return defaultValue;
  }
}

export function setStorageItem(key, value) {
  if (!isStorageAvailable()) {
    return false;
  }
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.warn(`Error writing ${key} to storage:`, e);
    return false;
  }
}

export function removeStorageItem(key) {
  if (!isStorageAvailable()) {
    return false;
  }
  
  try {
    localStorage.removeItem(key);
    return true;
  } catch (e) {
    console.warn(`Error removing ${key} from storage:`, e);
    return false;
  }
}
