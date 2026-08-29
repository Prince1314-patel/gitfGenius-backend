import { useState, useCallback, useEffect } from 'react';
import { get, post, clearToken, setToken, getToken } from '@/lib/api';
import { API_PATHS } from '@/lib/constants';
import { apiUserToDisplayName } from '@/lib/apiMappers';
import type { ApiUser, ApiAuthData } from '@/lib/apiMappers';
import type { ApiError } from '@/lib/api';

export interface User {
  id: string;
  email: string;
  name: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]> | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    get<ApiUser>(API_PATHS.AUTH_PROFILE, true)
      .then((data) => {
        setUser({
          id: data.id,
          email: data.email,
          name: apiUserToDisplayName(data),
        });
      })
      .catch(() => {
        clearToken();
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    setFieldErrors(null);
    try {
      const data = await post<ApiAuthData>(API_PATHS.AUTH_LOGIN, { email, password }, false);
      setToken(data.access_token);
      setUser({
        id: data.user.id,
        email: data.user.email,
        name: apiUserToDisplayName(data.user),
      });
      return { id: data.user.id, email: data.user.email, name: apiUserToDisplayName(data.user) };
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? 'Login failed');
      setFieldErrors(apiErr.details?.field_errors ?? null);
      setIsLoading(false);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signup = useCallback(
    async (email: string, password: string, fullName?: string) => {
      setIsLoading(true);
      setError(null);
      setFieldErrors(null);
      try {
        const data = await post<ApiAuthData>(API_PATHS.AUTH_REGISTER, {
          email,
          password,
          full_name: fullName ?? '',
        }, false);
        setToken(data.access_token);
        setUser({
          id: data.user.id,
          email: data.user.email,
          name: apiUserToDisplayName(data.user),
        });
        return { id: data.user.id, email: data.user.email, name: apiUserToDisplayName(data.user) };
      } catch (err) {
        const apiErr = err as ApiError;
        setError(apiErr.message ?? 'Signup failed');
        setFieldErrors(apiErr.details?.field_errors ?? null);
        setIsLoading(false);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setError(null);
    setFieldErrors(null);
  }, []);

  return {
    user,
    isLoading,
    error,
    fieldErrors,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };
}
