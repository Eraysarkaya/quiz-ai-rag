// Quiz AI API Client

import {
    QuizRequest,
    QuizResponse,
    QuizHistoryResponse,
    User,
    AuthToken,
    QuizQuestion
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ============ Structured API Error ============

/**
 * Structured API Error class that preserves backend error details.
 * Use error.message for user-facing text, error.code for programmatic handling.
 */
export class ApiError extends Error {
    code: string;
    details?: Record<string, unknown>;
    status: number;

    constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
        this.details = details;
    }

    /** Check if this is an authentication error (401) */
    isAuthError(): boolean {
        return this.status === 401;
    }

    /** Check if this is a not found error (404) */
    isNotFound(): boolean {
        return this.status === 404;
    }
}

// ============ Helper Functions ============

async function fetchWithAuth<T>(
    endpoint: string,
    options: RequestInit = {},
    timeout: number = 30000
): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('quiz_ai_token') : null;

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            // Parse error response - handle both structured {error:{...}} and legacy {detail:...}
            const data = await response.json().catch(() => ({}));

            let code = 'UNKNOWN_ERROR';
            let message = 'Request failed';
            let details: Record<string, unknown> | undefined;

            if (data.error && typeof data.error === 'object') {
                // Structured error format: {error: {code, message, details}}
                code = data.error.code || code;
                message = data.error.message || message;
                details = data.error.details;
            } else if (data.detail) {
                // Legacy FastAPI format: {detail: "..."}
                message = data.detail;
                code = 'API_ERROR';
            }

            throw new ApiError(response.status, code, message, details);
        }

        return response.json();
    } catch (error: unknown) {
        clearTimeout(timeoutId);

        // Re-throw ApiError as-is
        if (error instanceof ApiError) {
            throw error;
        }

        // Handle abort/timeout
        if (error instanceof Error && error.name === 'AbortError') {
            throw new ApiError(408, 'TIMEOUT', 'Request timeout - server took too long to respond');
        }

        // Handle network errors
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new ApiError(0, 'NETWORK_ERROR', 'Network error - please check your connection');
        }

        // Re-throw unknown errors
        throw error;
    }
}

// ============ Quiz API ============

export async function generateQuiz(request: QuizRequest): Promise<QuizResponse> {
    // Use 60 second timeout for quiz generation (Groq API can take 10-20s)
    const response = await fetchWithAuth<QuizResponse>('/quiz/generate', {
        method: 'POST',
        body: JSON.stringify(request),
    }, 60000);

    return response;
}

export async function getPopularTopics(): Promise<string[]> {
    try {
        const response = await fetchWithAuth<{ topics: string[] }>('/quiz/topics');
        return response.topics;
    } catch {
        return ['Physics', 'Biology', 'Chemistry', 'Earth Science', 'Astronomy'];
    }
}

export async function saveQuizAttempt(
    topic: string,
    difficulty: string,
    questions: QuizQuestion[],
    answers: Record<string, string>,
    score: number,
    total: number
): Promise<{ success: boolean; attempt_id: string }> {
    return await fetchWithAuth('/quiz/save', {
        method: 'POST',
        body: JSON.stringify({ topic, difficulty, questions, answers, score, total }),
    });
}

// ============ Auth API ============

export async function loginWithGoogle(code: string, redirectUri: string): Promise<AuthToken> {
    return fetchWithAuth<AuthToken>('/auth/google', {
        method: 'POST',
        body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });
}

export async function getCurrentUser(): Promise<User> {
    return fetchWithAuth<User>('/auth/me');
}

export async function getQuizHistory(limit: number = 50): Promise<QuizHistoryResponse> {
    return fetchWithAuth<QuizHistoryResponse>(`/quiz/history?limit=${limit}`);
}

export async function logout(): Promise<void> {
    await fetchWithAuth('/auth/logout', { method: 'POST' });
    if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
    }
}

// ============ Quiz Progress API ============

export interface QuizProgressData {
    topic: string;
    difficulty: string;
    questions: QuizQuestion[];
    answers: Record<string, string>;
    current_index: number;
    checked_questions?: string[];
}

