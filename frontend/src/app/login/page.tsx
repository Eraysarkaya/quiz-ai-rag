'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/AuthContext';

export default function LoginPage() {
    const router = useRouter();
    const { login, loginWithGoogle, register, isLoading } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            if (isRegister) {
                if (!name.trim()) {
                    setError('Please enter your name');
                    return;
                }
                const success = await register(name, email, password);
                if (success) {
                    // Registration successful - switch to login mode with success message
                    // Do NOT auto-redirect to home; user should sign in explicitly
                    setIsRegister(false);
                    setName('');
                    setPassword('');
                    // Keep email so user can easily log in
                    setError(''); // Clear any error
                    // Show success as a custom message (we'll use a success state)
                    alert('Account created successfully! Please sign in with your credentials.');
                } else {
                    setError('Registration failed. Please try again.');
                }
            } else {
                const success = await login(email, password);
                if (success) {
                    router.push('/');
                } else {
                    setError('Invalid email or password');
                }
            }
        } catch {
            setError('An error occurred. Please try again.');
        }
    };

    const handleGoogleLogin = async () => {
        const success = await loginWithGoogle();
        if (success) {
            router.push('/');
        }
    };

    return (
        <div className="min-h-screen bg-[#131314] text-white flex flex-col relative overflow-hidden">
            {/* Header */}
            <header className="w-full p-6 flex justify-between items-center z-20">
                <Link href="/" className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow-lg">
                        Q
                    </div>
                    <span className="text-xl font-semibold tracking-tight">Quiz AI</span>
                </Link>
            </header>

            {/* Background Blurs */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

            {/* Main Content */}
            <main className="flex-1 flex items-center justify-center p-4 z-10">
                <div className="w-full max-w-[420px] bg-[#1E1F20] rounded-3xl border border-gray-800 p-8 sm:p-10">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-bold mb-2">
                            {isRegister ? 'Create account' : 'Welcome back'}
                        </h1>
                        <p className="text-gray-400 text-sm">
                            {isRegister
                                ? 'Start your learning journey today'
                                : 'Sign in to continue your learning journey'}
                        </p>
                    </div>

                    {/* Google Login */}
                    <button
                        onClick={handleGoogleLogin}
                        disabled={isLoading}
                        className="w-full flex items-center justify-center space-x-3 bg-[#2A2B2D] hover:bg-[#333537] border border-gray-700 py-3 px-4 rounded-xl transition-all disabled:opacity-50"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        <span className="font-medium text-sm">Continue with Google</span>
                    </button>

                    {/* Divider */}
                    <div className="relative flex py-6 items-center">
                        <div className="flex-grow border-t border-gray-700" />
                        <span className="flex-shrink-0 mx-4 text-xs font-medium text-gray-500 uppercase">Or</span>
                        <div className="flex-grow border-t border-gray-700" />
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {isRegister && (
                            <div>
                                <label className="block text-xs font-semibold text-gray-400 mb-1.5 ml-1">
                                    Full Name
                                </label>
                                <div className="relative">
                                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                    </div>
                                    <input
                                        type="text"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full bg-[#131314] border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-sm placeholder-gray-500 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                                        placeholder="John Doe"
                                    />
                                </div>
                            </div>
                        )}

                        <div>
                            <label className="block text-xs font-semibold text-gray-400 mb-1.5 ml-1">
                                Email
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#131314] border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-sm placeholder-gray-500 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-1.5 ml-1">
                                <label className="block text-xs font-semibold text-gray-400">
                                    Password
                                </label>
                                {!isRegister && (
                                    <a href="#" className="text-xs font-medium text-indigo-500 hover:text-indigo-400">
                                        Forgot password?
                                    </a>
                                )}
                            </div>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#131314] border border-gray-700 rounded-xl py-3 pl-10 pr-4 text-sm placeholder-gray-500 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <p className="text-red-500 text-sm text-center">{error}</p>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3.5 px-4 rounded-xl shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
                        >
                            <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                        </button>
                    </form>

                    {/* Toggle */}
                    <div className="mt-8 text-center border-t border-gray-700/50 pt-6">
                        <p className="text-sm text-gray-400">
                            {isRegister ? 'Already have an account?' : "Don't have an account?"}
                            <button
                                onClick={() => setIsRegister(!isRegister)}
                                className="font-semibold text-indigo-500 hover:text-indigo-400 ml-1"
                            >
                                {isRegister ? 'Sign in' : 'Create account'}
                            </button>
                        </p>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="p-6 text-center z-10">
                <p className="text-[11px] text-gray-500">
                    © 2024 Quiz AI. All rights reserved.
                </p>
            </footer>
        </div>
    );
}
