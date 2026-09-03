"""
RevFlow LLM Adapter — Provider-agnostic interface with validation wrapper.

Per §8.1: Single interface, one implementation per provider (groq, gemini, anthropic).
Shared validation wrapper holds allow-list checking so provider code cannot bypass it.

All methods return None on failure (not exception) — deterministic fallback takes over.
"""
import os
import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from dataclasses import dataclass

from revflow.contracts.enums import EventType, Cause, Action, LadderStep
from revflow.ingestion.normaliser import Event

logger = logging.getLogger(__name__)

# ─── Offline Mode Guard ────────────────────────────────────────────────────────

# Global flag to disable all LLM calls (for offline mode / use_llm=False)
_OFFLINE_MODE = False


def set_offline_mode(enabled: bool) -> None:
    """Enable or disable offline mode. When enabled, all LLM calls return None immediately."""
    global _OFFLINE_MODE
    _OFFLINE_MODE = enabled


def is_offline_mode() -> bool:
    """Check if offline mode is enabled."""
    return _OFFLINE_MODE


# ─── Validation Wrapper ────────────────────────────────────────────────────────

def validate_llm_cause(cause_str: str, allowed_causes: List[str]) -> bool:
    """Validate LLM cause output is in allowed closed list."""
    return cause_str in allowed_causes


def validate_llm_action(action_str: str, allowed_actions: List[str]) -> bool:
    """Validate LLM action output is in allowed closed list."""
    return action_str in allowed_actions


def validate_llm_rationale(rationale: str) -> bool:
    """Validate LLM rationale exists and length >= 10 (FR-7)."""
    return rationale is not None and len(rationale) >= 10


# ─── Abstract Interface ──────────────────────────────────────────────────────

class LLMAdapter(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def classify_cause(
        self, event: Event, allowed_causes: List[str]
    ) -> Optional[Tuple[str, float]]:
        """
        Classify event cause.

        Returns:
            (cause_str, confidence) or None on failure.
        """
        if is_offline_mode():
            logger.debug("Offline mode: skipping LLM classify_cause")
            return None
        pass

    @abstractmethod
    async def select_action(
        self, event: Event, cause: str, allowed_actions: List[str]
    ) -> Optional[Tuple[str, str]]:
        """
        Select action for event given cause.

        Returns:
            (action_str, rationale) or None on failure.
        """
        pass

    @abstractmethod
    async def generate_outreach(
        self, event: Event, cause: str, locale: str, tone: str
    ) -> Optional[str]:
        """Generate outreach copy (SMS/WhatsApp/voice script). Returns body text or None."""
        pass

    @abstractmethod
    async def extract_ptp_date(self, reply_text: str) -> Optional[str]:
        """Extract promised date from customer reply. Returns ISO date string or None."""
        pass


# ─── Provider Implementations ─────────────────────────────────────────────────

class GroqAdapter(LLMAdapter):
    """Groq LLM provider adapter."""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")
        self.base_url = "https://api.groq.com/openai/v1"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=20.0,
        )

    async def _chat(self, messages: List[dict], temperature: float = 0) -> Optional[str]:
        """Make chat completion request."""
        if is_offline_mode():
            logger.debug("Offline mode: skipping LLM _chat")
            return None
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            if response.status_code != 200:
                logger.warning(f"Groq API error {response.status_code}: {response.text}")
                return None
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Groq API error: {e}")
            return None

    async def classify_cause(
        self, event: Event, allowed_causes: List[str]
    ) -> Optional[Tuple[str, float]]:
        system = (
            "You are a payment failure classifier. "
            "Given event details and a decline message, select the most likely cause "
            f"from this closed list: {allowed_causes}. "
            "Return JSON: {\"cause\": \"<cause>\", \"confidence\": <0.0-1.0>}."
        )
        user = (
            f"Event type: {event.event_type.value}\n"
            f"Amount: {event.amount_inr / 100:.2f} INR\n"
            f"Decline code: {event.decline_code}\n"
            f"Decline message: {event.decline_message}\n"
            f"Retry count: {event.retry_count}"
        )
        content = await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            cause = parsed.get("cause")
            confidence = float(parsed.get("confidence", 0.5))
            if cause not in allowed_causes:
                return None
            return (cause, confidence)
        except Exception:
            return None

    async def select_action(
        self, event: Event, cause: str, allowed_actions: List[str]
    ) -> Optional[Tuple[str, str]]:
        system = (
            "You are a revenue recovery policy engine. "
            f"Given event type {event.event_type.value}, cause {cause}, "
            f"select the best action from this closed list: {allowed_actions}. "
            "Return JSON: {\"action\": \"<action>\", \"rationale\": \"<human-readable reason, >=10 chars>\"}."
        )
        user = (
            f"Event type: {event.event_type.value}\n"
            f"Amount: {event.amount_inr / 100:.2f} INR\n"
            f"Cause: {cause}\n"
            f"Retry count: {event.retry_count}\n"
            f"Customer reply: {event.customer_reply_text}"
        )
        content = await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            action = parsed.get("action")
            rationale = parsed.get("rationale", "")
            if action not in allowed_actions:
                return None
            return (action, rationale)
        except Exception:
            return None

    async def generate_outreach(
        self, event: Event, cause: str, locale: str, tone: str
    ) -> Optional[str]:
        system = (
            f"Generate a {tone} payment reminder in {locale} for a {cause} event. "
            "Single message, concise, professional. No emojis. Return plain text only."
        )
        user = f"Amount: {event.amount_inr / 100:.2f} INR. Customer: {event.customer_id}"
        return await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])

    async def extract_ptp_date(self, reply_text: str) -> Optional[str]:
        system = (
            "Extract promised payment date from customer reply. "
            "Return JSON: {\"date\": \"YYYY-MM-DD\"} or {\"date\": null} if no clear date."
        )
        content = await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": reply_text},
        ])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            return parsed.get("date")
        except Exception:
            return None


