import { Calendar as CalendarIcon } from 'lucide-react';
import { motion } from 'framer-motion';
import { Contact } from '@/types/contact';
import { getDaysUntilBirthday, formatBirthdayBadge } from '@/lib/dateUtils';

interface CalendarPageProps {
  contacts: Contact[];
}

export function CalendarPage({ contacts }: CalendarPageProps) {
  const upcoming = [...contacts].sort(
    (a, b) => getDaysUntilBirthday(a.birthday) - getDaysUntilBirthday(b.birthday)
  );

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="px-4 md:px-6 py-4">
          <h1 className="text-2xl font-bold text-foreground">Calendar</h1>
        </div>
      </header>

      <div className="px-4 md:px-6 py-6 space-y-3">
        {upcoming.length > 0 ? (
          upcoming.map((contact, index) => {
            const badge = formatBirthdayBadge(contact.birthday);
            return (
              <motion.div
                key={contact.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className="flex items-center justify-between rounded-2xl bg-card p-4 shadow-card"
              >
                <div>
                  <h2 className="font-semibold text-foreground">{contact.name}</h2>
                  <p className="text-sm text-muted-foreground">{contact.relationship || 'Contact'}</p>
                </div>
                <span className={badge.isUrgent ? 'text-primary font-semibold' : 'text-secondary'}>
                  {badge.text}
                </span>
              </motion.div>
            );
          })
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-20"
          >
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-teal-100">
              <CalendarIcon className="h-10 w-10 text-secondary" />
            </div>
            <h2 className="text-xl font-semibold text-foreground mb-2">No birthdays yet</h2>
            <p className="text-muted-foreground max-w-sm mx-auto">
              Add contacts with birthdays to see them here.
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
