'use client';

import { CheckCircleIcon, XCircleIcon, LightBulbIcon } from '@heroicons/react/24/solid';
import { QuizQuestion } from '@/types';

interface QuizCardProps {
    question: QuizQuestion;
    questionNumber: number;
    totalQuestions: number;
    selectedAnswer?: string;
    showResult?: boolean;
    isLocked?: boolean;  // Whether answer has been checked/locked
    onSelectAnswer: (answer: string) => void;
    onCheckAnswer: () => void;
    onPrevious?: () => void;
    onNext?: () => void;
}

export default function QuizCard({
    question,
    questionNumber,
    totalQuestions,
    selectedAnswer,
    showResult = false,
    isLocked = false,
    onSelectAnswer,
    onCheckAnswer,
    onPrevious,
    onNext,
}: QuizCardProps) {
    const isCorrect = selectedAnswer === question.correct;
    const progress = (questionNumber / totalQuestions) * 100;
    const optionLabels = Object.keys(question.options);

    return (
        <div className="max-w-3xl mx-auto w-full animate-fade-in">
            {/* Progress Bar */}
            <div className="mb-8">
                <div className="flex justify-between items-end mb-2">
                    <div>
                        <span className="text-xs font-bold text-indigo-500 tracking-wider uppercase">
                            Question {questionNumber}
                        </span>
                        <span className="text-xs text-gray-500 uppercase tracking-wider ml-1">
                            of {totalQuestions}
                        </span>
                    </div>
                    <span className="text-xs text-gray-500">{Math.round(progress)}% Completed</span>
                </div>
                <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                    <div
                        className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Question Card */}
            <div className="bg-[#1E1F20] rounded-3xl border border-gray-800 p-6 md:p-10 mb-6">
                <h2 className="text-xl md:text-2xl font-medium text-white mb-8 leading-relaxed">
                    {question.question}
                </h2>

                {/* Options */}
                <div className="space-y-3">
                    {optionLabels.map((label) => {
                        const isSelected = selectedAnswer === label;
                        const isCorrectOption = label === question.correct;

                        let optionClasses = "flex items-center p-4 rounded-xl border cursor-pointer transition-all";

                        if (showResult) {
                            if (isCorrectOption) {
                                optionClasses += " border-2 border-green-500 bg-green-900/10";
                            } else if (isSelected && !isCorrect) {
                                optionClasses += " border-2 border-red-500 bg-red-900/10";
                            } else {
                                optionClasses += " border-gray-700 opacity-60";
                            }
                        } else if (isSelected) {
                            optionClasses += " border-2 border-indigo-500 bg-indigo-900/10";
                        } else {
                            optionClasses += " border-gray-700 hover:bg-[#2A2B2D] hover:border-gray-600";
                        }

                        return (
                            <label
                                key={label}
                                className={`${optionClasses} select-none`}
                                onClick={() => !showResult && !isLocked && onSelectAnswer(label)}
                            >
                                {/* Custom radio indicator instead of native input */}
                                <div className={`
                                    w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0
                                    transition-colors duration-150
                                    ${isSelected
                                        ? 'border-indigo-500 bg-indigo-500'
                                        : 'border-gray-600 bg-transparent'
                                    }
                                    ${showResult && isCorrectOption ? 'border-green-500 bg-green-500' : ''}
                                    ${showResult && isSelected && !isCorrect ? 'border-red-500 bg-red-500' : ''}
                                `}>
                                    {isSelected && (
                                        <div className="w-2 h-2 rounded-full bg-white" />
                                    )}
                                </div>
                                <span className="ml-4 text-white font-medium flex-1">
                                    {label}. {question.options[label]}
                                </span>
                                {showResult && isCorrectOption && (
                                    <CheckCircleIcon className="w-6 h-6 text-green-500" />
                                )}
                                {showResult && isSelected && !isCorrect && (
                                    <XCircleIcon className="w-6 h-6 text-red-500" />
                                )}
                            </label>
                        );
                    })}
                </div>

                {/* Action Buttons */}
                <div className="mt-8 flex items-center justify-between">
                    <button
                        onClick={onPrevious}
                        disabled={questionNumber === 1}
                        className="px-6 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        <span>Previous</span>
                    </button>

                    {!showResult ? (
                        <button
                            onClick={onCheckAnswer}
                            disabled={!selectedAnswer}
                            className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all transform hover:scale-105 active:scale-95 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            <span>Check Answer</span>
                            <CheckCircleIcon className="w-5 h-5" />
                        </button>
                    ) : (
                        <button
                            onClick={onNext}
                            className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all transform hover:scale-105 active:scale-95 flex items-center space-x-2"
                        >
                            <span>{questionNumber === totalQuestions ? 'See Results' : 'Next Question'}</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    )}
                </div>
            </div>

            {/* Explanation */}
            {showResult && question.explanation && (
                <div className={`
          bg-[#1E1F20] border rounded-2xl p-6 flex gap-4 relative overflow-hidden
          ${isCorrect ? 'border-green-500/30' : 'border-gray-700'}
        `}>
                    <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${isCorrect ? 'bg-green-500' : 'bg-indigo-500'}`} />
                    <div className="flex-shrink-0 mt-1">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${isCorrect ? 'bg-green-900/30 text-green-400' : 'bg-indigo-900/30 text-indigo-400'}`}>
                            <LightBulbIcon className="w-5 h-5" />
                        </div>
                    </div>
                    <div className="flex-1">
                        <h4 className="text-sm font-bold text-white mb-1 flex items-center">
                            Explanation
                            <span className={`ml-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${isCorrect ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                                {isCorrect ? 'Correct' : 'Incorrect'}
                            </span>
                        </h4>
                        <p className="text-sm text-gray-400 leading-relaxed">
                            {question.explanation}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
