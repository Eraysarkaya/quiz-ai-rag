'use client';

import { useState, useCallback, useEffect, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Sidebar, Header, TopicInput, QuizCard, ScoreDisplay, LoadingSkeleton } from '@/components';
import { QuizQuestion, Difficulty } from '@/types';
import { generateQuiz } from '@/lib/api';
import { useQuizHistory } from '@/lib/QuizHistoryContext';
import { useUserPreferences } from '@/lib/UserPreferencesContext';

type PageView = 'home' | 'quiz' | 'results';

function HomeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { quizzes, isReady, saveQuizToServer, loadQuizzes } = useQuizHistory();

  // Use global preferences context (updated instantly after Settings save)
  const { difficulty: prefDifficulty, questionCount: prefQuestionCount } = useUserPreferences();

  const [currentView, setCurrentView] = useState<PageView>('home');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  // Quiz state
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [lockedQuestions, setLockedQuestions] = useState<Set<string>>(new Set());
  const [showExplanation, setShowExplanation] = useState(false);
  const [quizTopic, setQuizTopic] = useState('');
  const [quizDifficulty, setQuizDifficulty] = useState('medium');
  const [currentQuizId, setCurrentQuizId] = useState<string | null>(null);

  // Track which quiz ID we've loaded to allow re-navigation
  const loadedQuizIdRef = useRef<string | null>(null);

  // Load quiz from URL parameter when context is ready
  // Accept both 'quiz' and 'resume' params for backward compatibility
  useEffect(() => {
    if (!isReady) return;

    const quizId = searchParams.get('quiz') || searchParams.get('resume');

    // No quiz param - reset to home if we were showing a quiz
    if (!quizId) {
      if (loadedQuizIdRef.current) {
        loadedQuizIdRef.current = null;
      }
      return;
    }

    // Already loaded this quiz - don't reload
    if (loadedQuizIdRef.current === quizId) {
      return;
    }

    // Find quiz in the list
    const quiz = quizzes.find(q => q.id === quizId);
    if (quiz) {
      loadedQuizIdRef.current = quizId;
      console.log('[Page] Loading quiz from URL:', quizId, 'status:', quiz.status);

      setQuestions(quiz.questions);
      setQuizTopic(quiz.topic);
      setQuizDifficulty(quiz.difficulty);
      setAnswers(quiz.answers || {});
      setCurrentQuestionIndex(quiz.current_index || 0);
      setCurrentQuizId(quiz.id);

      // Restore locked questions from answers (any answered question is locked)
      // In practice mode, once you check an answer it's locked
      const answeredIds = Object.keys(quiz.answers || {});
      setLockedQuestions(new Set(answeredIds));

      if (quiz.is_completed) {
        // Show results for completed quiz
        setCurrentView('results');
      } else {
        // Resume in-progress quiz
        setCurrentView('quiz');
        // Show explanation if current question was already answered (locked)
        const currentQ = quiz.questions[quiz.current_index || 0];
        if (currentQ && quiz.answers?.[currentQ.id]) {
          setShowExplanation(true);
        }
      }
    }
  }, [isReady, searchParams, quizzes]);

  // Save progress when quiz state changes (debounced)
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingSaveRef = useRef<((isFlush?: boolean) => void) | null>(null);

  // Common save function
  const executeSave = useCallback((isFlush = false) => {
    if (!currentQuizId || questions.length === 0) return;

    saveQuizToServer({
      quizId: currentQuizId,
      topic: quizTopic,
      difficulty: quizDifficulty,
      questions,
      answers,
      currentIndex: currentQuestionIndex,
      status: 'in_progress'
    }, { keepalive: isFlush }); // Use beacon/keepalive for flush

    if (isFlush) {
      pendingSaveRef.current = null;
    }
  }, [currentQuizId, questions, answers, currentQuestionIndex, quizTopic, quizDifficulty, saveQuizToServer]);

  // Flush pending save (for beforeunload/visibilitychange)
  const flushSave = useCallback(() => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = null;
    }
    // Always save on flush to capture latest state, even if no pending timeout
    // (Ensure we capture the very last millisecond of state)
    executeSave(true);
  }, [executeSave]);

  // Add beforeunload listener to save on tab close
  useEffect(() => {
    const handleBeforeUnload = () => flushSave();
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') flushSave();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [flushSave]);

  // Auto-save effect
  useEffect(() => {
    if (currentView !== 'quiz' || !currentQuizId || questions.length === 0) return;

    // Clear previous timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Debounce save (200ms)
    saveTimeoutRef.current = setTimeout(() => executeSave(false), 200);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [currentView, currentQuizId, questions, answers, currentQuestionIndex, quizTopic, quizDifficulty, executeSave]);

  const handleNewQuiz = useCallback(() => {
    setCurrentView('home');
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setLockedQuestions(new Set());
    setShowExplanation(false);
    setError(null);
    setSuggestions([]);
    setCurrentQuizId(null);
    loadedQuizIdRef.current = null;
    router.push('/');
  }, [router]);

  const handleGenerateQuiz = async (topic: string, difficulty: Difficulty, numQuestions: number) => {
    setIsLoading(true);
    setError(null);
    setSuggestions([]);
    setQuizTopic(topic);
    setQuizDifficulty(difficulty);

    try {
      const response = await generateQuiz({
        topic,
        difficulty,
        num_questions: numQuestions,
      });

      if (!response.questions || response.questions.length === 0) {
        setError(response.error || 'Failed to generate quiz - no questions returned');
        if (response.suggestions) {
          setSuggestions(response.suggestions);
        }
        setIsLoading(false);
        return;
      }

      if (response.success === false) {
        setError(response.error || 'Failed to generate quiz');
        if (response.suggestions) {
          setSuggestions(response.suggestions);
        }
        setIsLoading(false);
        return;
      }

      // Save new quiz to server immediately
      const savedQuiz = await saveQuizToServer({
        topic,
        difficulty,
        questions: response.questions,
        answers: {},
        currentIndex: 0,
        status: 'in_progress'
      });

      // Reload quizzes to update sidebar
      await loadQuizzes();

      // Get the quiz ID from response
      const quizId = savedQuiz?.id || 'quiz_' + Date.now();

      setCurrentQuizId(quizId);
      setQuestions(response.questions);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setLockedQuestions(new Set());
      setShowExplanation(false);
      setCurrentView('quiz');

      // Update URL with quiz ID
      router.push(`/?quiz=${quizId}`, { scroll: false });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectAnswer = (answer: string) => {
    const currentQuestion = questions[currentQuestionIndex];
    // Only allow changing answer if question is not locked
    if (!lockedQuestions.has(currentQuestion.id)) {
      setAnswers(prev => ({ ...prev, [currentQuestion.id]: answer }));
    }
  };

  const handleCheckAnswer = () => {
    const currentQuestion = questions[currentQuestionIndex];
    // Lock this question after checking
    setLockedQuestions(prev => new Set([...prev, currentQuestion.id]));
    setShowExplanation(true);
  };

  const handleNext = async () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      // When navigating, show explanation only if next question is locked
      const nextQuestion = questions[currentQuestionIndex + 1];
      setShowExplanation(lockedQuestions.has(nextQuestion.id));
    } else {
      // Quiz completed
      const correctCount = questions.filter(q => answers[q.id] === q.correct).length;

      // Save as completed
      if (currentQuizId) {
        await saveQuizToServer({
          quizId: currentQuizId,
          topic: quizTopic,
          difficulty: quizDifficulty,
          questions,
          answers,
          currentIndex: questions.length - 1,
          score: correctCount,
          status: 'completed'
        });
        await loadQuizzes();
      }

      setCurrentView('results');
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      const prevQuestion = questions[currentQuestionIndex - 1];
      // Show explanation if previous question is locked
      setShowExplanation(lockedQuestions.has(prevQuestion.id));
    }
  };

  const handleRetake = async () => {
    if (!currentQuizId) return;

    // Reset quiz on server FIRST (server is source of truth)
    await saveQuizToServer({
      quizId: currentQuizId,
      topic: quizTopic,
      difficulty: quizDifficulty,
      questions,
      answers: {},
      currentIndex: 0,
      score: 0,
      status: 'in_progress'
    });

    // Refresh sidebar to show "in progress" status
    await loadQuizzes();

    // Reset loadedQuizIdRef to allow reloading this quiz
    loadedQuizIdRef.current = null;

    // Reset local state and show quiz view
    setCurrentQuestionIndex(0);
    setAnswers({});
    setLockedQuestions(new Set());
    setShowExplanation(false);
    setCurrentView('quiz');

    // Update URL to ensure clean state (re-triggers load if needed)
    router.push(`/?quiz=${currentQuizId}`, { scroll: false });
  };

  const currentQuestion = questions[currentQuestionIndex];
  const selectedAnswer = currentQuestion ? answers[currentQuestion.id] : null;
  // Mobile sidebar state
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex bg-[#131314]">
      <Sidebar
        onNewQuiz={handleNewQuiz}
        isMobileOpen={isMobileSidebarOpen}
        onMobileClose={() => setIsMobileSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        <Header onMenuClick={() => setIsMobileSidebarOpen(true)} />

        <div className="flex-1 flex items-center justify-center p-4 md:p-8">
          {isLoading && (
            <LoadingSkeleton message={`Generating quiz about "${quizTopic}"...`} />
          )}

          {!isLoading && currentView === 'home' && (
            <div className="animate-fade-in w-full">
              <TopicInput
                onSubmit={handleGenerateQuiz}
                isLoading={isLoading}
                suggestedTopics={suggestions}
                initialDifficulty={prefDifficulty}
                initialQuestionCount={prefQuestionCount}
                error={error}
                onClearError={() => setError(null)}
              />
            </div>
          )}

          {currentView === 'quiz' && currentQuestion && (
            <div className="animate-fade-in w-full">
              <QuizCard
                question={currentQuestion}
                questionNumber={currentQuestionIndex + 1}
                totalQuestions={questions.length}
                selectedAnswer={selectedAnswer || undefined}
                showResult={showExplanation || lockedQuestions.has(currentQuestion.id)}
                isLocked={lockedQuestions.has(currentQuestion.id)}
                onSelectAnswer={handleSelectAnswer}
                onCheckAnswer={handleCheckAnswer}
                onNext={handleNext}
                onPrevious={currentQuestionIndex > 0 ? handlePrevious : undefined}
              />
            </div>
          )}

          {currentView === 'results' && (
            <div className="animate-fade-in w-full">
              <ScoreDisplay
                topic={quizTopic}
                questions={questions}
                answers={answers}
                onRetake={handleRetake}
                onNewQuiz={handleNewQuiz}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Wrap with Suspense for useSearchParams
export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#131314]" />}>
      <HomeContent />
    </Suspense>
  );
}
