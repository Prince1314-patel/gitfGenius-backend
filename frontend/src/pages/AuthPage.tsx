import { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import { Logo } from '@/components/Logo';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface AuthPageProps {
  onLogin: (email: string, password: string) => Promise<unknown>;
  onSignup: (email: string, password: string, fullName?: string) => Promise<unknown>;
  isLoading: boolean;
  error: string | null;
  fieldErrors?: Record<string, string[]> | null;
}

function fieldError(fieldErrors: Record<string, string[]> | null | undefined, field: string): string | null {
  const list = fieldErrors?.[field];
  return list?.length ? list[0] ?? null : null;
}

export function AuthPage({ onLogin, onSignup, isLoading, error, fieldErrors }: AuthPageProps) {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoginMode) {
      await onLogin(email, password);
    } else {
      await onSignup(email, password, fullName.trim() || undefined);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl bg-card p-8 shadow-card">
          <div className="flex justify-center mb-8">
            <Logo size="large" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLoginMode && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full name (optional)</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder="Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  maxLength={100}
                />
                {fieldError(fieldErrors, 'full_name') && (
                  <p className="text-sm text-destructive">{fieldError(fieldErrors, 'full_name')}</p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              {fieldError(fieldErrors, 'email') && (
                <p className="text-sm text-destructive">{fieldError(fieldErrors, 'email')}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              {fieldError(fieldErrors, 'password') && (
                <p className="text-sm text-destructive">{fieldError(fieldErrors, 'password')}</p>
              )}
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-sm text-destructive text-center"
              >
                {error}
              </motion.p>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading
                ? (isLoginMode ? 'Signing in...' : 'Creating account...')
                : (isLoginMode ? 'Sign In' : 'Create Account')}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setIsLoginMode(!isLoginMode)}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {isLoginMode ? 'Need an account? Sign up' : 'Have an account? Log in'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
