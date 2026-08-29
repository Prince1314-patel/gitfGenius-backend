/**
 * Application-wide constants: API paths, error codes, and storage keys.
 * Centralized for consistency and easier updates.
 */

/** API path segments (relative to /api/v1). */
export const API_PATHS = {
  CONTACTS: '/contacts',
  CONTACT_BY_ID: (id: string) => `/contacts/${id}`,
  MEMORIES_BY_CONTACT: (contactId: string) => `/contacts/${contactId}/memories`,
  MEMORY_BY_ID: (contactId: string, memoryId: string) => `/contacts/${contactId}/memories/${memoryId}`,
  RECOMMENDATIONS_BY_CONTACT: (contactId: string) => `/contacts/${contactId}/recommendations`,
  DEV_DB_SNAPSHOT: '/dev/db-snapshot',
} as const;
