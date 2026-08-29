import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ContactCard } from '@/components/ContactCard';
import { ContactModal } from '@/components/ContactModal';
import { ContactListSkeleton } from '@/components/Skeleton';
import { Contact } from '@/types/contact';
import { getDaysUntilBirthday } from '@/lib/dateUtils';

interface DashboardPageProps {
  contacts: Contact[];
  isLoading: boolean;
  userName: string;
  onAddContact: (contact: Omit<Contact, 'id' | 'memories' | 'createdAt' | 'updatedAt'>) => void;
}

export function DashboardPage({ contacts, isLoading, userName, onAddContact }: DashboardPageProps) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filter and sort contacts
  const filteredContacts = useMemo(() => {
    let result = contacts;
    
    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        contact =>
          contact.name.toLowerCase().includes(query) ||
          contact.relationship.toLowerCase().includes(query)
      );
    }

    // Sort by birthday proximity
    result = [...result].sort((a, b) => 
      getDaysUntilBirthday(a.birthday) - getDaysUntilBirthday(b.birthday)
    );

    return result;
  }, [contacts, searchQuery]);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="px-4 md:px-6 py-4">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-bold text-foreground"
          >
            Hi, {userName}
          </motion.h1>
        </div>
      </header>

      {/* Content */}
      <div className="px-4 md:px-6 py-6 space-y-6">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            placeholder="Search your contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-12"
          />
        </div>

        {/* Contact List */}
        {isLoading ? (
          <ContactListSkeleton />
        ) : filteredContacts.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-3"
          >
            {filteredContacts.map((contact, index) => (
              <motion.div
                key={contact.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <ContactCard
                  contact={contact}
                  onClick={() => navigate(`/contact/${contact.id}`)}
                />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              {searchQuery 
                ? 'No contacts found matching your search.'
                : 'No contacts yet. Add your first contact!'}
            </p>
          </div>
        )}
      </div>

      {/* FAB */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.3, type: 'spring' }}
        className="fixed bottom-24 right-4 md:bottom-6 md:right-6 z-50"
      >
        <Button
          variant="fab"
          size="fab"
          onClick={() => setIsModalOpen(true)}
        >
          <Plus className="h-6 w-6" />
        </Button>
      </motion.div>

      {/* Add Contact Modal */}
      <ContactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={onAddContact}
      />
    </div>
  );
}
