// Quiz AI TypeScript Types

// ============ Quiz Types ============

export type Difficulty = 'easy' | 'medium' | 'hard';

export interface QuizQuestion {
    id: string;
    question: string;
    options: Record<string, string>; // {"A": "...", "B": "...", ...}
    correct: string;
    explanation: string;
    cached: boolean;
}

export interface QuizRequest {
    topic: string;
    difficulty: Difficulty;
    num_questions: number;
}

export interface QuizResponse {
    success: boolean;
    topic: string;
    difficulty: string;
    questions: QuizQuestion[];
    error?: string;
    suggestions?: string[];
}

export interface AnswerVerifyRequest {
    question_id: string;
    selected_answer: string;
    correct_answer: string;
    explanation: string;
}

export interface AnswerVerifyResponse {
    correct: boolean;
    correct_answer: string;
    explanation: string;
}

// ============ User Types ============

export interface User {
    id: string;
    email: string;
    name: string;
    picture?: string;
}

export interface UserStats {
    total_quizzes: number;
    total_questions: number;
    correct_answers: number;
    average_score: number;
}

export interface QuizAttempt {
    id: string;
    topic: string;
    difficulty: string;
    questions: QuizQuestion[];
    answers: Record<string, string>;
    checkedQuestions?: string[];  // Question IDs that have been answered/locked
    score: number;
    total: number;
    percentage: number;
    created_at: string;
    isCompleted?: boolean;  // true if user finished all questions
}

export interface QuizHistoryResponse {
    stats: UserStats;
    attempts: QuizAttempt[];
}

// ============ Auth Types ============

export interface AuthToken {
    access_token: string;
    token_type: string;
}

// ============ UI State Types ============

export interface QuizState {
    currentQuestion: number;
    answers: Record<string, string>;
    showExplanation: boolean;
    isSubmitted: boolean;
    startTime?: Date;
    endTime?: Date;
}

export type PageType = 'home' | 'quiz' | 'results';
