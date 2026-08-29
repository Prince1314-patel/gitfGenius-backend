import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Pencil, Sparkles, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { AvatarInitials } from '@/components/AvatarInitials';
import { ContactModal } from '@/components/ContactModal';
import { MemoryFeed } from '@/components/MemoryFeed';
import { Contact } from '@/types/contact';
import { getAge, getDaysUntilBirthday } from '@/lib/dateUtils';

interface ContactDetailPageProps {
  getContact: (id: string) => Contact | undefined;
  fetchMemories: (contactId: string) => Promise<unknown>;
  onDeleteContact: (id: string) => void | Promise<void>;
  onUpdateContact: (id: string, updates: Partial<Contact>) => void | Promise<unknown>;
  onAddMemory: (contactId: string, content: string) => void | Promise<unknown>;
  onDeleteMemory: (contactId: string, memoryId: string) => void | Promise<unknown>;
  onFetchRecommendations: (contactId: string) => Promise<unknown>;
  recommendations: (contactId: string) => string[];
  contactsLoading: boolean;
}

export function ContactDetailPage({
  getContact,
  fetchMemories,
  onDeleteContact,
  onUpdateContact,
  onAddMemory,
  onDeleteMemory,
  onFetchRecommendations,
  recommendations,
  contactsLoading,
}: ContactDetailPageProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const contact = id ? getContact(id) : undefined;

  useEffect(() => {
    if (id) fetchMemories(id);
  }, [id, fetchMemories]);

  useEffect(() => {
    if (id) onFetchRecommendations(id);
  }, [id, onFetchRecommendations]);

  if (contactsLoading && !contact) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Contact not found</p>
          <Button variant="outline" onClick={() => navigate('/dashboard')}>
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  const age = getAge(contact.birthday);
  const daysUntilBirthday = getDaysUntilBirthday(contact.birthday);
  const giftIdeas = recommendations(contact.id);

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this contact?')) {
      await Promise.resolve(onDeleteContact(contact.id));
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="flex items-center justify-between px-4 md:px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span className="hidden md:inline">Back</span>
          </button>

          <div className="flex items-center gap-2">
            <Button aria-label="Edit contact" variant="ghost" size="icon" onClick={() => setIsEditing(true)}>
              <Pencil className="h-5 w-5" />
            </Button>
            <Button
              aria-label="Delete contact"
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="px-4 md:px-6 py-8 border-b border-border"
      >
        <div className="flex items-center gap-4 mb-6">
          <AvatarInitials name={contact.name} size="lg" />
          <div>
            <h1 className="text-2xl font-bold text-foreground">{contact.name}</h1>
            <p className="text-muted-foreground">
              {contact.relationship} • {age} years old
            </p>
          </div>
        </div>

        <div className="rounded-2xl bg-coral-50 p-4">
          <p className="text-sm text-muted-foreground mb-1">Days until birthday</p>
          <p className="text-3xl font-bold text-primary">
            {daysUntilBirthday === 0 ? 'Today! 🎉' : daysUntilBirthday}
          </p>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="px-4 md:px-6 py-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">Notes & Preferences</h2>
          <span className="text-sm text-muted-foreground">
            {contact.memories.length} {contact.memories.length === 1 ? 'note' : 'notes'}
          </span>
        </div>

        <MemoryFeed
          memories={contact.memories}
          onAddMemory={(content) => onAddMemory(contact.id, content)}
          onDeleteMemory={(memoryId) => onDeleteMemory(contact.id, memoryId)}
        />
      </motion.div>

      <div className="px-4 md:px-6 pb-8">
        <div className="rounded-2xl bg-card p-4 shadow-card">
          <div className="mb-3 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-secondary" />
            <h2 className="text-lg font-semibold text-foreground">Gift Ideas</h2>
          </div>
          {giftIdeas.length > 0 ? (
            <ul className="space-y-2">
              {giftIdeas.map((idea) => (
                <li key={idea} className="rounded-xl bg-muted px-3 py-2 text-sm text-foreground">
                  {idea}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Add notes to improve gift ideas.</p>
          )}
        </div>
      </div>

      <ContactModal
        isOpen={isEditing}
        onClose={() => setIsEditing(false)}
        onSave={(updates) => onUpdateContact(contact.id, updates)}
        contact={contact}
      />
    </div>
  );
}
