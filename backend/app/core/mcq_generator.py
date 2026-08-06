# backend/app/core/mcq_generator.py
"""
MCQ Generator with configurable difficulty levels and automatic explanations.
Uses Groq Llama model with Chain-of-Thought prompting.
"""

import logging
import json
import time
import random
from typing import Dict, Optional, List
from enum import Enum

from groq import Groq
from .config import (
    GROQ_API_KEY,
    LLM_MODEL,
    MCQ_TEMPERATURE,
    MCQ_MAX_TOKENS,
    MCQ_MAX_RETRIES
)
from .utils import extract_json_from_llm

logger = logging.getLogger(__name__)


class Difficulty(str, Enum):
    """MCQ difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Difficulty-specific instructions
DIFFICULTY_INSTRUCTIONS = {
    "easy": "Create a straightforward question testing basic factual recall. The answer should be directly stated in the text.",
    "medium": "Create a question requiring understanding and interpretation of the concept. May require connecting two pieces of information.",
    "hard": "Create a challenging question requiring analysis or synthesis of multiple concepts from the text."
}


class MCQGenerator:
    """
    Generates high-quality multiple-choice questions using Groq Llama model.
    
    Features:
    - Chain-of-Thought prompting for better reasoning
    - Configurable difficulty levels (easy/medium/hard)
    - Automatic explanation generation
    - Programmatic option randomization
    - Dynamic model selection for experiments
    """

    def __init__(self, model_name: str = None):
        """Initialize the MCQ generator with Groq client.
        
        Args:
            model_name: Optional Groq model ID. Defaults to LLM_MODEL from config.
        """
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model_name = model_name or LLM_MODEL

    def _build_prompt(
        self,
        context_text: str,
        difficulty: str = "medium"
    ) -> str:
        """
        Build enhanced prompt with difficulty instructions.
        
        Args:
            context_text: The retrieved context to generate question from
            difficulty: easy/medium/hard
            
        Returns:
            Formatted prompt string
        """
        diff_instruction = DIFFICULTY_INSTRUCTIONS.get(
            difficulty, DIFFICULTY_INSTRUCTIONS["medium"]
        )
        
        return f"""You are an expert academic exam question generator.
Your task is to create ONE high-quality multiple-choice question (MCQ) based STRICTLY on the provided context.

CONTEXT:
{context_text}

DIFFICULTY LEVEL: {difficulty.upper()}
{diff_instruction}

COGNITIVE LEVEL: UNDERSTAND (Comprehension-based questions)
Focus on: Explain, Describe, Summarize, Interpret, Compare concepts from the text.

STEP-BY-STEP INSTRUCTIONS:
1. **Analyze the Context**: Read carefully. Identify the key facts, concepts, or relationships.
2. **Formulate the Question**: Create a clear, unambiguous question stem appropriate for the {difficulty} difficulty level.
3. **Determine the Correct Answer**: Extract or derive the answer from the text. It must be verifiable from the context.
4. **Create Distractors**: Design 3 plausible but incorrect options that:
   - Are grammatically parallel to the correct answer
   - Represent common misconceptions or partial truths
   - Are related to the topic but factually wrong based on the context
   - Do NOT use "None of the above" or "All of the above"
5. **Write Explanation**: Explain why the correct answer is right and briefly why key distractors are wrong.
6. **Review**: Verify the question is answerable from the context alone.

OUTPUT FORMAT (valid JSON only):
{{
  "reasoning": "Your thought process for creating this question",
  "question": "The question stem",
  "correct_answer": "The correct option text",
  "distractors": [
      "Distractor 1 text",
      "Distractor 2 text",
      "Distractor 3 text"
  ],
  "explanation": "Why the correct answer is right and why the main distractor is wrong",
  "difficulty": "{difficulty}"
}}

