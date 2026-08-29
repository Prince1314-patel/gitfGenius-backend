import { Calendar as CalendarIcon } from 'lucide-react';
import { motion } from 'framer-motion';

export function CalendarPage() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="px-4 md:px-6 py-4">
          <h1 className="text-2xl font-bold text-foreground">Calendar</h1>
        </div>
      </header>

      <div className="flex flex-col items-center justify-center px-4 py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-teal-100">
            <CalendarIcon className="h-10 w-10 text-secondary" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">
            Coming Soon
          </h2>
          <p className="text-muted-foreground max-w-sm">
            The calendar view will help you see all upcoming birthdays at a glance. Stay tuned!
          </p>
        </motion.div>
      </div>
    </div>
  );
}
