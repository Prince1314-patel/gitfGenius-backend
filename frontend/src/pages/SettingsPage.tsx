import { User, Bell, Palette } from 'lucide-react';
import { motion } from 'framer-motion';

interface SettingsPageProps {
  userName: string;
  userEmail: string;
}

export function SettingsPage({ userName, userEmail }: SettingsPageProps) {
  const settingsItems = [
    { icon: User, label: 'Profile', description: 'Update your personal information' },
    { icon: Bell, label: 'Notifications', description: 'Manage your reminder preferences' },
    { icon: Palette, label: 'Appearance', description: 'Customize the look and feel' },
  ];

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="px-4 md:px-6 py-4">
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        </div>
      </header>

      <div className="px-4 md:px-6 py-6 space-y-6">
        {/* User Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl bg-card p-6 shadow-card"
        >
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-2xl font-semibold text-primary-foreground">
              {userName.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{userName}</h2>
              <p className="text-muted-foreground">{userEmail}</p>
            </div>
          </div>
        </motion.div>

        {/* Settings List */}
        <div className="space-y-3">
          {settingsItems.map((item, index) => (
            <motion.button
              key={item.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="w-full flex items-center gap-4 rounded-2xl bg-card p-4 shadow-card text-left hover:shadow-card-hover transition-shadow"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                <item.icon className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-medium text-foreground">{item.label}</h3>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}