export async function saveQuizProgress(data: QuizProgressData): Promise<{ success: boolean; progress_id: string }> {
    return fetchWithAuth('/quiz/progress', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function getQuizProgress(): Promise<{ has_progress: boolean; progress: QuizProgressData | null; all_progress: QuizProgressData[] }> {
    return fetchWithAuth('/quiz/progress');
}

export async function deleteQuizProgress(): Promise<{ success: boolean; deleted: boolean }> {
    return fetchWithAuth('/quiz/progress', { method: 'DELETE' });
}

// ============ NEW: Unified Quiz API ============

export interface Quiz {
    id: string;
    topic: string;
    difficulty: string;
    questions: QuizQuestion[];
    answers: Record<string, string>;
    current_index: number;
    score: number;
    total: number;
    percentage: number;
    status: 'in_progress' | 'completed';
    is_completed: boolean;
    created_at: string;
    updated_at: string;
}

export interface QuizSaveData {
    quiz_id?: string;  // If provided, update existing quiz
    topic: string;
    difficulty: string;
    questions: QuizQuestion[];
    answers?: Record<string, string>;
    current_index?: number;
    score?: number;
    status?: 'in_progress' | 'completed';
}

export async function getQuizzes(limit: number = 50): Promise<{ quizzes: Quiz[] }> {
    return fetchWithAuth(`/quiz/quizzes?limit=${limit}`);
}

export async function saveQuiz(data: QuizSaveData, options?: { keepalive?: boolean }): Promise<{ success: boolean; quiz: Partial<Quiz> }> {
    return fetchWithAuth('/quiz/quizzes', {
        method: 'POST',
        body: JSON.stringify({
            quiz_id: data.quiz_id,
            topic: data.topic,
            difficulty: data.difficulty,
            questions: data.questions,
            answers: data.answers || {},
            current_index: data.current_index || 0,
            score: data.score || 0,
            status: data.status || 'in_progress'
        }),
        keepalive: options?.keepalive
    });
}

export async function getQuizById(quizId: string): Promise<{ quiz: Quiz }> {
    return fetchWithAuth(`/quiz/quizzes/${quizId}`);
}

export async function deleteQuiz(quizId: string): Promise<{ success: boolean; deleted: boolean }> {
    return fetchWithAuth(`/quiz/quizzes/${quizId}`, { method: 'DELETE' });
}

export async function renameQuiz(quizId: string, newTopic: string): Promise<{ success: boolean; quiz: Partial<Quiz> }> {
    return fetchWithAuth(`/quiz/quizzes/${quizId}`, {
        method: 'PATCH',
        body: JSON.stringify({ topic: newTopic }),
    });
}

// ============ Health Check ============

export async function checkHealth(): Promise<{ status: string; version: string }> {
    return fetchWithAuth('/health');
}

// ============ Auth Helpers ============

export function isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('quiz_ai_token');
}

export function setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
        localStorage.setItem('quiz_ai_token', token);
    }
}

export function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('quiz_ai_token');
}

export function clearAuthToken(): void {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('quiz_ai_token');
    }
}

// ============ User Preferences & Profile ============

export interface UserPreferences {
    default_difficulty: string;
    default_question_count: number;
}

export async function getUserPreferences(): Promise<UserPreferences> {
    return fetchWithAuth('/user/preferences');
}

export async function updateUserPreferences(data: {
    default_difficulty?: string;
    default_question_count?: number;
}): Promise<{ success: boolean; preferences: UserPreferences }> {
    return fetchWithAuth('/user/preferences', {
        method: 'PATCH',
        body: JSON.stringify(data),
    });
}

export async function updateUserProfile(data: { name: string }): Promise<{ success: boolean; user: User }> {
    return fetchWithAuth('/user/profile', {
        method: 'PATCH',
        body: JSON.stringify(data),
    });
}

export async function clearUserHistory(): Promise<{ success: boolean; deleted_count: number }> {
    return fetchWithAuth('/user/clear-history', { method: 'POST' });
}

export async function deleteUserAccount(): Promise<{ success: boolean; message: string }> {
    return fetchWithAuth('/user/account', { method: 'DELETE' });
}
