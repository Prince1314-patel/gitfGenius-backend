export interface Memory {
  id: string;
  content: string;
  createdAt: Date;
}

export interface Contact {
  id: string;
  name: string;
  relationship: string;
  birthday: Date;
  avatar?: string;
  memories: Memory[];
  createdAt: Date;
  updatedAt: Date;
}

export type RelationshipType = 
  | 'Family'
  | 'Friend'
  | 'Colleague'
  | 'Partner'
  | 'Acquaintance'
  | 'Other';

export const RELATIONSHIP_OPTIONS: RelationshipType[] = [
  'Family',
  'Friend',
  'Colleague',
  'Partner',
  'Acquaintance',
  'Other',
];
