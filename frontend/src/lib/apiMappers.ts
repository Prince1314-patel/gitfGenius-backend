/**
 * API response types and mappers from backend shape to UI types.
 * Backend uses snake_case and optional fields; UI uses camelCase and Date.
 */

import type { Contact, Memory } from '@/types/contact';

/** User as returned by auth and profile endpoints. */
export interface ApiUser {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

/** Contact as returned by the API (single or in list). */
export interface ApiContact {
  id: string;
  name: string;
  relationship_type: string | null;
  birthday: string | null;
  created_at: string;
  memory_count?: number | null;
}

/** Memory as returned by the API. */
export interface ApiMemory {
  id: string;
  content: string;
  created_at: string;
}

/** Auth response data (login/register). */
export interface ApiAuthData {
  user: ApiUser;
  access_token: string;
  token_type: string;
}

/** Contacts list response data. */
export interface ApiContactsListData {
  contacts: ApiContact[];
}

/** Memories list response data. */
export interface ApiMemoriesListData {
  memories: ApiMemory[];
}

/** Gift recommendation response data. */
export interface ApiRecommendationsData {
  recommendations: string[];
}

export interface ApiDbSnapshotData {
  database_url: 'sqlite' | 'postgres';
  counts: {
    users: number;
    contacts: number;
    memories: number;
  };
  ai: {
    provider: 'openrouter' | 'local_fallback';
    model: string;
    configured: boolean;
  };
  users: Array<Pick<ApiUser, 'id' | 'email' | 'created_at'>>;
  contacts: ApiContact[];
  memories: ApiMemory[];
}

/**
 * Maps API contact to UI Contact. Uses created_at for both createdAt and updatedAt (API has no updatedAt).
 */
export function apiContactToContact(api: ApiContact): Contact {
  return {
    id: api.id,
    name: api.name,
    relationship: api.relationship_type ?? '',
    birthday: api.birthday ? new Date(api.birthday) : new Date(),
    createdAt: new Date(api.created_at),
    updatedAt: new Date(api.created_at),
    memories: [],
  };
}

/**
 * Maps API memory to UI Memory.
 */
export function apiMemoryToMemory(api: ApiMemory): Memory {
  return {
    id: api.id,
    content: api.content,
    createdAt: new Date(api.created_at),
  };
}

/**
 * Derives display name from API user: full_name or email local part.
 */
export function apiUserToDisplayName(api: ApiUser): string {
  if (api.full_name && api.full_name.trim()) {
    return api.full_name.trim();
  }
  const local = api.email.split('@')[0];
  return local ? local.charAt(0).toUpperCase() + local.slice(1) : 'User';
}
