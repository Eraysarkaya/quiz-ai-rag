'use client';

import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { QuizQuestion } from '@/types';

interface ScoreDisplayProps {
    questions: QuizQuestion[];
    answers: Record<string, string>;
    topic: string;
    onRetake?: () => void;
    onNewQuiz?: () => void;
}

export default function ScoreDisplay({
    questions,
    answers,
    topic,
    onRetake,
    onNewQuiz,
}: ScoreDisplayProps) {
    const totalQuestions = questions.length;
    const correctCount = questions.filter(q => answers[q.id] === q.correct).length;
    const incorrectCount = totalQuestions - correctCount;
    const percentage = Math.round((correctCount / totalQuestions) * 100);

    const getMessage = () => {
        if (percentage >= 80) return { text: 'Excellent Work!', emoji: '🎉' };
        if (percentage >= 60) return { text: 'Good Job!', emoji: '👍' };
        if (percentage >= 40) return { text: 'Keep Practicing!', emoji: '💪' };
        return { text: 'Room for Improvement', emoji: '📚' };
    };

    const message = getMessage();

    return (
        <div className="max-w-4xl mx-auto w-full animate-fade-in">
            {/* Score Card */}
            <div className="bg-[#1E1F20] rounded-3xl border border-gray-800 p-6 md:p-8 mb-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-8 md:gap-12">
                    {/* Score Circle */}
                    <div className="flex flex-col items-center flex-shrink-0">
                        <div
                            className="relative w-40 h-40 rounded-full flex items-center justify-center shadow-2xl shadow-indigo-500/10"
                            style={{
                                background: `conic-gradient(#4F46E5 ${percentage}%, #333537 0)`
                            }}
                        >
                            <div className="absolute inset-2 bg-[#1E1F20] rounded-full flex flex-col items-center justify-center">
                                <span className="text-5xl font-bold text-white">{percentage}%</span>
                                <span className="text-xs text-gray-500 font-medium mt-1">Score</span>
                            </div>
                        </div>
                    </div>

                    {/* Message and Stats */}
                    <div className="flex-1 text-center md:text-left">
                        <h2 className="text-3xl font-bold text-white mb-2 flex items-center justify-center md:justify-start gap-2">
                            {message.emoji} {message.text}
                        </h2>
                        <p className="text-gray-400 text-sm md:text-base leading-relaxed mb-6">
                            You completed the quiz on <span className="text-white font-medium">{topic}</span>.
                            {percentage >= 80 && " Outstanding performance!"}
                            {percentage >= 60 && percentage < 80 && " You're on the right track!"}
                            {percentage < 60 && " Review the explanations to learn more."}
                        </p>

                        {/* Stats Grid - 2 columns (no time) */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-green-900/10 border border-green-900/30 p-3 rounded-xl flex flex-col items-center md:items-start">
                                <div className="flex items-center space-x-1 mb-1">
                                    <CheckCircleIcon className="w-4 h-4 text-green-500" />
                                    <span className="text-xs font-bold text-green-400 uppercase">Correct</span>
                                </div>
                                <span className="text-xl font-bold text-white">
                                    {correctCount}<span className="text-sm font-normal text-gray-500">/{totalQuestions}</span>
                                </span>
                            </div>

                            <div className="bg-red-900/10 border border-red-900/30 p-3 rounded-xl flex flex-col items-center md:items-start">
                                <div className="flex items-center space-x-1 mb-1">
                                    <XCircleIcon className="w-4 h-4 text-red-500" />
                                    <span className="text-xs font-bold text-red-400 uppercase">Incorrect</span>
                                </div>
                                <span className="text-xl font-bold text-white">{incorrectCount}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 mt-8 justify-center">
                    <button
                        onClick={onRetake}
                        className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center space-x-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        <span>Retake Quiz</span>
                    </button>

                    <button
                        onClick={onNewQuiz}
                        className="px-6 py-3 rounded-xl bg-[#2A2B2D] hover:bg-[#383A3C] border border-gray-700 text-white text-sm font-medium transition-all flex items-center justify-center space-x-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        <span>New Quiz</span>
                    </button>
                </div>
            </div>

            {/* Review Section */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white">Review Answers</h3>
                </div>

                {questions.map((question, index) => {
                    const userAnswer = answers[question.id];
                    const isCorrect = userAnswer === question.correct;

                    return (
                        <div
                            key={question.id}
                            className="bg-[#1E1F20] rounded-2xl border border-gray-800 p-6 relative overflow-hidden"
                        >
                            <div className={`absolute left-0 top-0 bottom-0 w-1 ${isCorrect ? 'bg-green-500' : 'bg-red-500'}`} />

                            <div className="flex items-start justify-between mb-4 pl-3">
                                <div>
                                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 block">
                                        Question {index + 1}
                                    </span>
                                    <h4 className="text-lg font-medium text-white">{question.question}</h4>
                                </div>
                                <div className={`hidden sm:flex items-center space-x-1 px-3 py-1 rounded-full border ${isCorrect
                                    ? 'text-green-500 bg-green-900/10 border-green-900/20'
                                    : 'text-red-500 bg-red-900/10 border-red-900/20'
                                    }`}>
                                    {isCorrect ? (
                                        <CheckCircleIcon className="w-4 h-4" />
                                    ) : (
                                        <XCircleIcon className="w-4 h-4" />
                                    )}
                                    <span className="text-xs font-bold uppercase">{isCorrect ? 'Correct' : 'Incorrect'}</span>
                                </div>
                            </div>

                            {/* Options Grid */}
                            <div className="pl-3 grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                                {Object.entries(question.options).map(([label, text]) => {
                                    const isUserAnswer = userAnswer === label;
                                    const isCorrectOption = question.correct === label;

                                    let classes = "p-3 rounded-lg border flex items-center justify-between";
                                    if (isCorrectOption) {
                                        classes += " border-2 border-green-500 bg-green-900/10";
                                    } else if (isUserAnswer && !isCorrect) {
                                        classes += " border-2 border-red-500 bg-red-900/10";
                                    } else {
                                        classes += " border-gray-700 opacity-60";
                                    }

                                    return (
                                        <div key={label} className={classes}>
                                            <span className="text-sm font-medium text-white">{label}. {text}</span>
                                            {isCorrectOption && <CheckCircleIcon className="w-5 h-5 text-green-500" />}
                                            {isUserAnswer && !isCorrect && <XCircleIcon className="w-5 h-5 text-red-500" />}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Explanation */}
                            {question.explanation && (
                                <div className="ml-3 bg-[#2A2B2D] rounded-xl p-4 flex gap-3">
                                    <svg className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
                                    </svg>
                                    <div>
                                        <p className="text-xs font-bold text-gray-400 uppercase mb-1">Explanation</p>
                                        <p className="text-sm text-gray-400 leading-relaxed">{question.explanation}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
