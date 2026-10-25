"""LLM Provider Client for AI Compliance Copilot.

Supports OpenAI-compatible LLM providers (e.g. OpenAI, Anthropic via proxy, Groq, local Ollama, vLLM).
Provides error handling, timeouts, and graceful fallback to rule-based tools.
"""

import logging
import httpx
from typing import Optional, List, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        """Returns True if provider and API key are configured."""
        return bool(self.settings.LLM_PROVIDER and self.settings.LLM_API_KEY)

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context_data: Optional[str] = None,
    ) -> Optional[str]:
        """Call configured LLM provider using OpenAI-compatible chat completions API.
        
        Never logs or exposes the API key.
        Returns None if call fails or LLM is not configured.
        """
        if not self.is_configured:
            return None

        base_url = self.settings.LLM_BASE_URL.rstrip("/") if self.settings.LLM_BASE_URL else "https://api.openai.com/v1"
        endpoint = f"{base_url}/chat/completions"
        model = self.settings.LLM_MODEL or "gpt-4o-mini"

        content = user_message
        if context_data:
            content = f"GROUNDED CONTEXT DATA (AUTHORIZED RECORDS ONLY):\n{context_data}\n\nUSER QUESTION:\n{user_message}"

        headers = {
            "Authorization": f"Bearer {self.settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"].get("content", "").strip()
                else:
                    logger.warning(
                        "LLM provider returned non-200 status: %s",
                        response.status_code,
                    )
        except httpx.TimeoutException:
            logger.warning("LLM provider timed out after 15 seconds")
        except Exception as e:
            logger.warning("LLM provider call error: %s", type(e).__name__)

        return None


llm_service = LLMService()
