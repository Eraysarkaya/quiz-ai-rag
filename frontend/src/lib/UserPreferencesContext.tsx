'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { getUserPreferences } from './api';
import { useAuth } from './AuthContext';
import { Difficulty } from '@/types';

// Default values for guests or loading state
const DEFAULT_DIFFICULTY: Difficulty = 'medium';
const DEFAULT_QUESTION_COUNT = 5;

interface UserPreferencesContextType {
    // Current preferences
    difficulty: Difficulty;
    questionCount: number;
    isLoaded: boolean;

    // Update preferences (call after successful save to server)
    setPreferences: (prefs: { difficulty?: Difficulty; questionCount?: number }) => void;

    // Reload from server
    reloadPreferences: () => Promise<void>;
}

const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined);

export function UserPreferencesProvider({ children }: { children: ReactNode }) {
    const { isAuthenticated } = useAuth();

    const [difficulty, setDifficulty] = useState<Difficulty>(DEFAULT_DIFFICULTY);
    const [questionCount, setQuestionCount] = useState<number>(DEFAULT_QUESTION_COUNT);
    const [isLoaded, setIsLoaded] = useState(false);

    // Load preferences from server when authenticated
    const reloadPreferences = useCallback(async () => {
        if (!isAuthenticated) {
            setDifficulty(DEFAULT_DIFFICULTY);
            setQuestionCount(DEFAULT_QUESTION_COUNT);
            setIsLoaded(true);
            return;
        }

        try {
            const prefs = await getUserPreferences();
            setDifficulty(prefs.default_difficulty as Difficulty);
            setQuestionCount(prefs.default_question_count);
        } catch (err) {
            console.error('[Preferences] Failed to load:', err);
            // Keep defaults on error
        } finally {
            setIsLoaded(true);
        }
    }, [isAuthenticated]);

    // Load on mount and when auth changes
    useEffect(() => {
        reloadPreferences();
    }, [reloadPreferences]);

    // Update local state (call after successful server save)
    const setPreferences = useCallback((prefs: { difficulty?: Difficulty; questionCount?: number }) => {
        if (prefs.difficulty !== undefined) {
            setDifficulty(prefs.difficulty);
        }
        if (prefs.questionCount !== undefined) {
            setQuestionCount(prefs.questionCount);
        }
    }, []);

    return (
        <UserPreferencesContext.Provider value={{
            difficulty,
            questionCount,
            isLoaded,
            setPreferences,
            reloadPreferences
        }}>
            {children}
        </UserPreferencesContext.Provider>
    );
}

export function useUserPreferences() {
    const context = useContext(UserPreferencesContext);
    if (!context) {
        throw new Error('useUserPreferences must be used within UserPreferencesProvider');
    }
    return context;
}
