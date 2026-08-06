'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

function GoogleCallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [error, setError] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(true);

    useEffect(() => {
        const handleCallback = async () => {
            const code = searchParams.get('code');
            const state = searchParams.get('state');
            const errorParam = searchParams.get('error');

            if (errorParam) {
                setError(`Google authentication failed: ${errorParam}`);
                setIsProcessing(false);
                return;
            }

            if (!code) {
                setError('No authorization code received');
                setIsProcessing(false);
                return;
            }

            // Verify state
            const savedState = sessionStorage.getItem('google_oauth_state');
            if (state !== savedState) {
                setError('Invalid state parameter');
                setIsProcessing(false);
                return;
            }
            sessionStorage.removeItem('google_oauth_state');

            try {
                // Exchange code for tokens via backend
                const response = await fetch(`${API_URL}/auth/google/callback`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code,
                        redirect_uri: `${window.location.origin}/auth/google/callback`
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('quiz_ai_token', data.access_token);
                    localStorage.setItem('quiz_ai_user', JSON.stringify(data.user));

                    // Dispatch auth-login event to notify all components
                    window.dispatchEvent(new Event('auth-login'));

                    // Small delay to ensure event is processed before navigation
                    await new Promise(resolve => setTimeout(resolve, 50));

                    // Redirect to home
                    router.push('/');
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    setError(errorData.detail || 'Authentication failed');
                    setIsProcessing(false);
                }
            } catch (err) {
                console.error('Google callback error:', err);
                setError('Failed to complete authentication');
                setIsProcessing(false);
            }
        };

        handleCallback();
    }, [searchParams, router]);

    if (isProcessing) {
        return (
            <div className="min-h-screen bg-[#131314] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-400">Signing in with Google...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#131314] flex items-center justify-center">
                <div className="text-center max-w-md p-6">
                    <div className="text-red-500 text-6xl mb-4">⚠️</div>
                    <h1 className="text-xl font-semibold text-white mb-2">Authentication Failed</h1>
                    <p className="text-gray-400 mb-6">{error}</p>
                    <button
                        onClick={() => router.push('/login')}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return null;
}

export default function GoogleCallbackPage() {
    return (
        <Suspense fallback={(
            <div className="min-h-screen bg-[#131314] flex items-center justify-center">
                <p className="text-gray-400">Preparing sign in...</p>
            </div>
        )}>
            <GoogleCallbackContent />
        </Suspense>
    );
}
