import { useState, useCallback } from 'react';
import { Contact, Memory } from '@/types/contact';
import { get, post, del } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import { apiContactToContact, apiMemoryToMemory } from '@/lib/apiMappers';
import type { ApiContact, ApiContactsListData, ApiMemory, ApiMemoriesListData } from '@/lib/apiMappers';

export function useContacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [memoriesByContactId, setMemoriesByContactId] = useState<Record<string, Memory[]>>({});
  const [isLoading, setIsLoading] = useState(false);

  const fetchContacts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await get<ApiContactsListData>(API_PATHS.CONTACTS, true);
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
    const data = await get<ApiMemoriesListData>(API_PATHS.MEMORIES_BY_CONTACT(contactId), true);
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
      const data = await post<ApiContact>(API_PATHS.CONTACTS, body, true);
      const newContact = apiContactToContact(data);
      setContacts((prev) => [...prev, newContact]);
      return newContact;
    },
    []
  );

  /** No-op: backend has no contact update endpoint. */
  const updateContact = useCallback((_id: string, _updates: Partial<Contact>) => {}, []);

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
    const data = await post<ApiMemory>(API_PATHS.MEMORIES_BY_CONTACT(contactId), { content }, true);
    const memory = apiMemoryToMemory(data);
    setMemoriesByContactId((prev) => ({
      ...prev,
      [contactId]: [memory, ...(prev[contactId] ?? [])],
    }));
    return memory;
  }, []);

  /** No-op: backend has no memory delete endpoint. */
  const deleteMemory = useCallback((_contactId: string, _memoryId: string) => {}, []);

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
  };
}
