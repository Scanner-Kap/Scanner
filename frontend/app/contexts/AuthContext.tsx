import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import axios from 'axios';

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL || '';

export interface GitHubUser {
  id: number;
  github_id: number;
  github_login: string;
  name: string | null;
  email: string | null;
  avatar_url: string | null;
  bio: string | null;
}

interface AuthContextType {
  user: GitHubUser | null;
  token: string | null;
  isLoading: boolean;
  signInWithGitHub: () => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isLoading: false,
  signInWithGitHub: async () => {},
  signOut: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

// In-memory token storage (use SecureStore in production for native apps)
let storedToken: string | null = null;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<GitHubUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUserProfile = useCallback(async (jwtToken: string) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      setUser(response.data);
      setToken(jwtToken);
      storedToken = jwtToken;
    } catch {
      setUser(null);
      setToken(null);
      storedToken = null;
    }
  }, []);

  // Restore session from memory on mount
  useEffect(() => {
    if (storedToken) {
      fetchUserProfile(storedToken).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [fetchUserProfile]);

  // Handle deep link callbacks from GitHub OAuth
  useEffect(() => {
    const handleUrl = async (event: { url: string }) => {
      const { url } = event;
      if (url.includes('auth/callback')) {
        const parsed = Linking.parse(url);
        const jwtToken = parsed.queryParams?.token as string | undefined;
        const error = parsed.queryParams?.error as string | undefined;

        if (jwtToken) {
          await fetchUserProfile(jwtToken);
        } else if (error) {
          console.error('GitHub OAuth error:', error);
        }
      }
    };

    const subscription = Linking.addEventListener('url', handleUrl);
    return () => subscription.remove();
  }, [fetchUserProfile]);

  const signInWithGitHub = async () => {
    if (!BACKEND_URL) {
      console.error('EXPO_PUBLIC_BACKEND_URL is not set');
      return;
    }
    try {
      const result = await WebBrowser.openAuthSessionAsync(
        `${BACKEND_URL}/api/auth/github`,
        Linking.createURL('auth/callback')
      );

      if (result.type === 'success' && result.url) {
        const parsed = Linking.parse(result.url);
        const jwtToken = parsed.queryParams?.token as string | undefined;
        if (jwtToken) {
          await fetchUserProfile(jwtToken);
        }
      }
    } catch (err) {
      console.error('GitHub sign-in failed:', err);
    }
  };

  const signOut = () => {
    setUser(null);
    setToken(null);
    storedToken = null;
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, signInWithGitHub, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
