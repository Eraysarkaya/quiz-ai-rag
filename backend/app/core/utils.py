# backend/app/core/utils.py
"""
Shared utilities for Quiz AI backend.
Consolidates common functions used across modules.
"""

import json
import re
from typing import Any, Optional, List


def normalize_text(text: Any) -> str:
    """
    Ensures text is always a clean string.
    Handles None, lists, and other types gracefully.
    
    Args:
        text: Input that may be str, list, None, or other type
        
    Returns:
        Clean string representation
    """
    if text is None:
        return ""
    if isinstance(text, list):
        return " ".join(str(item) for item in text if item)
    return str(text).strip()


def extract_json_from_llm(text: str) -> Optional[dict]:
    """
    Extracts JSON object from LLM output, handling markdown code blocks.
    
    Args:
        text: Raw LLM output that may contain markdown formatting
        
    Returns:
        Parsed JSON dict or None if extraction fails
    """
    if not text:
        return None
        
    text = text.strip()
    
    # Handle markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object in text using improved regex
    # Non-greedy match with nested brace support
    match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def estimate_tokens(text: str) -> int:
    """
    Approximate token count for English text.
    Uses word count * 1.3 as a reasonable approximation.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return int(len(text.split()) * 1.3)


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """
    Truncates text to maximum length with suffix.
    
    Args:
        text: Input text
        max_chars: Maximum character length
        suffix: String to append when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def validate_mcq_structure(mcq: dict) -> bool:
    """
    Validates that an MCQ dict has all required fields.
    
    Args:
        mcq: MCQ dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ["question", "options", "correct"]
    
    if not isinstance(mcq, dict):
        return False
    
    for key in required_keys:
        if key not in mcq:
            return False
    
    # Validate options structure
    options = mcq.get("options", {})
    if not isinstance(options, dict) or len(options) < 4:
        return False
    
    # Validate correct answer exists in options
    correct = mcq.get("correct", "")
    if correct not in options:
        return False
    
    return True


def format_mcq_for_display(mcq: dict) -> str:
    """
    Formats an MCQ dict as a human-readable string.
    
    Args:
        mcq: MCQ dictionary with question, options, correct, explanation
        
    Returns:
        Formatted string representation
    """
    if not mcq:
        return "No MCQ data"
    
    lines = [
        f"❓ Question: {mcq.get('question', 'N/A')}",
        "",
        "📋 Options:"
    ]
    
    options = mcq.get("options", {})
    correct = mcq.get("correct", "")
    
    for key in sorted(options.keys()):
        marker = "✅" if key == correct else "  "
        lines.append(f"  {marker} {key}) {options[key]}")
    
    if mcq.get("explanation"):
        lines.append("")
        lines.append(f"💡 Explanation: {mcq.get('explanation')}")
    
    if mcq.get("difficulty"):
        lines.append(f"📊 Difficulty: {mcq.get('difficulty')}")
    
    return "\n".join(lines)
