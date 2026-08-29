import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Memory } from '@/types/contact';
import { formatRelativeTime } from '@/lib/dateUtils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface MemoryFeedProps {
  memories: Memory[];
  onAddMemory: (content: string) => void | Promise<unknown>;
  onDeleteMemory?: (memoryId: string) => void;
}

export function MemoryFeed({ memories, onAddMemory, onDeleteMemory }: MemoryFeedProps) {
  const [newMemory, setNewMemory] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddMemory = async () => {
    if (!newMemory.trim()) return;
    setIsAdding(true);
    try {
      await Promise.resolve(onAddMemory(newMemory.trim()));
      setNewMemory('');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Add Memory Section */}
      <div className="space-y-3">
        <Textarea
          placeholder="Jot down a new thought (e.g., Loves oat milk lattes)..."
          value={newMemory}
          onChange={(e) => setNewMemory(e.target.value)}
          className="min-h-[100px] rounded-xl border-2 border-warmGray-200 focus:border-secondary focus:ring-2 focus:ring-secondary/20 resize-none"
        />
        <Button
          variant="secondary"
          onClick={handleAddMemory}
          disabled={!newMemory.trim() || isAdding}
          className="w-full md:w-auto"
        >
          {isAdding ? 'Adding...' : 'Add Note'}
        </Button>
      </div>

      {/* Memory List */}
      <div className="space-y-3">
        <AnimatePresence>
          {memories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onDelete={onDeleteMemory ? () => onDeleteMemory(memory.id) : undefined}
            />
          ))}
        </AnimatePresence>

        {memories.length === 0 && (
          <p className="text-center text-muted-foreground py-8">
            No notes yet. Add your first memory above!
          </p>
        )}
      </div>
    </div>
  );
}

interface MemoryCardProps {
  memory: Memory;
  onDelete?: () => void;
}

function MemoryCard({ memory, onDelete }: MemoryCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="relative rounded-2xl bg-card p-4 shadow-card"
    >
      <p className={`text-foreground ${onDelete ? 'pr-8' : ''}`}>{memory.content}</p>
      <p className="mt-2 text-xs text-muted-foreground">
        {formatRelativeTime(memory.createdAt)}
      </p>

      {onDelete && (
        <button
          aria-label="Delete note"
          onClick={onDelete}
          className="absolute top-3 right-3 rounded-full p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </motion.div>
  );
}
