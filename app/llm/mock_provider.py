"""
Mock LLM provider for demonstration and testing.

Returns canned responses so you can see the terminal UI and multi-agent
workflows working without needing an API key.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.llm.base import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """A mock LLM that simulates responses."""

    @property
    def model_name(self) -> str:
        return "mock-llm-1.0"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        # Simulate network latency
        await asyncio.sleep(1.5)

        # Basic heuristic to return different canned responses based on the prompt
        system_lower = system_prompt.lower()
        
        if "security" in system_lower:
            return "### [CRITICAL] Remote Code Execution Risk\n- **Risk**: Using `eval()` allows execution of arbitrary code.\n- **Location**: `test_bug.py` line 3\n- **Fix**: Remove `eval` completely and use safe parsing."
        elif "performance" in system_lower:
            return "### [HIGH] Inefficient Memory Allocation\n- **Impact**: Creating a 100M item list in memory will cause massive RAM usage and garbage collection pauses.\n- **Location**: `test_bug.py` line 6\n- **Fix**: Use a generator expression instead of a list comprehension."
        elif "readability" in system_lower:
            return "### [MEDIUM] Lack of Type Hints\n- **Issue**: The `x` parameter has no type hint making it hard to maintain.\n- **Location**: `test_bug.py`\n- **Suggestion**: Add type hints `def bad_code(x: str) -> int:`"
        elif "architecture" in system_lower:
            return "### [LOW] Mixed Responsibilities\n- **Principle violated**: Single Responsibility Principle.\n- **Location**: `test_bug.py`\n- **Refactoring**: Separate data fetching and data processing logic into distinct functions."
        elif "test" in system_lower and "qa" in system_lower:
            return "### [HIGH] Missing Security Tests\n- **What's untested**: The `eval()` path needs testing with malicious payloads to ensure proper sanitization (if `eval` isn't removed).\n- **Risk**: High risk of regression.\n- **Suggested test**: Add `test_bad_code_with_malicious_input()`."
        elif "synthesise" in system_lower or "executive summary" in system_lower:
            return """## 🎯 Executive Summary
This code snippet contains critical security and performance flaws that must be addressed immediately before deployment.

## 🚨 Top Priority Issues
1. **Remove `eval()`** - Critical RCE vulnerability.
2. **Refactor memory allocation** - Replace the 100M item list comprehension with a generator or mathematical constant.

## ✅ Strengths
- The code is concise.

## 📋 Action Items
- [ ] Replace `eval` with `ast.literal_eval`.
- [ ] Refactor list comprehension.
- [ ] Add type hints.

## 🏆 Overall Risk: [CRITICAL]
"""
        else:
            return "Mock response. The AI successfully parsed the prompt and generated this demonstration message."

    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        response = await self.complete(system_prompt, user_prompt)
        # Yield the response in small chunks to simulate streaming
        chunk_size = 10
        for i in range(0, len(response), chunk_size):
            await asyncio.sleep(0.05)
            yield response[i : i + chunk_size]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Return a dummy vector
        return [[0.0] * 384 for _ in texts]