class GeminiAdapter(LLMAdapter):
    """Google Gemini LLM provider adapter."""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.client = httpx.AsyncClient(timeout=20.0)

    async def _chat(self, messages: List[dict], temperature: float = 0) -> Optional[str]:
        if is_offline_mode():
            logger.debug("Offline mode: skipping LLM _chat")
            return None
        try:
            # Convert to Gemini format
            contents = []
            for m in messages:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m["content"]}]})

            response = await self.client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "responseMimeType": "application/json",
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return None

    async def classify_cause(
        self, event: Event, allowed_causes: List[str]
    ) -> Optional[Tuple[str, float]]:
        system = (
            "You are a payment failure classifier. "
            f"Select cause from: {allowed_causes}. "
            "Return JSON: {\"cause\": \"...\", \"confidence\": 0.0}."
        )
        user = (
            f"Event type: {event.event_type.value}\n"
            f"Decline code: {event.decline_code}\n"
            f"Decline message: {event.decline_message}\n"
            f"Retry count: {event.retry_count}"
        )
        content = await self._chat([{"role": "user", "content": system + "\n\n" + user}])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            cause = parsed.get("cause")
            confidence = float(parsed.get("confidence", 0.5))
            if cause not in allowed_causes:
                return None
            return (cause, confidence)
        except Exception:
            return None

    async def select_action(
        self, event: Event, cause: str, allowed_actions: List[str]
    ) -> Optional[Tuple[str, str]]:
        system = (
            f"Select action from {allowed_actions} for event {event.event_type.value}, cause {cause}. "
            "Return JSON: {\"action\": \"...\", \"rationale\": \"...\"}."
        )
        user = f"Retry count: {event.retry_count}. Reply: {event.customer_reply_text}"
        content = await self._chat([{"role": "user", "content": system + "\n\n" + user}])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            action = parsed.get("action")
            rationale = parsed.get("rationale", "")
            if action not in allowed_actions:
                return None
            return (action, rationale)
        except Exception:
            return None

    async def generate_outreach(
        self, event: Event, cause: str, locale: str, tone: str
    ) -> Optional[str]:
        system = f"Generate {tone} {locale} reminder for {cause}. Amount: {event.amount_inr/100:.0f} INR. Return plain text."
        content = await self._chat([{"role": "user", "content": system}])
        return content

    async def extract_ptp_date(self, reply_text: str) -> Optional[str]:
        system = "Extract promised date from reply. Return JSON: {\"date\": \"YYYY-MM-DD\" or null}."
        content = await self._chat([{"role": "user", "content": system + "\n\n" + reply_text}])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            return parsed.get("date")
        except Exception:
            return None


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude LLM provider adapter."""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", "claude-3-haiku-20240307")
        self.base_url = "https://api.anthropic.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=20.0,
        )

    async def _chat(self, messages: List[dict], temperature: float = 0) -> Optional[str]:
        if is_offline_mode():
            logger.debug("Offline mode: skipping LLM _chat")
            return None
        try:
            system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_messages = [m for m in messages if m["role"] == "user"]

            response = await self.client.post(
                f"{self.base_url}/messages",
                json={
                    "model": self.model,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": m["content"]} for m in user_messages],
                    "temperature": temperature,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            logger.warning(f"Anthropic API error: {e}")
            return None

    async def classify_cause(
        self, event: Event, allowed_causes: List[str]
    ) -> Optional[Tuple[str, float]]:
        system = (
            "You are a payment failure classifier. "
            f"Select cause from: {allowed_causes}. "
            "Return JSON only: {\"cause\": \"...\", \"confidence\": 0.0}."
        )
        user = (
            f"Event type: {event.event_type.value}\n"
            f"Decline code: {event.decline_code}\n"
            f"Decline message: {event.decline_message}\n"
            f"Retry count: {event.retry_count}"
        )
        content = await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            cause = parsed.get("cause")
            confidence = float(parsed.get("confidence", 0.5))
            if cause not in allowed_causes:
                return None
            return (cause, confidence)
        except Exception:
            return None

    async def select_action(
        self, event: Event, cause: str, allowed_actions: List[str]
    ) -> Optional[Tuple[str, str]]:
        system = (
            f"Select action from {allowed_actions} for event {event.event_type.value}, cause {cause}. "
            "Return JSON only: {\"action\": \"...\", \"rationale\": \"...\"}."
        )
        user = f"Retry count: {event.retry_count}. Reply: {event.customer_reply_text}"
        content = await self._chat([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            action = parsed.get("action")
            rationale = parsed.get("rationale", "")
            if action not in allowed_actions:
                return None
            return (action, rationale)
        except Exception:
            return None

    async def generate_outreach(
        self, event: Event, cause: str, locale: str, tone: str
    ) -> Optional[str]:
        system = f"Generate {tone} {locale} reminder for {cause}. Amount: {event.amount_inr/100:.0f} INR. Return plain text."
        content = await self._chat([{"role": "system", "content": system}])
        return content

    async def extract_ptp_date(self, reply_text: str) -> Optional[str]:
        system = "Extract promised date from reply. Return JSON: {\"date\": \"YYYY-MM-DD\" or null}."
        content = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": reply_text}])
        if content is None:
            return None
        try:
            parsed = json.loads(content)
            return parsed.get("date")
        except Exception:
            return None


# ─── Provider Factory ────────────────────────────────────────────────────────

_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter() -> LLMAdapter:
    """Get singleton LLMAdapter instance based on LLM_PROVIDER env var."""
    global _llm_adapter
    if _llm_adapter is not None:
        return _llm_adapter

    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        _llm_adapter = GroqAdapter()
    elif provider == "gemini":
        _llm_adapter = GeminiAdapter()
    elif provider == "anthropic":
        _llm_adapter = AnthropicAdapter()
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Must be groq, gemini, or anthropic.")

    return _llm_adapter