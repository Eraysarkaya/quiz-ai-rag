/**
 * Shared constants for quiz configuration.
 * Use these in both Settings page and Home page to prevent mismatches.
 */

// Allowed difficulty levels
export const DIFFICULTIES = ['easy', 'medium', 'hard'] as const;
export type Difficulty = typeof DIFFICULTIES[number];

// Allowed question counts (must match backend validation)
export const QUESTION_COUNTS = [3, 5, 10] as const;
export type QuestionCount = typeof QUESTION_COUNTS[number];

// Default values
export const DEFAULT_DIFFICULTY: Difficulty = 'medium';
export const DEFAULT_QUESTION_COUNT: QuestionCount = 5;

// Display labels for UI
export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard'
};

export const QUESTION_COUNT_LABELS: Record<QuestionCount, string> = {
    3: '3 Questions',
    5: '5 Questions',
    10: '10 Questions'
};
