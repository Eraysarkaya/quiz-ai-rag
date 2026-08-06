'use client';

import { AuthProvider } from '@/lib/AuthContext';
import { QuizHistoryProvider } from '@/lib/QuizHistoryContext';
import { UserPreferencesProvider } from '@/lib/UserPreferencesContext';
import { ToastProvider } from '@/lib/ToastContext';

export default function Providers({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <ToastProvider>
                <UserPreferencesProvider>
                    <QuizHistoryProvider>
                        {children}
                    </QuizHistoryProvider>
                </UserPreferencesProvider>
            </ToastProvider>
        </AuthProvider>
    );
}

