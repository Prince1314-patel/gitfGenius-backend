import { useState, useCallback } from 'react';
import { Contact, Memory } from '@/types/contact';
import { get, post, put, del } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import { apiContactToContact, apiMemoryToMemory } from '@/lib/apiMappers';
import type { ApiContact, ApiContactsListData, ApiMemory, ApiMemoriesListData, ApiRecommendationsData } from '@/lib/apiMappers';

export function useContacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [memoriesByContactId, setMemoriesByContactId] = useState<Record<string, Memory[]>>({});
  const [recommendationsByContactId, setRecommendationsByContactId] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(false);

  const fetchContacts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await get<ApiContactsListData>(API_PATHS.CONTACTS);
      setContacts((data.contacts ?? []).map(apiContactToContact));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getContact = useCallback(
    (id: string): Contact | undefined => {
      const contact = contacts.find((c) => c.id === id);
      if (!contact) return undefined;
      const memories = memoriesByContactId[id] ?? [];
      return { ...contact, memories };
    },
    [contacts, memoriesByContactId]
  );

  const fetchMemories = useCallback(async (contactId: string): Promise<Memory[]> => {
    const data = await get<ApiMemoriesListData>(API_PATHS.MEMORIES_BY_CONTACT(contactId));
    const memories = (data.memories ?? []).map(apiMemoryToMemory);
    setMemoriesByContactId((prev) => ({ ...prev, [contactId]: memories }));
    return memories;
  }, []);

  const addContact = useCallback(
    async (
      contact: Omit<Contact, 'id' | 'memories' | 'createdAt' | 'updatedAt'> & { birthday?: Date | string }
    ) => {
      const body: { name: string; relationship_type?: string; birthday?: string } = {
        name: contact.name,
      };
      if (contact.relationship) body.relationship_type = contact.relationship;
      if (contact.birthday != null && String(contact.birthday) !== '') {
        body.birthday =
          contact.birthday instanceof Date
            ? contact.birthday.toISOString().split('T')[0]
            : String(contact.birthday).slice(0, 10);
      }
      const data = await post<ApiContact>(API_PATHS.CONTACTS, body);
      const newContact = apiContactToContact(data);
      setContacts((prev) => [...prev, newContact]);
      return newContact;
    },
    []
  );

  const updateContact = useCallback(async (id: string, updates: Partial<Contact>) => {
    const body: { name?: string; relationship_type?: string; birthday?: string } = {};
    if (updates.name !== undefined) body.name = updates.name;
    if (updates.relationship !== undefined) body.relationship_type = updates.relationship;
    if (updates.birthday !== undefined) body.birthday = updates.birthday.toISOString().slice(0, 10);
    const data = await put<ApiContact>(API_PATHS.CONTACT_BY_ID(id), body);
    const updated = apiContactToContact(data);
    setContacts((prev) => prev.map((contact) => (contact.id === id ? updated : contact)));
    return updated;
  }, []);

  const deleteContact = useCallback(async (id: string) => {
    await del(API_PATHS.CONTACT_BY_ID(id));
    setContacts((prev) => prev.filter((c) => c.id !== id));
    setMemoriesByContactId((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const addMemory = useCallback(async (contactId: string, content: string): Promise<Memory> => {
    const data = await post<ApiMemory>(API_PATHS.MEMORIES_BY_CONTACT(contactId), { content });
    const memory = apiMemoryToMemory(data);
    setMemoriesByContactId((prev) => ({
      ...prev,
      [contactId]: [memory, ...(prev[contactId] ?? [])],
    }));
    return memory;
  }, []);

  const fetchRecommendations = useCallback(async (contactId: string): Promise<string[]> => {
    const data = await get<ApiRecommendationsData>(API_PATHS.RECOMMENDATIONS_BY_CONTACT(contactId));
    setRecommendationsByContactId((prev) => ({ ...prev, [contactId]: data.recommendations ?? [] }));
    return data.recommendations ?? [];
  }, []);

  const deleteMemory = useCallback(async (contactId: string, memoryId: string) => {
    await del(API_PATHS.MEMORY_BY_ID(contactId, memoryId));
    setMemoriesByContactId((prev) => ({
      ...prev,
      [contactId]: (prev[contactId] ?? []).filter((memory) => memory.id !== memoryId),
    }));
  }, []);

  return {
    contacts,
    isLoading,
    fetchContacts,
    getContact,
    fetchMemories,
    addContact,
    updateContact,
    deleteContact,
    addMemory,
    deleteMemory,
    fetchRecommendations,
    recommendationsByContactId,
  };
}
