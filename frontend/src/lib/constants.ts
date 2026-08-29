/**
 * Application-wide constants: API paths, error codes, and storage keys.
 * Centralized for consistency and easier updates.
 */

/** Key used to store the JWT access token in localStorage. */
export const TOKEN_STORAGE_KEY = 'giftgenius_access_token';

/** API path segments (relative to /api/v1). */
export const API_PATHS = {
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_PROFILE: '/auth/profile',
  CONTACTS: '/contacts',
  CONTACT_BY_ID: (id: string) => `/contacts/${id}`,
  MEMORIES_BY_CONTACT: (contactId: string) => `/contacts/${contactId}/memories`,
} as const;

/** Backend error codes for programmatic handling (see FRONTEND_INTEGRATION.md). */
export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  MISSING_TOKEN: 'MISSING_TOKEN',
  INVALID_TOKEN: 'INVALID_TOKEN',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  DUPLICATE_EMAIL: 'DUPLICATE_EMAIL',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  SYSTEM_ERROR: 'SYSTEM_ERROR',
} as const;

/** Error codes that require clearing token and redirecting to login. */
export const AUTH_ERROR_CODES = [
  ERROR_CODES.MISSING_TOKEN,
  ERROR_CODES.INVALID_TOKEN,
  ERROR_CODES.TOKEN_EXPIRED,
] as const;