STRICT RULES:
- Output ONLY valid JSON. No other text.
- Provide exactly 3 distractors.
- The question must be answerable using ONLY the provided context.
- All options should be similar in length and style.
"""

    def _validate_raw_response(self, data: Dict) -> bool:
        """
        Validate the structure of the raw LLM response before shuffling.
        
        Args:
            data: Parsed JSON response from LLM
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ["question", "correct_answer", "distractors"]
        
        for key in required_keys:
            if key not in data:
                logger.warning(f"Validation Failed: Missing key '{key}'")
                return False
        
        if not isinstance(data["distractors"], list) or len(data["distractors"]) != 3:
            logger.warning("Validation Failed: 'distractors' must be a list of 3 items")
            return False
        
        # Check for empty values
        if not data["question"].strip():
            logger.warning("Validation Failed: Empty question")
            return False
            
        if not data["correct_answer"].strip():
            logger.warning("Validation Failed: Empty correct answer")
            return False
        
        for i, d in enumerate(data["distractors"]):
            if not d.strip():
                logger.warning(f"Validation Failed: Empty distractor at index {i}")
                return False
        
        return True

    def _shuffle_and_label(self, raw_data: Dict) -> Dict:
        """
        Shuffle options and assign A/B/C/D labels.
        
        Args:
            raw_data: Validated raw response with correct_answer and distractors
            
        Returns:
            Final MCQ format with options dict and correct label
        """
        correct_text = raw_data["correct_answer"].strip()
        distractors = [d.strip() for d in raw_data["distractors"]]
        
        # Combine and shuffle
        all_options = [correct_text] + distractors
        random.shuffle(all_options)
        
        # Assign labels
        labels = ["A", "B", "C", "D"]
        options_dict = {}
        correct_label = ""
        
        for label, text in zip(labels, all_options):
            options_dict[label] = text
            if text == correct_text:
                correct_label = label
        
        return {
            "question": raw_data["question"].strip(),
            "options": options_dict,
            "correct": correct_label,
            "explanation": raw_data.get("explanation", "").strip(),
            "difficulty": raw_data.get("difficulty", "medium"),
            "reasoning": raw_data.get("reasoning", "")
        }

    def generate_mcq(
        self,
        context_text: str,
        difficulty: str = "medium",
        max_retries: int = None
    ) -> Optional[Dict]:
        """
        Generate a single MCQ from context text.
        
        All questions target comprehension level (understand).
        
        Args:
            context_text: Source text to generate question from
            difficulty: easy/medium/hard
            max_retries: Override default retry count
            
        Returns:
            MCQ dict with question, options, correct, explanation, etc.
            Returns None if generation fails.
        """
        if max_retries is None:
            max_retries = MCQ_MAX_RETRIES
            
        # Validate difficulty
        try:
            difficulty = Difficulty(difficulty.lower()).value
        except ValueError:
            difficulty = "medium"
        
        prompt = self._build_prompt(context_text, difficulty)

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that outputs only valid JSON. No markdown, no explanations, just JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=MCQ_TEMPERATURE,
                    max_tokens=MCQ_MAX_TOKENS,
                    timeout=60.0  # 60 second timeout to prevent hanging
                )

                raw_output = response.choices[0].message.content
                raw_data = extract_json_from_llm(raw_output)
                
                if raw_data is None:
                    logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON")
                    continue

                if self._validate_raw_response(raw_data):
                    # Success! Shuffle and return
                    return self._shuffle_and_label(raw_data)
                
                logger.warning(f"Attempt {attempt + 1} failed validation. Retrying...")

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error - {e}")
            
            time.sleep(1)  # Brief pause before retry

        logger.error("Failed to generate valid MCQ after all retries")
        return None

    def generate_multiple_mcqs(
        self,
        context_text: str,
        count: int = 3,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate multiple MCQs from the same context.
        
        Args:
            context_text: Source text
            count: Number of questions to generate
            difficulty: Difficulty level
            
        Returns:
            List of MCQ dicts
        """
        mcqs = []
        for i in range(count):
            logger.debug(f"Generating MCQ {i+1}/{count}")
            mcq = self.generate_mcq(context_text, difficulty)
            if mcq:
                mcqs.append(mcq)
        return mcqs
