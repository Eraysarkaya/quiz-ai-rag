'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Bars3Icon } from '@heroicons/react/24/outline';
import { User } from '@/types';

interface HeaderProps {
    title?: string;
    showTimer?: boolean;
    timeRemaining?: number;
    onMenuClick?: () => void;
}

export default function Header({
    title = 'Quiz AI',
    showTimer = false,
    timeRemaining,
    onMenuClick
}: HeaderProps) {
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        // Load user from localStorage
        const loadUser = () => {
            const savedUser = localStorage.getItem('quiz_ai_user');
            if (savedUser) {
                try {
                    const parsed = JSON.parse(savedUser);
                    setUser(parsed);
                } catch {
                    setUser(null);
                }
            } else {
                setUser(null);
            }
        };

        loadUser();

        // Listen for auth events
        const handleAuthLogin = () => loadUser();
        const handleAuthLogout = () => setUser(null);
        const handleStorageChange = () => loadUser();

        window.addEventListener('auth-login', handleAuthLogin);
        window.addEventListener('auth-logout', handleAuthLogout);
        window.addEventListener('storage', handleStorageChange);

        return () => {
            window.removeEventListener('auth-login', handleAuthLogin);
            window.removeEventListener('auth-logout', handleAuthLogout);
            window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <>
            {/* Mobile Header - Sticky */}
            <header className="md:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 border-b border-gray-800/50 bg-[#131314]/95 backdrop-blur-sm safe-area-inset">
                <button
                    onClick={onMenuClick}
                    className="p-2 -ml-2 rounded-xl hover:bg-[#333537] text-gray-400 transition-colors"
                    aria-label="Open menu"
                >
                    <Bars3Icon className="w-6 h-6" />
                </button>

                <div className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-lg">
                        Q
                    </div>
                    <span className="text-base font-semibold text-white">{title}</span>
                </div>

                {/* Right spacer or user avatar */}
                <div className="w-10 flex justify-end">
                    {user && (
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold shadow-lg">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                    )}
                </div>
            </header>

            {/* Desktop Header - Static (not fixed, flows with content) */}
            <header className="hidden md:flex justify-between items-center px-6 py-4 border-b border-gray-800/50 bg-[#131314]">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow-lg">
                        Q
                    </div>
                    <span className="text-lg font-semibold text-white tracking-tight">{title}</span>
                </div>

                <div className="flex items-center gap-4">
                    {/* Timer */}
                    {showTimer && timeRemaining !== undefined && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#2A2B2D] border border-gray-700/50">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-sm text-white font-mono">{formatTime(timeRemaining)}</span>
                        </div>
                    )}

                    {/* Sign In button - only if not logged in */}
                    {!user && (
                        <Link
                            href="/login"
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
                        >
                            Sign In
                        </Link>
                    )}
                </div>
            </header>
        </>
    );
}
