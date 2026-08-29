import { useEffect, useState } from 'react';
import { Database, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { get } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import type { ApiDbSnapshotData } from '@/lib/apiMappers';

export function DatabasePage() {
  const [snapshot, setSnapshot] = useState<ApiDbSnapshotData | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadSnapshot = async () => {
    setIsLoading(true);
    setError('');
    try {
      setSnapshot(await get<ApiDbSnapshotData>(API_PATHS.DEV_DB_SNAPSHOT));
    } catch {
      setError('Database snapshot is unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSnapshot();
  }, []);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="flex items-center justify-between px-4 md:px-6 py-4">
          <h1 className="text-2xl font-bold text-foreground">Database</h1>
          <Button aria-label="Refresh database snapshot" variant="outline" size="icon" onClick={loadSnapshot} disabled={isLoading}>
            <RefreshCw className={isLoading ? 'h-5 w-5 animate-spin' : 'h-5 w-5'} />
          </Button>
        </div>
      </header>

      <div className="px-4 md:px-6 py-6 space-y-4">
        {error ? <p className="text-sm text-destructive">{error}</p> : null}

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl bg-card p-5 shadow-card">
          <div className="mb-4 flex items-center gap-3">
            <Database className="h-5 w-5 text-secondary" />
            <div>
              <h2 className="font-semibold text-foreground">{snapshot?.database_url ?? 'Loading'} database</h2>
              <p className="text-sm text-muted-foreground">Development snapshot</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {(['users', 'contacts', 'memories'] as const).map((key) => (
              <div key={key} className="rounded-xl bg-muted p-3">
                <p className="text-xs text-muted-foreground">{key}</p>
                <p className="text-xl font-semibold text-foreground">{snapshot?.counts[key] ?? '-'}</p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl bg-card p-5 shadow-card">
          <h2 className="mb-3 text-lg font-semibold text-foreground">AI</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-muted p-3">
              <p className="text-xs text-muted-foreground">provider</p>
              <p className="font-medium text-foreground">{snapshot?.ai.provider ?? '-'}</p>
            </div>
            <div className="rounded-xl bg-muted p-3">
              <p className="text-xs text-muted-foreground">model</p>
              <p className="font-medium text-foreground">{snapshot?.ai.model ?? '-'}</p>
            </div>
            <div className="rounded-xl bg-muted p-3">
              <p className="text-xs text-muted-foreground">key</p>
              <p className="font-medium text-foreground">{snapshot?.ai.configured ? 'configured' : 'fallback'}</p>
            </div>
          </div>
        </motion.div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">Recent Contacts</h2>
          {(snapshot?.contacts ?? []).map((contact) => (
            <div key={contact.id} className="rounded-2xl bg-card p-4 shadow-card">
              <p className="font-medium text-foreground">{contact.name}</p>
              <p className="text-sm text-muted-foreground">
                {contact.relationship_type || 'Contact'} · {contact.memory_count ?? 0} notes
              </p>
            </div>
          ))}
          {snapshot && snapshot.contacts.length === 0 ? <p className="text-sm text-muted-foreground">No contacts yet.</p> : null}
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">Recent Memories</h2>
          {(snapshot?.memories ?? []).map((memory) => (
            <div key={memory.id} className="rounded-2xl bg-card p-4 shadow-card">
              <p className="text-sm text-foreground">{memory.content}</p>
            </div>
          ))}
          {snapshot && snapshot.memories.length === 0 ? <p className="text-sm text-muted-foreground">No memories yet.</p> : null}
        </section>
      </div>
    </div>
  );
}
