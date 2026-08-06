"""
Quiz Service - Clean Backend Implementation
Async wrapper around the Quiz Pipeline for FastAPI
"""
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..config import get_settings, POPULAR_TOPICS
from ..core.pipeline import QuizPipeline

settings = get_settings()


@dataclass
class QuizServiceResult:
    """Result from quiz generation."""
    success: bool
    questions: List[dict] = None
    error: str = None
    message: str = None
    suggestions: List[str] = None


class QuizService:
    """
    Quiz generation service using RAG pipeline.
    Async wrapper for FastAPI integration.
    """
    
    def __init__(self):
        """Initialize the quiz service."""
        self._pipeline = None
        self._initialized = False
    
    def _get_pipeline(self):
        """Lazy load the pipeline."""
        if self._pipeline is None:
            try:
                print("⚙️ Initializing QuizPipeline from backend/app/core...")
                self._pipeline = QuizPipeline()
                self._initialized = True
                print("✅ Pipeline initialized successfully")
            except ImportError as e:
                print(f"❌ Could not import pipeline: {e}")
                raise
            except Exception as e:
                print(f"❌ Error initializing pipeline: {e}")
                import traceback
                traceback.print_exc()
                raise
        return self._pipeline
    
    async def generate_quiz(
        self,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 3
    ) -> dict:
        """
        Generate a quiz on the given topic.
        
        Args:
            topic: Science topic
            difficulty: easy/medium/hard
            num_questions: Number of questions (1-10)
            
        Returns:
            Dict with questions or error
        """
        try:
            print(f"🎯 Generating quiz: topic='{topic}', difficulty='{difficulty}', num={num_questions}")
            
            pipeline = self._get_pipeline()
            
            # Generate multiple questions
            results = pipeline.generate_multiple(
                user_query=topic,
                num_questions=num_questions,
                difficulty=difficulty,
                top_k=num_questions * 2
            )
            
            print(f"📊 Got {len(results) if results else 0} results")
            
            # Handle empty results
            if not results:
                return {
                    "error": True,
                    "message": "No relevant content found for this topic.",
                    "suggestions": POPULAR_TOPICS[:5]
                }
            
            # Check for OOD error
            first_result = results[0]
            if first_result.mcq.get("error"):
                return {
                    "error": True,
                    "message": first_result.mcq.get("message", "Topic not found."),
                    "suggestions": first_result.mcq.get("suggestions", POPULAR_TOPICS[:5])
                }
            
            # Format questions
            questions = []
            for result in results:
                mcq = result.mcq
                questions.append({
                    "question": mcq.get("question", ""),
                    "options": mcq.get("options", {}),
                    "correct": mcq.get("correct", ""),
                    "explanation": mcq.get("explanation", ""),
                    "cached": result.cached
                })
            
            print(f"✅ Generated {len(questions)} questions successfully")
            
            return {
                "error": False,
                "questions": questions
            }
            
        except Exception as e:
            print(f"❌ Quiz generation error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": True,
                "message": f"An error occurred: {str(e)}",
                "suggestions": POPULAR_TOPICS[:5]
            }
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        try:
            pipeline = self._get_pipeline()
            stats = pipeline.cache.get_stats()
            return {
                "total_entries": stats.total_entries,
                "total_hits": stats.total_hits,
                "hit_rate": stats.hit_rate
            }
        except Exception:
            return {
                "total_entries": 0,
                "total_hits": 0,
                "hit_rate": 0.0
            }
