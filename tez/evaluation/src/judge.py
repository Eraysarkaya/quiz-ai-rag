"""
LLM Judge for Quiz AI Evaluation.

Uses GPT-OSS 120B as an INDEPENDENT judge (never same as generator).

Based on FaithJudge research (2025): https://arxiv.org/html/2505.04847v2
"""

import json
import os
import re
import time
from typing import Dict, Optional
from pathlib import Path


class LLMJudge:
    """
    Independent LLM Judge using GPT-OSS 120B.

    CRITICAL: The judge model must NEVER be the same as any generator model.
    This eliminates self-consistency bias.
    """

    DEFAULT_MODEL = "openai/gpt-oss-120b"
    TEMPERATURE = 0.0
    PRIMARY_MAX_COMPLETION_TOKENS = 512
    SECONDARY_MAX_COMPLETION_TOKENS = 512
    SEED = 42

    def __init__(self, model: str = None, api_key: str = None):
        """
        Initialize LLM Judge.

        Args:
            model: Judge model (default: GPT-OSS 120B)
            api_key: Groq API key
        """
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("groq package required: pip install groq")

        self.model = model or self.DEFAULT_MODEL
        self.api_key = api_key or self._get_api_key()

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = Groq(api_key=self.api_key)
        print(f"LLM Judge initialized: {self.model}")

    def _get_api_key(self) -> Optional[str]:
        """Get Groq API key from environment or .env file."""
        # Try environment
        api_key = os.environ.get('GROQ_API_KEY')
        if api_key:
            return api_key

        # Try .env files
        env_paths = [
            Path(__file__).resolve().parent.parent.parent.parent / ".env",
            Path(__file__).parent.parent.parent.parent / "backend" / ".env",
            Path.cwd() / "backend" / ".env",
            Path.cwd() / ".env",
        ]

        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith('GROQ_API_KEY='):
                            return line.split('=', 1)[1].strip().strip('"')

        return None

    def evaluate(self, prompt: str, max_retries: Optional[int] = None) -> Dict:
        """
        Evaluate using LLM judge.

        Args:
            prompt: The evaluation prompt
            max_retries: Maximum retry attempts. None means retry until success.

        Returns:
            Dict with at least 'score' key
        """
        attempt = 0
        strategies = (
            ("percent_integer", self._request_percent_score),
            ("numeric", self._request_numeric_score),
        )

        while True:
            attempt += 1
            try:
                strategy_name, strategy = strategies[(attempt - 1) % len(strategies)]
                response_payload = strategy(prompt)
                content = response_payload.get("content", "")
                parsed = self._parse_response(content)
                score = parsed.get("score")

                if isinstance(score, (int, float)):
                    numeric_score = float(score)
                    if strategy_name == "percent_integer" and numeric_score > 1.0:
                        numeric_score = numeric_score / 100.0
                    parsed["score"] = max(0.0, min(1.0, numeric_score))
                    parsed["strategy"] = strategy_name
                    return parsed

                debug = self._format_debug(response_payload)
                raise ValueError(
                    "Judge response missing numeric score"
                    f" [strategy={strategy_name}; {debug}]"
                )

            except Exception as e:
                print(f"  Judge error (attempt {attempt}): {e}")

                if max_retries is not None and attempt >= max_retries:
                    return {"score": None, "error": "Failed after retries"}

                # Back off slightly to avoid hammering the provider on repeated failures.
                time.sleep(min(10, 2 + attempt))

    def _request_percent_score(self, prompt: str) -> Dict[str, str]:
        """Primary judge request: integer score from 0 to 100."""
        user_prompt = (
            "Evaluate the quiz item below.\n"
            "Return only one integer from 0 to 100 inclusive.\n"
            "Do not explain. Do not add words. Do not add JSON.\n"
            "Examples: 0 , 57 , 84 , 100\n\n"
            f"{prompt}"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.TEMPERATURE,
            max_completion_tokens=self.PRIMARY_MAX_COMPLETION_TOKENS,
            include_reasoning=False,
            reasoning_effort="low",
            seed=self.SEED,
            timeout=60.0,
        )
        return self._extract_response_payload(response)

    def _request_numeric_score(self, prompt: str) -> Dict[str, str]:
        """Fallback judge request: decimal score from 0.0 to 1.0."""
        user_prompt = (
            "Evaluate the quiz item below.\n"
            "Return only one numeric score between 0.0 and 1.0 inclusive.\n"
            "Valid examples: 0.00 , 0.57 , 1.0\n"
            "Do not explain. Do not add words. Do not add JSON.\n\n"
            f"{prompt}"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.TEMPERATURE,
            max_completion_tokens=self.SECONDARY_MAX_COMPLETION_TOKENS,
            include_reasoning=False,
            reasoning_effort="low",
            seed=self.SEED,
            timeout=60.0,
        )
        return self._extract_response_payload(response)

    def _extract_response_payload(self, response) -> Dict[str, str]:
        """Extract content and debug metadata from a Groq completion response."""
        choice = response.choices[0]
        message = choice.message
        content = (message.content or "").strip()
        reasoning = getattr(message, "reasoning", None)
        refusal = getattr(message, "refusal", None)
        return {
            "content": content,
            "reasoning": (reasoning or "")[:200],
            "refusal": (refusal or "")[:200],
            "finish_reason": str(getattr(choice, "finish_reason", "")),
        }

    def _format_debug(self, payload: Dict[str, str]) -> str:
        """Format compact debug metadata for retry logs."""
        content_preview = (payload.get("content") or "")[:60]
        reasoning_preview = (payload.get("reasoning") or "")[:60]
        refusal_preview = (payload.get("refusal") or "")[:60]
        finish_reason = payload.get("finish_reason") or "unknown"
        return (
            f"finish_reason={finish_reason}, "
            f"content='{content_preview}', "
            f"reasoning='{reasoning_preview}', "
            f"refusal='{refusal_preview}'"
        )

    def _parse_response(self, response: str) -> Dict:
        """Parse a score from text or JSON response."""
        # Try direct parse first
        try:
            parsed = json.loads(response)
            if isinstance(parsed, (int, float)):
                return {"score": float(parsed)}
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Try to extract JSON object (handles nested braces)
        try:
            # Find the first { and last }
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass

        # Try to extract score number directly
        try:
            score_match = re.search(r'"?score"?\s*[:\s]+\s*([0-9]+(?:\.[0-9]*)?)', response)
            if score_match:
                value = score_match.group(1)
                if value.endswith("."):
                    value += "0"
                return {"score": float(value)}
            bare_number_match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]*)?)\s*", response)
            if bare_number_match:
                value = bare_number_match.group(1)
                if value.endswith("."):
                    value += "0"
                return {"score": float(value)}
        except (ValueError, AttributeError):
            pass

        # Log the raw response for debugging
        print(f"  [DEBUG] Failed to parse response: {response[:100]}...")
        return {"score": None, "raw_response": response[:200]}


def get_judge(model: str = None) -> LLMJudge:
    """Convenience function to get LLM judge."""
    return LLMJudge(model=model)
