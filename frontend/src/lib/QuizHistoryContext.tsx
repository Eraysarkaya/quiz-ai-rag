'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from 'react';
import { getQuizzes, saveQuiz, getQuizById, deleteQuiz, renameQuiz as renameQuizApi, Quiz } from './api';
import { useAuth } from './AuthContext';
import { QuizQuestion } from '@/types';

interface QuizContextType {
    quizzes: Quiz[];
    isLoading: boolean;
    isReady: boolean;
    loadQuizzes: () => Promise<void>;
    saveQuizToServer: (data: {
        quizId?: string;
        topic: string;
        difficulty: string;
        questions: QuizQuestion[];
        answers?: Record<string, string>;
        currentIndex?: number;
        score?: number;
        status?: 'in_progress' | 'completed';
    }, options?: { keepalive?: boolean }) => Promise<{ id: string } | null>;
    getQuiz: (quizId: string) => Promise<Quiz | null>;
    removeQuiz: (quizId: string) => Promise<boolean>;
    renameQuiz: (quizId: string, newTopic: string) => Promise<boolean>;
    findQuizById: (quizId: string) => Quiz | undefined;
}

const QuizHistoryContext = createContext<QuizContextType | undefined>(undefined);

export function QuizHistoryProvider({ children }: { children: ReactNode }) {
    const [quizzes, setQuizzes] = useState<Quiz[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isReady, setIsReady] = useState(false);
    const { isAuthenticated, user } = useAuth();

    const abortControllerRef = useRef<AbortController | null>(null);
    const prevUserIdRef = useRef<string | null>(null);

    // Sort quizzes stably by updated_at desc
    const sortQuizzes = (list: Quiz[]) => {
        return [...list].sort((a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
    };

    // Load all quizzes from server (SWR pattern)
    const loadQuizzes = useCallback(async () => {
        if (!isAuthenticated || !user) {
            setQuizzes([]);
            setIsReady(true);
            return;
        }

        // Cancel previous in-flight request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();

        // Stale-while-revalidate: don't clear existing quizzes if we have them
        // Only show loading if we have no data
        if (quizzes.length === 0) {
            setIsLoading(true);
        }

        try {
            const response = await getQuizzes(50); // Pass signal if API supported it
            const serverQuizzes = response.quizzes || [];

            // Dedupe by ID as safety net (REPLACE state, never append)
            const uniqueMap = new Map<string, Quiz>();
            for (const quiz of serverQuizzes) {
                uniqueMap.set(quiz.id, quiz);
            }
            const deduped = Array.from(uniqueMap.values());
            const sorted = sortQuizzes(deduped);

            setQuizzes(sorted);
            console.log('[QuizContext] Loaded', sorted.length, 'quizzes from server');
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') return;
            console.error('[QuizContext] Failed to load quizzes:', error);
            // Don't clear quizzes on error if we have stale data (UI stability)
        } finally {
            setIsLoading(false);
            setIsReady(true);
            abortControllerRef.current = null;
        }
    }, [isAuthenticated, user, quizzes.length]);

    // Save quiz to server (create or update)
    const saveQuizToServer = useCallback(async (data: {
        quizId?: string;
        topic: string;
        difficulty: string;
        questions: QuizQuestion[];
        answers?: Record<string, string>;
        currentIndex?: number;
        score?: number;
        status?: 'in_progress' | 'completed';
    }, options?: { keepalive?: boolean }): Promise<{ id: string } | null> => {
        if (!isAuthenticated || !user) {
            console.warn('[QuizContext] Cannot save - not authenticated');
            return null;
        }

        try {
            const response = await saveQuiz({
                quiz_id: data.quizId,
                topic: data.topic,
                difficulty: data.difficulty,
                questions: data.questions,
                answers: data.answers || {},
                current_index: data.currentIndex || 0,
                score: data.score || 0,
                status: data.status || 'in_progress'
            }, options);

            if (response.success && response.quiz?.id) {
                const savedQuiz = response.quiz;
                // Optimistic update (or rather, immediate sync)
                setQuizzes(prev => {
                    const existing = prev.find(q => q.id === savedQuiz.id);
                    if (existing) {
                        return sortQuizzes(prev.map(q => q.id === savedQuiz.id ? { ...existing, ...savedQuiz } : q));
                    }
                    return sortQuizzes([savedQuiz as unknown as Quiz, ...prev]);
                });
                return { id: savedQuiz.id! };
            }
            return null;
        } catch (error) {
            console.error('[QuizContext] Failed to save quiz:', error);
            return null;
        }
    }, [isAuthenticated, user]);


    // Get single quiz by ID (from cache or server)
    const getQuiz = useCallback(async (quizId: string): Promise<Quiz | null> => {
        // First check local cache
        const cached = quizzes.find(q => q.id === quizId);
        if (cached) return cached;

        // If not in cache, fetch from server
        if (!isAuthenticated) return null;

        try {
            const response = await getQuizById(quizId);
            if (response.quiz) {
                // Update cache if fetched
                setQuizzes(prev => sortQuizzes([...prev.filter(q => q.id !== quizId), response.quiz as unknown as Quiz]));
                return response.quiz;
            }
            return null;
        } catch (error) {
            console.error('[QuizContext] Failed to get quiz:', error);
            return null;
        }
    }, [quizzes, isAuthenticated]);

    // Find quiz in local cache only (synchronous)
    const findQuizById = useCallback((quizId: string): Quiz | undefined => {
        return quizzes.find(q => q.id === quizId);
    }, [quizzes]);

    // Remove quiz (Optimistic)
    const removeQuiz = useCallback(async (quizId: string): Promise<boolean> => {
        if (!isAuthenticated) return false;

        // 1. Optimistic update
        const previousQuizzes = [...quizzes];
        setQuizzes(prev => prev.filter(q => q.id !== quizId));

        try {
            const response = await deleteQuiz(quizId);
            if (response.success) {
                return true;
            }
            // Rollback on failure (API logic error)
            setQuizzes(previousQuizzes);
            return false;
        } catch (error) {
            console.error('[QuizContext] Failed to delete quiz:', error);
            // Rollback on network error
            setQuizzes(previousQuizzes);
            return false;
        }
    }, [isAuthenticated, quizzes]);

    // Rename quiz (Optimistic)
    const renameQuiz = useCallback(async (quizId: string, newTopic: string): Promise<boolean> => {
        if (!isAuthenticated) return false;

        // 1. Optimistic update
        const previousQuizzes = [...quizzes];
        setQuizzes(prev => prev.map(q =>
            q.id === quizId ? { ...q, topic: newTopic, updated_at: new Date().toISOString() } : q
        ));

        try {
            const response = await renameQuizApi(quizId, newTopic);
            if (response.success) {
                return true;
            }
            // Rollback
            setQuizzes(previousQuizzes);
            return false;
        } catch (error) {
            console.error('[QuizContext] Failed to rename quiz:', error);
            // Rollback
            setQuizzes(previousQuizzes);
            return false;
        }
    }, [isAuthenticated, quizzes]);

    // Listen for auth events from AuthContext
    useEffect(() => {
        const handleLogout = () => {
            console.log('[QuizContext] Auth logout event - clearing quiz state');
            if (abortControllerRef.current) abortControllerRef.current.abort();
            setQuizzes([]);
            setIsReady(false);
            prevUserIdRef.current = null;
        };

        const handleLogin = () => {
            console.log('[QuizContext] Auth login event - loading quizzes');
            setIsReady(false);
            loadQuizzes();
        };

        window.addEventListener('auth-logout', handleLogout);
        window.addEventListener('auth-login', handleLogin);

        return () => {
            window.removeEventListener('auth-logout', handleLogout);
            window.removeEventListener('auth-login', handleLogin);
        };
    }, [loadQuizzes]);

    // Load quizzes when user changes (and initial load)
    useEffect(() => {
        const currentUserId = user?.id ?? null;
        const prevUserId = prevUserIdRef.current;

        // Load if user exists and changed, OR if first load/no quizzes yet (for SWR consistency)
        if (currentUserId && (currentUserId !== prevUserId || quizzes.length === 0)) {
            console.log('[QuizContext] User check:', prevUserId, '->', currentUserId);
            prevUserIdRef.current = currentUserId;
            loadQuizzes();
        } else if (!currentUserId) {
            // If logged out, ensure cleared
            if (quizzes.length > 0) setQuizzes([]);
            setIsReady(true);
        }
    }, [user, loadQuizzes, quizzes.length]);

    // Initial load
    useEffect(() => {
        if (isAuthenticated && user && !isReady && quizzes.length === 0) {
            loadQuizzes();
        }
    }, [isAuthenticated, user, isReady, quizzes.length, loadQuizzes]);

    return (
        <QuizHistoryContext.Provider value={{
            quizzes,
            isLoading,
            isReady,
            loadQuizzes,
            saveQuizToServer,
            getQuiz,
            removeQuiz,
            renameQuiz,
            findQuizById
        }}>
            {children}
        </QuizHistoryContext.Provider>
    );
}

export function useQuizHistory() {
    const context = useContext(QuizHistoryContext);
    if (context === undefined) {
        throw new Error('useQuizHistory must be used within a QuizHistoryProvider');
    }
    return context;
}

// ============ LEGACY EXPORTS (for backward compatibility) ============
// These will be removed once all components are updated

export { QuizHistoryProvider as default };
