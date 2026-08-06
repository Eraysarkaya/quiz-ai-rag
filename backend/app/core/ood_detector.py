# backend/app/core/ood_detector.py
"""
Out-of-Distribution (OOD) Detection for Quiz AI.

Detects when user queries fall outside the knowledge base scope.
Uses retrieval confidence scores to identify OOD queries and provide
graceful fallback responses.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for retrieval results."""
    HIGH = "high"      # > 0.60 - proceed normally
    MEDIUM = "medium"  # 0.45-0.60 - proceed with warning
    LOW = "low"        # < 0.45 - OOD, use fallback


@dataclass
class OODResult:
    """Result from OOD detection analysis."""
    is_ood: bool
    confidence_level: ConfidenceLevel
    best_score: float
    message: str
    suggested_topics: Optional[List[str]] = None


class OODDetector:
    """
    Out-of-Distribution Detection for Quiz AI.
    
    Analyzes retrieval results to determine if a query is within
    the knowledge base scope. Provides fallback messages and
    alternative topic suggestions for OOD queries.
    """
    
    # Popular topics from the SciQ knowledge base
    POPULAR_TOPICS = [
        "Photosynthesis",
        "Cell biology", 
        "DNA and genetics",
        "Chemical reactions",
        "Newton's laws of motion",
        "Human body systems",
        "Ecosystems and food chains",
        "Electricity and circuits",
        "Atoms and molecules",
        "Earth's atmosphere"
    ]
    
    def __init__(
        self,
        high_threshold: float = 0.60,
        low_threshold: float = 0.45
    ):
        """
        Initialize OOD detector.
        
        Args:
            high_threshold: Score above which confidence is HIGH
            low_threshold: Score below which query is considered OOD
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
    
    def analyze(
        self,
        retrieval_result: dict,
        top_k: int = 5
    ) -> OODResult:
        """
        Analyze retrieval result for OOD detection.
        
        Args:
            retrieval_result: Output from RAGRetriever.retrieve_with_context()
            top_k: Number of top chunks to consider for analysis
            
        Returns:
            OODResult with detection outcome and suggested actions
        """
        chunks = retrieval_result.get("chunks", [])
        
        # No chunks found at all
        if not chunks:
            return OODResult(
                is_ood=True,
                confidence_level=ConfidenceLevel.LOW,
                best_score=0.0,
                message="No relevant information found in our science database. "
                        "Please try one of the popular topics below.",
                suggested_topics=self.POPULAR_TOPICS[:5]
            )
        
        # Get best score from top chunk
        best_score = chunks[0].get("score", 0.0)
        
        # Calculate average score of top-k chunks
        top_scores = [c.get("score", 0.0) for c in chunks[:top_k]]
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        # HIGH confidence - proceed normally
        if best_score >= self.high_threshold:
            return OODResult(
                is_ood=False,
                confidence_level=ConfidenceLevel.HIGH,
                best_score=best_score,
                message=f"High confidence match found (score: {best_score:.2f})."
            )
        
        # MEDIUM confidence - proceed with warning
        if best_score >= self.low_threshold:
            return OODResult(
                is_ood=False,
                confidence_level=ConfidenceLevel.MEDIUM,
                best_score=best_score,
                message=f"Partial match found (score: {best_score:.2f}). "
                        "Results may be limited."
            )
        
        # LOW confidence - OOD detected
        # Always use popular topics for better suggestions
        return OODResult(
            is_ood=True,
            confidence_level=ConfidenceLevel.LOW,
            best_score=best_score,
            message="This topic appears to be outside the scope of our science database. "
                    "Please try a science-related topic.",
            suggested_topics=self.POPULAR_TOPICS[:5]
        )
    
    def _extract_related_topics(self, chunks: list) -> List[str]:
        """
        Extract potentially related topics from low-scoring chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            List of extracted topic hints
        """
        topics = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            
            # Extract first sentence as topic hint
            if text:
                first_sentence = text.split(".")[0].strip()
                if len(first_sentence) > 10 and len(first_sentence) < 100:
                    # Truncate if too long
                    if len(first_sentence) > 60:
                        first_sentence = first_sentence[:60] + "..."
                    topics.append(first_sentence)
        
        return topics[:3]  # Return max 3 suggestions
    
    def format_fallback_message(self, ood_result: OODResult) -> str:
        """
        Format a user-friendly fallback message.

        Args:
            ood_result: Result from analyze()

        Returns:
            Formatted message string
        """
        if not ood_result.is_ood:
            return ""

        message = f"""
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Topic Out of Scope                                        ║
╠══════════════════════════════════════════════════════════════╣
║  {ood_result.message[:60]}
║
║  📚 Suggested Topics:
"""

        if ood_result.suggested_topics:
            for i, topic in enumerate(ood_result.suggested_topics[:5], 1):
                message += f"║    {i}. {topic}\n"

        message += """╚══════════════════════════════════════════════════════════════╝"""

        return message
