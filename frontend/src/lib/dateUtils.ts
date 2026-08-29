import { differenceInDays, differenceInYears, format, setYear, isAfter, isBefore, startOfDay } from 'date-fns';

export function getDaysUntilBirthday(birthday: Date): number {
  const today = startOfDay(new Date());
  const thisYearBirthday = setYear(birthday, today.getFullYear());
  
  if (isBefore(thisYearBirthday, today)) {
    // Birthday has passed this year, calculate for next year
    const nextYearBirthday = setYear(birthday, today.getFullYear() + 1);
    return differenceInDays(nextYearBirthday, today);
  }
  
  return differenceInDays(thisYearBirthday, today);
}

export function getAge(birthday: Date): number {
  return differenceInYears(new Date(), birthday);
}

export function formatBirthdayBadge(birthday: Date): { text: string; isUrgent: boolean } {
  const daysUntil = getDaysUntilBirthday(birthday);
  
  if (daysUntil === 0) {
    return { text: 'Today! 🎉', isUrgent: true };
  }
  
  if (daysUntil <= 14) {
    return { text: `${daysUntil} day${daysUntil === 1 ? '' : 's'} left!`, isUrgent: true };
  }
  
  // Format as month and day
  const thisYearBirthday = setYear(birthday, new Date().getFullYear());
  const nextBirthday = isBefore(thisYearBirthday, new Date()) 
    ? setYear(birthday, new Date().getFullYear() + 1)
    : thisYearBirthday;
    
  return { text: format(nextBirthday, 'MMM d'), isUrgent: false };
}

export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const days = differenceInDays(now, date);
  
  if (days === 0) {
    return 'Added today';
  }
  
  if (days === 1) {
    return 'Added yesterday';
  }
  
  if (days < 7) {
    return `Added ${days} days ago`;
  }
  
  if (days < 30) {
    const weeks = Math.floor(days / 7);
    return `Added ${weeks} week${weeks === 1 ? '' : 's'} ago`;
  }
  
  return `Added ${format(date, 'MMM d, yyyy')}`;
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
}
