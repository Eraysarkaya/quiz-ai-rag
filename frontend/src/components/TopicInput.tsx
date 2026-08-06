'use client';

import { useState, useEffect } from 'react';
import {
    SignalIcon,
    ListBulletIcon,
    PaperAirplaneIcon
} from '@heroicons/react/24/outline';
import { Difficulty } from '@/types';
import { useAuth } from '@/lib/AuthContext';

interface TopicInputProps {
    onSubmit: (topic: string, difficulty: Difficulty, numQuestions: number) => void;
    isLoading?: boolean;
    suggestedTopics?: string[];
    initialDifficulty?: Difficulty;
    initialQuestionCount?: number;
    error?: string | null;
    onClearError?: () => void;
}

export default function TopicInput({
    onSubmit,
    isLoading = false,
    initialDifficulty = 'medium',
    initialQuestionCount = 5,
    error = null,
    onClearError
}: TopicInputProps) {
    const { user } = useAuth();
    const [topic, setTopic] = useState('');
    const [difficulty, setDifficulty] = useState<Difficulty>(initialDifficulty);
    const [numQuestions, setNumQuestions] = useState(initialQuestionCount);
    const [showDifficultyMenu, setShowDifficultyMenu] = useState(false);
    const [showQuestionsMenu, setShowQuestionsMenu] = useState(false);

    // Get user name from AuthContext (reactive)
    const userName = user?.name?.split(' ')[0] || 'Learner';

    // Sync with initial values when they change (e.g., after preferences load)
    useEffect(() => {
        setDifficulty(initialDifficulty);
    }, [initialDifficulty]);

    useEffect(() => {
        setNumQuestions(initialQuestionCount);
    }, [initialQuestionCount]);

    const handleSubmit = () => {
        if (topic.trim() && !isLoading) {
            onSubmit(topic.trim(), difficulty, numQuestions);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        setTopic(suggestion);
        onSubmit(suggestion, difficulty, numQuestions);
    };

    const defaultTopics = [
        { emoji: '⚛️', title: 'Physics', description: 'Laws of motion, energy' },
        { emoji: '🧬', title: 'Biology', description: 'Cells, genetics, evolution' },
        { emoji: '🧪', title: 'Chemistry', description: 'Atoms, reactions, elements' },
        { emoji: '🌍', title: 'Earth Science', description: 'Climate, geology, oceans' },
    ];

    return (
        <div className="w-full space-y-6">
            {/* Welcome Text */}
            <div className="space-y-1 mb-6 text-center md:text-left">
                <h1 className="text-xl sm:text-3xl md:text-4xl font-semibold">
                    <span className="gradient-text">Hello, {userName}</span>
                </h1>
                <p className="text-lg sm:text-2xl md:text-3xl font-normal text-gray-500">
                    What would you like to quiz today?
                </p>
            </div>

            {/* Input Card */}
            <div className="bg-[#1E1F20] rounded-3xl border border-gray-800 p-4 transition-colors duration-200">
                <div className="flex flex-col space-y-4">
                    <textarea
                        value={topic}
                        onChange={(e) => {
                            setTopic(e.target.value);
                            if (error && onClearError) onClearError();
                        }}
                        onKeyPress={handleKeyPress}
                        className="w-full bg-transparent border-none focus:ring-0 text-white text-lg placeholder-gray-500 resize-none h-16 sm:h-24"
                        placeholder="Enter a science topic (e.g., 'Photosynthesis', 'DNA Replication')..."
                        disabled={isLoading}
                    />

                    <div className="flex flex-wrap items-center justify-between gap-4 mt-2">
                        <div className="flex flex-wrap items-center gap-2">
                            {/* Difficulty Dropdown */}
                            <div className="relative">
                                <button
                                    onClick={() => setShowDifficultyMenu(!showDifficultyMenu)}
                                    className="flex items-center space-x-1 px-3 py-1.5 rounded-full bg-[#2A2B2D] hover:bg-[#383A3C] text-sm text-white transition-colors"
                                >
                                    <SignalIcon className="w-4 h-4" />
                                    <span className="capitalize">{difficulty}</span>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>
                                {showDifficultyMenu && (
                                    <div className="absolute bottom-full mb-2 left-0 w-32 bg-[#2A2B2D] rounded-xl shadow-2xl border border-gray-700/50 overflow-hidden z-[100] backdrop-blur-sm">
                                        {(['easy', 'medium', 'hard'] as Difficulty[]).map((d) => (
                                            <button
                                                key={d}
                                                onClick={() => { setDifficulty(d); setShowDifficultyMenu(false); }}
                                                className="block w-full px-4 py-2.5 text-sm text-white hover:bg-[#383A3C] text-left capitalize transition-colors"
                                            >
                                                {d}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Questions Count Dropdown */}
                            <div className="relative">
                                <button
                                    onClick={() => setShowQuestionsMenu(!showQuestionsMenu)}
                                    className="flex items-center space-x-1 px-3 py-1.5 rounded-full bg-[#2A2B2D] hover:bg-[#383A3C] text-sm text-white transition-colors"
                                >
                                    <ListBulletIcon className="w-4 h-4" />
                                    <span>{numQuestions} Questions</span>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>
                                {showQuestionsMenu && (
                                    <div className="absolute bottom-full mb-2 left-0 w-36 bg-[#2A2B2D] rounded-xl shadow-2xl border border-gray-700/50 overflow-hidden z-[100] backdrop-blur-sm">
                                        {[3, 5, 10].map((n) => (
                                            <button
                                                key={n}
                                                onClick={() => { setNumQuestions(n); setShowQuestionsMenu(false); }}
                                                className="block w-full px-4 py-2.5 text-sm text-white hover:bg-[#383A3C] text-left transition-colors"
                                            >
                                                {n} Questions
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Submit Button */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 hidden sm:block">
                                Generate Quiz
                            </span>
                            <button
                                onClick={handleSubmit}
                                disabled={!topic.trim() || isLoading}
                                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg p-2 transition-colors flex items-center justify-center shadow-md shadow-indigo-500/20"
                            >
                                {isLoading ? (
                                    <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full spinner" />
                                ) : (
                                    <PaperAirplaneIcon className="w-6 h-6" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 animate-fade-in">
                    <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <p className="text-sm font-medium text-red-400">Topic not recognized</p>
                        <p className="text-xs text-gray-400 mt-1">{error}</p>
                    </div>
                </div>
            )}

            {/* Suggestion Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 w-full">
                {defaultTopics.map((item, index) => (
                    <button
                        key={index}
                        onClick={() => {
                            if (onClearError) onClearError();
                            handleSuggestionClick(item.title);
                        }}
                        className="flex flex-col items-start p-4 rounded-xl bg-[#1E1F20] hover:bg-[#2A2B2D] transition-colors text-left group h-full border border-gray-800"
                    >
                        <div className="bg-black/20 p-2 rounded-lg mb-2 group-hover:scale-110 transition-transform">
                            <span className="text-xl">{item.emoji}</span>
                        </div>
                        <span className="text-sm font-medium text-white mb-1">{item.title}</span>
                        <span className="text-xs text-gray-500">{item.description}</span>
                    </button>
                ))}
            </div>

            {/* Footer */}
            <div className="text-center mt-8">
                <p className="text-[10px] sm:text-xs text-gray-500">
                    Powered by AI · Questions generated from verified scientific sources
                </p>
                <p className="text-[10px] sm:text-xs text-gray-600 mt-2">
                    <a className="hover:text-gray-400" href="/terms">Terms</a>
                    {' · '}
                    <a className="hover:text-gray-400" href="/privacy">Privacy</a>
                </p>
            </div>
        </div>
    );
}
