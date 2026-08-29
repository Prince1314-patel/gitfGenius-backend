import { useState } from 'react';
import { X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Contact, RELATIONSHIP_OPTIONS } from '@/types/contact';

interface ContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Create-only: saves via API. Can reject with { message, details?: { field_errors } }. */
  onSave: (contact: Omit<Contact, 'id' | 'memories' | 'createdAt' | 'updatedAt'>) => void | Promise<void>;
}

function fieldError(fieldErrors: Record<string, string[]> | null | undefined, field: string): string | null {
  const list = fieldErrors?.[field];
  return list?.length ? list[0] ?? null : null;
}

export function ContactModal({ isOpen, onClose, onSave }: ContactModalProps) {
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState('');
  const [birthday, setBirthday] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]> | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setFieldErrors(null);
    setIsLoading(true);
    try {
      await Promise.resolve(
        onSave({
          name: name.trim(),
          relationship: relationship.trim() || '',
          ...(birthday && { birthday: new Date(birthday) }),
        } as Omit<Contact, 'id' | 'memories' | 'createdAt' | 'updatedAt'>)
      );
      setName('');
      setRelationship('');
      setBirthday('');
      onClose();
    } catch (err: unknown) {
      const details = err && typeof err === 'object' && 'details' in err ? (err as { details?: { field_errors?: Record<string, string[]> } }).details : undefined;
      setFieldErrors(details?.field_errors ?? null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFieldErrors(null);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-foreground/20 backdrop-blur-sm"
            onClick={handleClose}
          />

          <motion.div
            initial={{ opacity: 0, y: '100%' }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-x-0 bottom-0 z-50 md:inset-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2"
          >
            <div className="w-full max-w-lg rounded-t-3xl md:rounded-2xl bg-card p-6 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-foreground">Add New Contact</h2>
                <button
                  onClick={handleClose}
                  className="rounded-full p-2 hover:bg-muted transition-colors"
                >
                  <X className="h-5 w-5 text-muted-foreground" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="Enter contact name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                  {fieldError(fieldErrors, 'name') && (
                    <p className="text-sm text-destructive">{fieldError(fieldErrors, 'name')}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="relationship">Relationship (optional)</Label>
                  <Select value={relationship} onValueChange={setRelationship}>
                    <SelectTrigger className="h-11 rounded-xl border-2 border-warmGray-200 focus:border-secondary focus:ring-2 focus:ring-secondary/20">
                      <SelectValue placeholder="Select relationship" />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-warmGray-200 z-[100]">
                      {RELATIONSHIP_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {fieldError(fieldErrors, 'relationship_type') && (
                    <p className="text-sm text-destructive">{fieldError(fieldErrors, 'relationship_type')}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="birthday">Birthday (optional)</Label>
                  <Input
                    id="birthday"
                    type="date"
                    value={birthday}
                    onChange={(e) => setBirthday(e.target.value)}
                  />
                  {fieldError(fieldErrors, 'birthday') && (
                    <p className="text-sm text-destructive">{fieldError(fieldErrors, 'birthday')}</p>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isLoading || !name.trim()}>
                  {isLoading ? 'Saving...' : 'Save Contact'}
                </Button>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
