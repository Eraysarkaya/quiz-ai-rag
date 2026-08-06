# backend/app/core/pipeline.py
"""
Complete end-to-end Quiz AI pipeline.
Combines retrieval and MCQ generation with configurable parameters.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .rag_retriever import RAGRetriever
from .mcq_generator import MCQGenerator, Difficulty
from .utils import format_mcq_for_display
from .semantic_cache import SemanticCache
from .ood_detector import OODDetector, ConfidenceLevel, OODResult

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class QuizRequest:
    """Request parameters for quiz generation."""
    topic: str
    difficulty: str = "medium"
    num_questions: int = 1
    top_k: int = 5
    similarity_metric: str = "cosine"


@dataclass
class QuizResult:
    """Result from quiz generation."""
    mcq: Dict
    retrieved_chunks: List[Dict]
    best_chunk_id: int
    best_chunk_score: float
    context_used: str
    cached: bool = False
    ood_warning: str = None


class QuizPipeline:
    """
    End-to-end MCQ generation pipeline.
    
    Flow:
    1. User input (topic/query)
    2. RAG retrieval → most relevant chunks
    3. MCQ generation → structured question with explanation
    """
    
    # Singleton instance for model caching
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for model caching."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, top_k: int = 5):
        """Initialize the pipeline (only once due to singleton)."""
        if QuizPipeline._initialized:
            return
            
        logger.info("Initializing Quiz Pipeline...")
        self.retriever = RAGRetriever(top_k=top_k)
        self.generator = MCQGenerator()
        self.cache = SemanticCache()
        self.ood_detector = OODDetector()
        QuizPipeline._initialized = True
        logger.info("Pipeline ready")

    def generate(
        self,
        user_query: str,
        difficulty: str = "medium",
        top_k: int = None
    ) -> Optional[QuizResult]:
        """Generate a single MCQ from a topic/query."""
        if top_k is None:
            top_k = self.retriever.top_k

        # 1) Check semantic cache first
        cached_result = self.cache.lookup(user_query, difficulty)
        if cached_result:
            logger.info(f"Cache HIT (similarity: {cached_result['similarity']:.2f})")
            return QuizResult(
                mcq=cached_result["mcq"],
                retrieved_chunks=[],
                best_chunk_id="cached",
                best_chunk_score=cached_result["similarity"],
                context_used="[Cached]",
                cached=True
            )

        logger.info(f"Retrieving context for: '{user_query}'")

        # 2) RAG retrieval
        retrieval_result = self.retriever.retrieve_with_context(user_query, top_k=top_k)
        chunks = retrieval_result["chunks"]
        context_text = retrieval_result["context"]
        
        if not chunks:
            logger.warning("No relevant chunks found")
            return None

        best_chunk = chunks[0]
        logger.info(f"Retrieved {len(chunks)} chunks. Best score: {best_chunk['score']:.4f}")

        # 3) OOD Detection
        ood_result = self.ood_detector.analyze(retrieval_result)
        
        if ood_result.is_ood:
            logger.warning(f"OOD Detected: {ood_result.message}")
            return QuizResult(
                mcq={"error": "out_of_domain", "message": ood_result.message, "suggestions": ood_result.suggested_topics},
                retrieved_chunks=chunks,
                best_chunk_id=best_chunk["chunk_id"],
                best_chunk_score=best_chunk["score"],
                context_used="",
                cached=False,
                ood_warning=ood_result.message
            )
        
        ood_warning = None
        if ood_result.confidence_level == ConfidenceLevel.MEDIUM:
            ood_warning = ood_result.message
            logger.warning(f"Low confidence: {ood_warning}")

        # 4) MCQ generation
        logger.info(f"Generating MCQ (difficulty={difficulty})")
        mcq = self.generator.generate_mcq(context_text, difficulty=difficulty)

        if not mcq:
            logger.error("MCQ generation failed")
            return None

        # 5) Store in cache
        self.cache.store(
            query=user_query,
            mcq=mcq,
            chunk_id=str(best_chunk["chunk_id"]),
            difficulty=difficulty
        )

        return QuizResult(
            mcq=mcq,
            retrieved_chunks=chunks,
            best_chunk_id=best_chunk["chunk_id"],
            best_chunk_score=best_chunk["score"],
            context_used=context_text,
            cached=False
        )

    def generate_multiple(
        self,
        user_query: str,
        num_questions: int = 3,
        difficulty: str = "medium",
        top_k: int = 10,
        min_score: float = 0.25  # Lower threshold for multi-question generation
    ) -> List[QuizResult]:
        """Generate multiple unique MCQs from different chunks."""
        results = []
        used_chunks = set()

        # Request more chunks to ensure enough unique ones
        retrieval_top_k = max(top_k, num_questions * 3)
        logger.info(f"Retrieving context for: '{user_query}' (top_{retrieval_top_k}, min_score={min_score})")

        retrieval_result = self.retriever.retrieve_with_context(
            user_query, top_k=retrieval_top_k, min_score=min_score
        )
        chunks = retrieval_result.get("chunks", [])
        
        if not chunks:
            logger.warning("No relevant chunks found")
            return []

        # Warn if fewer chunks found than requested
        if len(chunks) < num_questions:
            logger.warning(
                f"Only {len(chunks)} relevant chunks found for {num_questions} questions. "
                f"Consider using a more specific topic."
            )

        logger.info(f"Retrieved {len(chunks)} chunks for {num_questions} questions")
        
        # OOD check
        ood_result = self.ood_detector.analyze(retrieval_result)
        if ood_result.is_ood:
            logger.warning(f"OOD Detected: {ood_result.message}")
            return [QuizResult(
                mcq={"error": "out_of_domain", "message": ood_result.message, "suggestions": ood_result.suggested_topics},
                retrieved_chunks=chunks[:1],
                best_chunk_id=chunks[0]["chunk_id"] if chunks else 0,
                best_chunk_score=chunks[0]["score"] if chunks else 0,
                context_used="",
                cached=False,
                ood_warning=ood_result.message
            )]
        
        # Generate questions from different chunks
        for i in range(num_questions):
            logger.debug(f"Generating question {i+1}/{num_questions}")
            
            chunk_to_use = None
            for chunk in chunks:
                chunk_id = chunk.get("chunk_id")
                if chunk_id not in used_chunks:
                    chunk_to_use = chunk
                    used_chunks.add(chunk_id)
                    break
            
            if not chunk_to_use:
                logger.warning(f"No more unique chunks, stopping at {len(results)} questions")
                break
            
            context_text = chunk_to_use.get("text", "")
            logger.debug(f"Using chunk {chunk_to_use['chunk_id']} (score: {chunk_to_use['score']:.4f})")
            
            mcq = self.generator.generate_mcq(context_text, difficulty=difficulty)
            
            if mcq:
                results.append(QuizResult(
                    mcq=mcq,
                    retrieved_chunks=[chunk_to_use],
                    best_chunk_id=chunk_to_use["chunk_id"],
                    best_chunk_score=chunk_to_use["score"],
                    context_used=context_text,
                    cached=False
                ))
                # NOTE: Not caching multi-question results to ensure variety
                # across different sessions for the same topic
            else:
                logger.warning(f"MCQ generation failed for chunk {chunk_to_use['chunk_id']}")
        
        logger.info(f"Generated {len(results)} unique questions")
        return results

    def generate_quiz(self, request: QuizRequest) -> List[QuizResult]:
        """Generate multiple MCQs based on a request."""
        logger.info(f"Quiz request: topic='{request.topic}', difficulty={request.difficulty}, num={request.num_questions}")
        
        if request.num_questions == 1:
            result = self.generate(
                user_query=request.topic,
                difficulty=request.difficulty,
                top_k=request.top_k
            )
            return [result] if result else []
        
        return self.generate_multiple(
            user_query=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            top_k=request.top_k
        )

    def generate_batch(self, topics: List[str], difficulty: str = "medium") -> List[QuizResult]:
        """Generate MCQs for multiple topics."""
        results = []
        for topic in topics:
            result = self.generate(user_query=topic, difficulty=difficulty)
            if result:
                results.append(result)
        return results
