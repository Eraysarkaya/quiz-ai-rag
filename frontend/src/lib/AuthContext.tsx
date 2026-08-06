'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User } from '@/types';

type AuthStatus = 'loading' | 'authed' | 'guest';

interface AuthContextType {
    user: User | null;
    authStatus: AuthStatus;
    isAuthenticated: boolean;
    isLoading: boolean;
    // Error states - expose actual backend messages
    loginError: string | null;
    registerError: string | null;
    // Actions
    login: (email: string, password: string) => Promise<boolean>;
    loginWithGoogle: () => Promise<boolean>;
    register: (name: string, email: string, password: string) => Promise<boolean>;
    logout: () => void;
    updateUser: (user: Partial<User>) => void;
    clearErrors: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [authStatus, setAuthStatus] = useState<AuthStatus>('loading');
    const [loginError, setLoginError] = useState<string | null>(null);
    const [registerError, setRegisterError] = useState<string | null>(null);

    // Clear errors
    const clearErrors = useCallback(() => {
        setLoginError(null);
        setRegisterError(null);
    }, []);

    // Check for existing session on mount
    useEffect(() => {
        const checkAuth = async () => {
            try {
                const token = localStorage.getItem('quiz_ai_token');
                if (!token) {
                    setAuthStatus('guest');
                    return;
                }

                // Validate token with backend
                const response = await fetch(`${API_URL}/auth/me`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const userData = await response.json();
                    setUser(userData);
                    localStorage.setItem('quiz_ai_user', JSON.stringify(userData));
                    setAuthStatus('authed');
                } else {
                    // Token invalid - clear everything (strict auth, no fallback)
                    console.log('[Auth] Token invalid, clearing auth state');
                    localStorage.removeItem('quiz_ai_token');
                    localStorage.removeItem('quiz_ai_user');
                    setUser(null);
                    setAuthStatus('guest');
                }
            } catch {
                // Network error - NO cached user fallback (strict auth)
                // User must re-login when network is restored
                console.warn('[Auth] Network error during auth check, clearing state');
                localStorage.removeItem('quiz_ai_token');
                localStorage.removeItem('quiz_ai_user');
                setUser(null);
                setAuthStatus('guest');
            }
        };

        checkAuth();

        // Listen for auth-login event (from Google OAuth callback, login, register)
        const handleAuthLogin = () => {
            console.log('[Auth] auth-login event received, refreshing state');
            const savedUser = localStorage.getItem('quiz_ai_user');
            const token = localStorage.getItem('quiz_ai_token');
            if (savedUser && token) {
                try {
                    const userData = JSON.parse(savedUser);
                    setUser(userData);
                    setAuthStatus('authed');
                } catch {
                    console.warn('[Auth] Failed to parse saved user');
                }
            }
        };

        // Listen for auth-logout event (from logout action)
        const handleAuthLogout = () => {
            console.log('[Auth] auth-logout event received, clearing state');
            setUser(null);
            setAuthStatus('guest');
            setLoginError(null);
            setRegisterError(null);
        };

        window.addEventListener('auth-login', handleAuthLogin);
        window.addEventListener('auth-logout', handleAuthLogout);

        return () => {
            window.removeEventListener('auth-login', handleAuthLogin);
            window.removeEventListener('auth-logout', handleAuthLogout);
        };
    }, []);

    const login = async (email: string, password: string): Promise<boolean> => {
        setLoginError(null);
        // Do not switch to 'loading' to prevent UI flicker if already guest
        // setAuthStatus('loading'); 

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('quiz_ai_token', data.access_token);
                localStorage.setItem('quiz_ai_user', JSON.stringify(data.user));
                setUser(data.user);
                setAuthStatus('authed');

                // Dispatch login event for QuizHistoryContext to load data
                window.dispatchEvent(new Event('auth-login'));
                return true;
            }

            // Login failed - extract structured error message
            const errorMsg = data.error?.message || data.detail || 'Login failed';
            setLoginError(errorMsg);
            setAuthStatus('guest');
            return false;
        } catch {
            // Network error
            setLoginError('Network error. Please check your connection.');
            setAuthStatus('guest');
            return false;
        }
    };

    const loginWithGoogle = async (): Promise<boolean> => {
        const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

        if (!GOOGLE_CLIENT_ID) {
            console.error('Google Client ID not configured');
            setLoginError('Google login is not configured');
            return false;
        }

        // Redirect to Google OAuth
        const redirectUri = `${window.location.origin}/auth/google/callback`;
        const scope = 'openid email profile';
        const state = Math.random().toString(36).substring(7);

        // Save state for verification
        sessionStorage.setItem('google_oauth_state', state);

        const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
            `client_id=${GOOGLE_CLIENT_ID}` +
            `&redirect_uri=${encodeURIComponent(redirectUri)}` +
            `&response_type=code` +
            `&scope=${encodeURIComponent(scope)}` +
            `&state=${state}` +
            `&access_type=offline` +
            `&prompt=consent`;

        window.location.href = googleAuthUrl;
        return true; // Will redirect
    };

    const register = async (name: string, email: string, password: string): Promise<boolean> => {
        setRegisterError(null);
        // setAuthStatus('loading'); // Optional

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('quiz_ai_token', data.access_token);
                localStorage.setItem('quiz_ai_user', JSON.stringify(data.user));
                setUser(data.user);
                setAuthStatus('authed');

                // Dispatch login event for QuizHistoryContext to load data
                window.dispatchEvent(new Event('auth-login'));
                return true;
            }

            // Registration failed - extract structured error message
            const errorMsg = data.error?.message || data.detail || 'Registration failed';
            setRegisterError(errorMsg);
            setAuthStatus('guest');
            return false;
        } catch {
            // Network error
            setRegisterError('Network error. Please check your connection.');
            setAuthStatus('guest');
            return false;
        }
    };

    const logout = useCallback(() => {
        console.log('[Auth] Logging out, clearing all auth data');

        // Clear auth data only (no quiz history in localStorage anymore)
        localStorage.removeItem('quiz_ai_token');
        localStorage.removeItem('quiz_ai_user');

        // Clear errors
        setLoginError(null);
        setRegisterError(null);

        // Clear user state
        setUser(null);

        // Dispatch event for QuizHistoryContext to clear quiz state
        window.dispatchEvent(new Event('auth-logout'));
    }, []);

    const updateUser = (updates: Partial<User>) => {
        if (user) {
            const updatedUser = { ...user, ...updates };
            setUser(updatedUser);
            localStorage.setItem('quiz_ai_user', JSON.stringify(updatedUser));
        }
    };

    return (
        <AuthContext.Provider value={{
            user,
            authStatus,
            isAuthenticated: !!user,
            isLoading: authStatus === 'loading',
            loginError,
            registerError,
            login,
            loginWithGoogle,
            register,
            logout,
            updateUser,
            clearErrors
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
