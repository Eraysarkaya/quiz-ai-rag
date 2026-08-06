'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    PlusIcon,
    ChatBubbleLeftIcon,
    Bars3Icon,
    XMarkIcon,
    Cog6ToothIcon,
    ArrowRightOnRectangleIcon,
    ChevronDownIcon,
    EllipsisVerticalIcon,
    TrashIcon,
    PencilIcon,
} from '@heroicons/react/24/outline';
import { useQuizHistory } from '@/lib/QuizHistoryContext';
import { Quiz } from '@/lib/api';
import { useAuth } from '@/lib/AuthContext';

// ============================================================
// CONSTANTS
// ============================================================

interface SidebarProps {
    onNewQuiz: () => void;
    isMobileOpen?: boolean;
    onMobileClose?: () => void;
}

type DateGroup = 'Today' | 'Yesterday' | 'This Week' | 'Older';

const STORAGE_KEYS = {
    collapsed: 'quiz_ai_sidebar_collapsed',
    user: 'quiz_ai_user',
    history: 'quiz_ai_history',
    progress: 'quiz_ai_progress',
    token: 'quiz_ai_token',
} as const;

// ============================================================
// UTILITIES
// ============================================================

function getDateGroup(dateString: string): DateGroup {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
    if (date > weekAgo) return 'This Week';
    return 'Older';
}

function groupQuizzesByDate(quizzes: Quiz[]): Record<DateGroup, Quiz[]> {
    if (!quizzes || !Array.isArray(quizzes)) return {} as Record<DateGroup, Quiz[]>;
    return quizzes.reduce((groups, quiz) => {
        const group = getDateGroup(quiz.created_at);
        if (!groups[group]) groups[group] = [];
        groups[group].push(quiz);
        return groups;
    }, {} as Record<DateGroup, Quiz[]>);
}

// ============================================================
// MAIN COMPONENT
// ============================================================

