'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';
import { useQuizHistory } from '@/lib/QuizHistoryContext';
import { useUserPreferences } from '@/lib/UserPreferencesContext';
import { Sidebar } from '@/components';
import { Bars3Icon } from '@heroicons/react/24/outline';
import {
    getUserPreferences,
    updateUserPreferences,
    updateUserProfile,
    clearUserHistory,
    deleteUserAccount
} from '@/lib/api';
import { DIFFICULTIES, QUESTION_COUNTS, DIFFICULTY_LABELS, QUESTION_COUNT_LABELS, Difficulty } from '@/lib/constants';
import { useToast } from '@/lib/ToastContext';

function errorDetails(error: unknown): { message: string; status?: number } {
    if (error instanceof Error) {
        return {
            message: error.message,
            status: 'status' in error && typeof error.status === 'number' ? error.status : undefined,
        };
    }
    return { message: 'Unexpected error' };
}

export default function SettingsPage() {
    const router = useRouter();
    const { user, isAuthenticated, logout, updateUser } = useAuth();
    const { loadQuizzes } = useQuizHistory();
    const { setPreferences: setGlobalPreferences } = useUserPreferences();
    const { showToast } = useToast();

    // Form state (local edits)
    const [name, setName] = useState('');
    const [difficulty, setDifficulty] = useState<Difficulty>('medium');
    const [questionCount, setQuestionCount] = useState(5);

    // Original values (for dirty tracking)
    const [originalName, setOriginalName] = useState('');
    const [originalDifficulty, setOriginalDifficulty] = useState<Difficulty>('medium');
    const [originalQuestionCount, setOriginalQuestionCount] = useState(5);

    // UI state
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [prefsLoaded, setPrefsLoaded] = useState(false);

    // Load user data
    useEffect(() => {
        if (user) {
            setName(user.name);
            setOriginalName(user.name);
        }
    }, [user]);

    // Load preferences from server
    useEffect(() => {
        if (isAuthenticated && !prefsLoaded) {
            getUserPreferences()
                .then(prefs => {
                    const d = prefs.default_difficulty as Difficulty;
                    const q = prefs.default_question_count;
                    setDifficulty(d);
                    setQuestionCount(q);
                    setOriginalDifficulty(d);
                    setOriginalQuestionCount(q);
                    setPrefsLoaded(true);
                })
                .catch(err => {
                    console.error('Failed to load preferences:', err);
                    setPrefsLoaded(true);
                });
        }
    }, [isAuthenticated, prefsLoaded]);

    // Dirty check
    const isNameDirty = name.trim() !== originalName;
    const isPrefsDirty = difficulty !== originalDifficulty || questionCount !== originalQuestionCount;
    const isDirty = isNameDirty || isPrefsDirty;

    // Save handler - calls only changed endpoints
    const handleSave = useCallback(async () => {
        if (!isDirty) return;

        setSaving(true);
        setError(null);
        setSaved(false);

        try {
            // Save profile if name changed
            if (isNameDirty) {
                const trimmedName = name.trim();
                if (!trimmedName) {
                    setError('Name cannot be empty');
                    setSaving(false);
                    return;
                }
                const response = await updateUserProfile({ name: trimmedName });
                if (response.success) {
                    updateUser({ name: response.user.name });
                    setOriginalName(response.user.name);
                }
            }

            // Save preferences if changed
            if (isPrefsDirty) {
                const response = await updateUserPreferences({
                    default_difficulty: difficulty,
                    default_question_count: questionCount
                });
                if (response.success) {
                    setOriginalDifficulty(difficulty);
                    setOriginalQuestionCount(questionCount);
                    // Update global context for Home page
                    setGlobalPreferences({ difficulty, questionCount });
                }
            }

            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (err: unknown) {
            const details = errorDetails(err);
            if (details.status === 401) {
                logout();
                router.push('/login');
                return;
            }
            setError(details.message || 'Failed to save changes');
        } finally {
            setSaving(false);
        }
    }, [isDirty, isNameDirty, isPrefsDirty, name, difficulty, questionCount, updateUser, setGlobalPreferences, logout, router]);

    const handleClearHistory = useCallback(async () => {
        if (!confirm('Are you sure you want to clear all quiz history? This cannot be undone.')) {
            return;
        }
        try {
            await clearUserHistory();
            loadQuizzes();
            showToast('History cleared successfully', 'success');
            router.push('/');
        } catch (err: unknown) {
            showToast(errorDetails(err).message || 'Failed to clear history', 'error');
        }
    }, [loadQuizzes, router, showToast]);

    const handleDeleteAccount = useCallback(async () => {
        if (!confirm('Are you sure you want to delete your account? This cannot be undone.')) {
            return;
        }
        try {
            await deleteUserAccount();
            showToast('Account deleted successfully', 'success');
            logout();
            router.push('/');
        } catch (err: unknown) {
            showToast(errorDetails(err).message || 'Failed to delete account', 'error');
        }
    }, [logout, router, showToast]);

    return (
        <div className="min-h-screen flex bg-[#131314]">
            <Sidebar
                onNewQuiz={() => router.push('/')}
                isMobileOpen={isMobileSidebarOpen}
                onMobileClose={() => setIsMobileSidebarOpen(false)}
            />

            <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
                {/* Mobile Header */}
                <div className="md:hidden flex items-center justify-between p-4 border-b border-gray-800 bg-[#131314]">
                    <button
                        onClick={() => setIsMobileSidebarOpen(true)}
                        className="p-2 rounded-full hover:bg-[#333537] text-gray-400 transition-colors"
                    >
                        <Bars3Icon className="w-6 h-6" />
                    </button>
                    <h1 className="text-base font-semibold text-white">Settings</h1>
                    {user ? (
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow-lg">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                    ) : (
                        <div className="w-8" />
                    )}
                </div>

                {/* Desktop Header */}
                <div className="hidden md:flex justify-between items-center p-4 md:p-6 border-b border-gray-800 sticky top-0 bg-[#131314] z-10">
                    <h1 className="text-lg md:text-xl font-semibold text-white">Settings</h1>
                    {user && (
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow-lg">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                    )}
                </div>

                {/* Content Area */}
                <div className="flex-1 p-4 sm:p-6 md:p-8 lg:p-12 overflow-y-auto">
                    <div className="max-w-3xl mx-auto space-y-6 md:space-y-8">

                        {/* Account Section */}
                        <section className="bg-[#1E1F20] rounded-xl md:rounded-2xl p-4 md:p-6 border border-gray-800">
                            <h2 className="text-base md:text-lg font-semibold text-white mb-4 flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                Account Information
                            </h2>

                            {isAuthenticated ? (
                                <div className="flex flex-col sm:flex-row items-center gap-4 md:gap-6">
                                    <div className="relative flex-shrink-0">
                                        <div className="h-16 w-16 md:h-20 md:w-20 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-2xl md:text-3xl font-bold shadow-lg">
                                            {user?.name.charAt(0).toUpperCase()}
                                        </div>
                                    </div>
                                    <div className="flex-1 w-full space-y-3 md:space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
                                            <div>
                                                <label className="block text-xs font-medium text-gray-400 mb-1">Full Name</label>
                                                <input
                                                    type="text"
                                                    value={name}
                                                    onChange={(e) => setName(e.target.value)}
                                                    className="w-full bg-[#131314] border border-gray-700 rounded-lg text-white text-sm py-2 md:py-2.5 px-3 focus:border-indigo-500 outline-none transition-colors"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-gray-400 mb-1">Email Address</label>
                                                <input
                                                    type="email"
                                                    value={user?.email || ''}
                                                    disabled
                                                    className="w-full bg-[#131314] border border-gray-700 rounded-lg text-gray-500 text-sm py-2 md:py-2.5 px-3 cursor-not-allowed"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-6 md:py-8">
                                    <p className="text-gray-400 mb-4 text-sm md:text-base">Sign in to manage your account</p>
                                    <Link href="/login" className="inline-block px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm md:text-base">
                                        Sign In
                                    </Link>
                                </div>
                            )}
                        </section>

                        {/* Preferences Section */}
                        <section className="bg-[#1E1F20] rounded-xl md:rounded-2xl p-4 md:p-6 border border-gray-800">
                            <h2 className="text-base md:text-lg font-semibold text-white mb-4 flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                </svg>
                                Preferences
                            </h2>
                            <div className="space-y-4 md:space-y-6">
                                {/* Default Difficulty */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-white">Default Difficulty</p>
                                        <p className="text-xs text-gray-400">Set your preferred starting difficulty</p>
                                    </div>
                                    <select
                                        value={difficulty}
                                        onChange={(e) => setDifficulty(e.target.value as Difficulty)}
                                        className="bg-[#131314] border border-gray-700 text-white text-sm rounded-lg p-2 md:p-2.5 focus:border-indigo-500 outline-none transition-colors"
                                    >
                                        {DIFFICULTIES.map((d) => (
                                            <option key={d} value={d}>{DIFFICULTY_LABELS[d]}</option>
                                        ))}
                                    </select>
                                </div>

                                <hr className="border-gray-700" />

                                {/* Default Question Count */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-white">Default Question Count</p>
                                        <p className="text-xs text-gray-400">Number of questions per quiz</p>
                                    </div>
                                    <select
                                        value={questionCount}
                                        onChange={(e) => setQuestionCount(parseInt(e.target.value))}
                                        className="bg-[#131314] border border-gray-700 text-white text-sm rounded-lg p-2 md:p-2.5 focus:border-indigo-500 outline-none transition-colors"
                                    >
                                        {QUESTION_COUNTS.map((count) => (
                                            <option key={count} value={count}>{QUESTION_COUNT_LABELS[count]}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Save Button + Error */}
                                {isAuthenticated && (
                                    <div className="pt-4 border-t border-gray-700 flex items-center justify-between">
                                        {error && (
                                            <p className="text-red-400 text-xs">{error}</p>
                                        )}
                                        <div className="flex-1" />
                                        <button
                                            onClick={handleSave}
                                            disabled={!isDirty || saving}
                                            className={`px-5 py-2 font-medium rounded-lg transition-all text-sm ${saved
                                                ? 'bg-green-600 text-white'
                                                : isDirty
                                                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                                                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                                }`}
                                        >
                                            {saving ? 'Saving...' : saved ? '✓ Saved!' : 'Save changes'}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* Privacy Section */}
                        <section className="bg-[#1E1F20] rounded-xl md:rounded-2xl p-4 md:p-6 border border-gray-800">
                            <h2 className="text-base md:text-lg font-semibold text-white mb-4 flex items-center">
                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                </svg>
                                Privacy & Data
                            </h2>
                            <div className="flex items-center justify-between p-3 md:p-4 rounded-lg md:rounded-xl bg-[#131314]">
                                <div className="flex items-center gap-3">
                                    <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <div>
                                        <p className="text-sm font-medium text-white">Clear History</p>
                                        <p className="text-xs text-gray-400 hidden sm:block">Delete all your past quiz results</p>
                                    </div>
                                </div>
                                <button
                                    onClick={handleClearHistory}
                                    className="px-3 md:px-4 py-1.5 md:py-2 text-xs font-medium text-red-400 border border-red-900/30 rounded-lg hover:bg-red-900/10 transition-colors flex-shrink-0"
                                >
                                    Clear
                                </button>
                            </div>
                        </section>

                        {/* Danger Zone */}
                        {isAuthenticated && (
                            <section className="bg-red-900/10 rounded-xl md:rounded-2xl p-4 md:p-6 border border-red-900/20">
                                <h2 className="text-base md:text-lg font-semibold text-red-400 mb-2 flex items-center">
                                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                    Danger Zone
                                </h2>
                                <p className="text-xs md:text-sm text-gray-400 mb-4">
                                    Once you delete your account, there is no going back. Please be certain.
                                </p>
                                <button
                                    onClick={handleDeleteAccount}
                                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs md:text-sm font-medium rounded-lg transition-colors"
                                >
                                    Delete Account
                                </button>
                            </section>
                        )}

                        {/* Footer */}
                        <div className="py-4 text-center">
                            <p className="text-xs text-gray-500">
                                © 2025 Quiz AI · <a href="/terms" className="hover:text-gray-300">Terms</a> · <a href="/privacy" className="hover:text-gray-300">Privacy</a>
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
