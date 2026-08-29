import { Contact } from '@/types/contact';
import { AvatarInitials } from './AvatarInitials';
import { BirthdayBadge } from './BirthdayBadge';
import { formatBirthdayBadge } from '@/lib/dateUtils';
import { motion } from 'framer-motion';

interface ContactCardProps {
  contact: Contact;
  onClick: () => void;
}

export function ContactCard({ contact, onClick }: ContactCardProps) {
  const { text, isUrgent } = formatBirthdayBadge(contact.birthday);

  return (
    <motion.button
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className="flex w-full items-center gap-4 rounded-2xl bg-card p-4 shadow-card transition-shadow hover:shadow-card-hover text-left"
    >
      <AvatarInitials name={contact.name} />
      
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-foreground truncate">
          {contact.name}
        </h3>
        <p className="text-sm text-muted-foreground">
          {contact.relationship}
        </p>
      </div>

      <BirthdayBadge text={text} isUrgent={isUrgent} />
    </motion.button>
  );
}