export default function Sidebar({ onNewQuiz, isMobileOpen = false, onMobileClose }: SidebarProps) {
    const pathname = usePathname();
    const router = useRouter();

    // Context data (Sources of Truth)
    const { authStatus, user, logout } = useAuth();
    const { quizzes, removeQuiz, renameQuiz } = useQuizHistory();

    // UI state
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');

    // Mounted gate to prevent hydration mismatch
    const [isMounted, setIsMounted] = useState(false);
    // The mount gate intentionally synchronizes client-only localStorage state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    useEffect(() => setIsMounted(true), []);

    // Load collapsed state
    useEffect(() => {
        if (!isMounted) return;
        const saved = localStorage.getItem(STORAGE_KEYS.collapsed);
        // This one-time hydration update restores the user's saved preference.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        if (saved === 'true') setIsCollapsed(true);
    }, [isMounted]);

    // Save collapsed state
    useEffect(() => {
        if (isMounted) {
            localStorage.setItem(STORAGE_KEYS.collapsed, String(isCollapsed));
        }
    }, [isCollapsed, isMounted]);

    // Close mobile on route change
    useEffect(() => {
        if (isMobileOpen && onMobileClose) onMobileClose();
    }, [pathname, isMobileOpen, onMobileClose]);

    // Close menus when clicking outside
    useEffect(() => {
        if (!openMenuId) return;

        const handleClick = (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('[data-menu]')) return;
            setOpenMenuId(null);
        };

        const timer = setTimeout(() => {
            document.addEventListener('click', handleClick);
        }, 10);

        return () => {
            clearTimeout(timer);
            document.removeEventListener('click', handleClick);
        };
    }, [openMenuId]);

    // ============================================================
    // HANDLERS
    // ============================================================

    const handleLogout = useCallback(() => {
        setOpenMenuId(null);
        logout();
        router.push('/');
    }, [logout, router]);

    const handleDeleteQuiz = useCallback(async (quizId: string) => {
        await removeQuiz(quizId);
        setOpenMenuId(null);
    }, [removeQuiz]);

    const handleRenameStart = useCallback((quiz: Quiz, e: React.MouseEvent) => {
        e.stopPropagation(); // Stop navigation
        setEditingId(quiz.id);
        setEditingTitle(quiz.topic);
        setOpenMenuId(null);
    }, []);

    const handleRenameFinish = useCallback(async (quizId: string) => {
        const newTopic = editingTitle.trim();
        if (newTopic && newTopic.length > 0) {
            await renameQuiz(quizId, newTopic);
        }
        setEditingId(null);
        setEditingTitle('');
    }, [editingTitle, renameQuiz]);

    const handleNewQuiz = useCallback(() => {
        onNewQuiz();
        onMobileClose?.();
    }, [onNewQuiz, onMobileClose]);

    // ============================================================
    // GROUPED DATA
    // ============================================================

    const groupedQuizzes = groupQuizzesByDate(quizzes);
    const dateOrder: DateGroup[] = ['Today', 'Yesterday', 'This Week', 'Older'];

    // ============================================================
    // RENDER QUIZ ITEM
    // ============================================================

    const renderQuizItem = (quiz: Quiz, closeOnClick?: () => void) => {
        const isEditing = editingId === quiz.id;
        const isMenuOpen = openMenuId === quiz.id;
        // All quizzes use the same URL format now
        const href = `/?quiz=${quiz.id}`;

        if (isEditing) {
            return (
                <div key={quiz.id} className="px-3 py-2">
                    <input
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        onBlur={() => handleRenameFinish(quiz.id)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleRenameFinish(quiz.id);
                            if (e.key === 'Escape') { setEditingId(null); setEditingTitle(''); }
                        }}
                        autoFocus
                        className="w-full bg-[#2A2B2D] border border-indigo-500 rounded-lg px-3 py-2 text-sm text-white outline-none"
                    />
                </div>
            );
        }

        return (
            <div key={quiz.id} className="relative group">
                <Link
                    href={href}
                    onClick={() => closeOnClick?.()}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-[#2A2B2D] transition-colors text-sm"
                >
                    <ChatBubbleLeftIcon className={`w-5 h-5 flex-shrink-0 ${quiz.is_completed ? 'text-green-400' : 'text-gray-500'}`} />
                    <div className="flex-1 min-w-0">
                        <span className="block truncate text-gray-200">{quiz.topic}</span>
                        <span className={`text-xs ${quiz.is_completed ? 'text-green-400' : 'text-yellow-400'}`}>
                            {quiz.is_completed ? `${quiz.score}/${quiz.total} (${quiz.percentage}%)` : 'In progress'}
                        </span>
                    </div>
                </Link>

                {/* Menu Toggle Button */}
                <button
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setOpenMenuId(isMenuOpen ? null : quiz.id);
                    }}
                    className="absolute right-1 top-1/2 -translate-y-1/2 p-1.5 rounded-lg hover:bg-[#383A3C] opacity-0 group-hover:opacity-100 transition-opacity z-10"
                >
                    <EllipsisVerticalIcon className="w-4 h-4 text-gray-500" />
                </button>

                {/* Dropdown Menu - Simple inline with high z-index */}
                {isMenuOpen && (
                    <div
                        data-menu="quiz"
                        className="absolute right-0 top-full mt-1 w-36 bg-[#2A2B2D] rounded-xl shadow-2xl border border-gray-700/50 overflow-hidden z-[9999]"
                    >
                        <button
                            onClick={(e) => {
                                handleRenameStart(quiz, e);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-300 hover:bg-[#383A3C] transition-colors"
                        >
                            <PencilIcon className="w-4 h-4" />
                            <span>Rename</span>
                        </button>
                        <button
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleDeleteQuiz(quiz.id);
                            }}
                            className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-red-400 hover:bg-[#383A3C] transition-colors"
                        >
                            <TrashIcon className="w-4 h-4" />
                            <span>Delete</span>
                        </button>
                    </div>
                )}
            </div>
        );
    };

    // ============================================================
    // RENDER USER SECTION
    // ============================================================

    const renderUserSection = () => {
        // Strict gating to prevent Guest CTA flash during loading
        if (authStatus === 'loading' || !isMounted) {
            return <div className="p-2.5 h-[52px] animate-pulse bg-gray-800/30 rounded-xl mx-2" />;
        }

        if (authStatus === 'guest' || !user) {
            return null; // Sign In button is in header
        }

        const initial = user.name?.charAt(0).toUpperCase() || '?';
        const isMenuOpen = openMenuId === 'user-menu';

        return (
            <div className="relative">
                <button
                    onClick={() => setOpenMenuId(isMenuOpen ? null : 'user-menu')}
                    className="flex items-center justify-between w-full p-2.5 rounded-xl hover:bg-[#2A2B2D] transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold">
                            {initial}
                        </div>
                        <div className="text-left min-w-0">
                            <p className="text-sm font-medium text-white truncate max-w-[120px]">{user.name}</p>
                            <p className="text-xs text-gray-500 truncate max-w-[120px]">{user.email}</p>
                        </div>
                    </div>
                    <ChevronDownIcon className={`w-4 h-4 text-gray-500 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* User Menu Dropdown */}
                {isMenuOpen && (
                    <div
                        data-menu="user"
                        className="absolute left-0 bottom-full mb-2 w-56 bg-[#2A2B2D] rounded-xl border border-gray-700/50 shadow-2xl overflow-hidden z-[9999]"
                    >
                        <div className="p-3 border-b border-gray-700/50">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white font-bold">
                                    {initial}
                                </div>
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-white truncate">{user.name}</p>
                                    <p className="text-xs text-gray-400 truncate">{user.email}</p>
                                </div>
                            </div>
                        </div>
                        <div className="py-1">
                            <Link
                                href="/settings"
                                onClick={() => setOpenMenuId(null)}
                                className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-300 hover:bg-[#383A3C] transition-colors"
                            >
                                <Cog6ToothIcon className="w-4 h-4" />
                                <span>Settings</span>
                            </Link>
                            <button
                                onClick={handleLogout}
                                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-[#383A3C] transition-colors"
                            >
                                <ArrowRightOnRectangleIcon className="w-4 h-4" />
                                <span>Sign Out</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // ============================================================
    // RENDER EXPANDED CONTENT
    // ============================================================

    const renderExpanded = (closeOnClick?: () => void) => (
        <>
            {/* Header */}
            <div className="flex-shrink-0 p-3">
                <div className="mb-3">
                    <button
                        onClick={() => setIsCollapsed(true)}
                        className="p-2 rounded-lg hover:bg-[#2A2B2D] transition-colors"
                    >
                        <Bars3Icon className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                <button
                    onClick={handleNewQuiz}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-full bg-[#2A2B2D] hover:bg-[#383A3C] border border-gray-700/50 transition-colors text-gray-200"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span className="text-sm font-medium">New Quiz</span>
                </button>
            </div>

            {/* History Label */}
            <div className="flex-shrink-0 px-4 py-2">
                <h3 className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Quiz History</h3>
            </div>

            {/* Quiz List or Guest Banner */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 overscroll-contain">
                {(authStatus === 'loading' || !isMounted) ? (
                    <div className="p-4 space-y-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-10 bg-gray-800/30 rounded-lg animate-pulse" />
                        ))}
                    </div>
                ) : (authStatus === 'guest' || !user) ? (
                    /* Guest Mode Banner - no button, just info */
                    <div className="p-4 text-center">
                        <div className="text-gray-500 mb-3">
                            <ChatBubbleLeftIcon className="w-10 h-10 mx-auto opacity-50" />
                        </div>
                        <p className="text-sm text-gray-400">Sign in to save your quiz history</p>
                    </div>
                ) : quizzes.length === 0 ? (
                    /* Empty State for Logged-in Users */
                    <div className="p-4 text-center text-gray-500 text-sm">
                        No quizzes yet. Start a new quiz!
                    </div>
                ) : (
                    /* Quiz History List */
                    dateOrder.map((label) => {
                        const items = groupedQuizzes[label];
                        if (!items?.length) return null;
                        return (
                            <div key={label} className="mb-2">
                                <h4 className="text-[11px] font-medium text-gray-600 px-2 py-1">{label}</h4>
                                {items.map((quiz) => renderQuizItem(quiz, closeOnClick))}
                            </div>
                        );
                    })
                )}
            </div>

            {/* User Section */}
            <div className="flex-shrink-0 border-t border-gray-800/50 p-2">
                {renderUserSection()}
            </div>
        </>
    );

    // ============================================================
    // RENDER COLLAPSED CONTENT (Gemini style - no quiz icons)
    // ============================================================

    const renderCollapsed = () => (
        <>
            <div className="flex-shrink-0 p-2 flex flex-col items-center gap-2">
                <button
                    onClick={() => setIsCollapsed(false)}
                    className="p-3 rounded-lg hover:bg-[#2A2B2D] transition-colors"
                >
                    <Bars3Icon className="w-5 h-5 text-gray-400" />
                </button>
                <button
                    onClick={handleNewQuiz}
                    className="p-3 rounded-lg hover:bg-[#2A2B2D] transition-colors"
                    title="New Quiz"
                >
                    <PlusIcon className="w-5 h-5 text-gray-400" />
                </button>
            </div>

            <div className="flex-1" />

            <div className="flex-shrink-0 p-2 flex flex-col items-center border-t border-gray-800/50">
                {user ? (
                    <Link href="/settings" className="p-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold hover:scale-105 transition-transform">
                            {user.name?.charAt(0).toUpperCase() || '?'}
                        </div>
                    </Link>
                ) : (
                    <Link href="/settings" className="p-3 rounded-lg hover:bg-[#2A2B2D] transition-colors">
                        <Cog6ToothIcon className="w-5 h-5 text-gray-500" />
                    </Link>
                )}
            </div>
        </>
    );

    // ============================================================
    // RENDER MOBILE CONTENT
    // ============================================================

    const renderMobile = () => (
        <>
            <div className="flex-shrink-0 p-3">
                <div className="mb-3">
                    <button onClick={onMobileClose} className="p-2 rounded-lg hover:bg-[#2A2B2D] transition-colors">
                        <XMarkIcon className="w-5 h-5 text-gray-400" />
                    </button>
                </div>
                <button
                    onClick={handleNewQuiz}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-full bg-[#2A2B2D] hover:bg-[#383A3C] border border-gray-700/50 transition-colors text-gray-200"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span className="text-sm font-medium">New Quiz</span>
                </button>
            </div>

            <div className="flex-shrink-0 px-4 py-2">
                <h3 className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">Quiz History</h3>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 overscroll-contain">
                {!user ? (
                    <div className="p-4 text-center">
                        <div className="text-gray-500 mb-3">
                            <ChatBubbleLeftIcon className="w-10 h-10 mx-auto opacity-50" />
                        </div>
                        <p className="text-sm text-gray-400">Sign in to save your quiz history</p>
                    </div>
                ) : quizzes.length === 0 ? (
                    <div className="p-4 text-center text-gray-500 text-sm">
                        No quizzes yet. Start a new quiz!
                    </div>
                ) : (
                    dateOrder.map((label) => {
                        const items = groupedQuizzes[label];
                        if (!items?.length) return null;
                        return (
                            <div key={label} className="mb-2">
                                <h4 className="text-[11px] font-medium text-gray-600 px-2 py-1">{label}</h4>
                                {items.map((quiz) => renderQuizItem(quiz, onMobileClose))}
                            </div>
                        );
                    })
                )}
            </div>

            <div className="flex-shrink-0 border-t border-gray-800/50 p-2">
                {renderUserSection()}
            </div>
        </>
    );

    // ============================================================
    // MAIN RENDER
    // ============================================================

    const sidebarWidth = isCollapsed ? 64 : 260;

    return (
        <>
            {/* Desktop Sidebar */}
            <aside
                className="hidden md:flex flex-col h-screen bg-[#1E1F20] border-r border-gray-800/30 fixed top-0 left-0 z-40 transition-all duration-200"
                style={{ width: sidebarWidth }}
            >
                {isCollapsed ? renderCollapsed() : renderExpanded()}
            </aside>

            {/* Desktop Spacer */}
            <div className="hidden md:block flex-shrink-0 transition-all duration-200" style={{ width: sidebarWidth }} />

            {/* Mobile Backdrop */}
            {isMobileOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden" onClick={onMobileClose} />
            )}

            {/* Mobile Drawer */}
            <aside className={`fixed top-0 left-0 bottom-0 w-[280px] flex flex-col h-screen bg-[#1E1F20] z-50 md:hidden transition-transform duration-300 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                {renderMobile()}
            </aside>
        </>
    );
}
