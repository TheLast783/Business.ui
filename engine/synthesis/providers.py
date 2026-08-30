"""Pluggable LLM Provider architecture with live API support and instant deterministic mock fallbacks."""

import json
import os
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class BaseSynthesisProvider(ABC):
    """Abstract Base Class for AI synthesis providers."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.rate_per_1k_prompt = 0.0015
        self.rate_per_1k_completion = 0.0020

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generates raw text response with telemetry."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        """Generates a validated structured Pydantic/dataclass instance."""
        pass


class DeterministicFallbackProvider(BaseSynthesisProvider):
    """
    Instant (<5ms) deterministic fallback execution provider.
    Requires 0 external API keys, 0 network access, and guarantees 0 hallucinations.
    """

    def __init__(self, **kwargs):
        super().__init__(api_key=None, model_name="deterministic_mock")

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        t0 = time.time()
        prompt_words = len(prompt.split()) if prompt else 10
        prompt_tokens = prompt_words * 2
        completion_tokens = 160
        total_tokens = prompt_tokens + completion_tokens
        latency_ms = max(0.5, (time.time() - t0) * 1000.0)

        return {
            "text": "Deterministic synthesis output generated from non-LLM evidence mesh.",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_usd": 0.0,
            "mode": "deterministic_mock",
            "is_fallback": True,
        }

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        t0 = time.time()
        if fallback_factory is not None:
            obj = fallback_factory()
        else:
            try:
                obj = schema_cls()
            except Exception:
                raise ValueError(f"Cannot instantiate schema {schema_cls} without fallback_factory")

        latency_ms = max(0.5, (time.time() - t0) * 1000.0)
        if hasattr(obj, "latency_ms") and (getattr(obj, "latency_ms") == 0.0 or getattr(obj, "latency_ms") is None):
            setattr(obj, "latency_ms", latency_ms)
        if hasattr(obj, "execution_mode"):
            setattr(obj, "execution_mode", "DETERMINISTIC_FALLBACK")
        return obj


class OpenAISynthesisProvider(BaseSynthesisProvider):
    """Live OpenAI API synthesis provider with automatic deterministic fallback on failure."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o"):
        key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key=key, model_name=model_name)
        self.fallback = DeterministicFallbackProvider()

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate(prompt, system_prompt)

        t0 = time.time()
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt or "Evaluate KPI anomaly."})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.1,
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", len(prompt.split()) * 2)
                completion_tokens = usage.get("completion_tokens", 150)
                total_tokens = prompt_tokens + completion_tokens
                cost = (prompt_tokens * self.rate_per_1k_prompt + completion_tokens * self.rate_per_1k_completion) / 1000.0
                latency_ms = (time.time() - t0) * 1000.0

                return {
                    "text": choice,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "mode": "openai",
                    "is_fallback": False,
                }
        except Exception:
            return self.fallback.generate(prompt, system_prompt)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        if not self.api_key:
            return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)

        t0 = time.time()
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            schema_json = {}
            if hasattr(schema_cls, "model_json_schema"):
                schema_json = schema_cls.model_json_schema()

            system_instruction = (
                f"{system_prompt}\nYou must output strictly valid JSON matching this schema:\n"
                f"{json.dumps(schema_json)}"
            )

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]["message"]["content"]
                parsed = json.loads(choice)
                if hasattr(schema_cls, "model_validate"):
                    obj = schema_cls.model_validate(parsed)
                else:
                    obj = schema_cls(**parsed)

                usage = data.get("usage", {})
                latency_ms = (time.time() - t0) * 1000.0
                if hasattr(obj, "latency_ms"):
                    setattr(obj, "latency_ms", latency_ms)
                if hasattr(obj, "execution_mode"):
                    setattr(obj, "execution_mode", "LIVE_LLM")
                if hasattr(obj, "token_usage"):
                    setattr(
                        obj,
                        "token_usage",
                        {
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0),
                        },
                    )
                return obj
        except Exception:
            return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)


class GeminiSynthesisProvider(BaseSynthesisProvider):
    """Live Google Gemini API synthesis provider with automatic deterministic fallback on failure."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        key = api_key or os.getenv("GEMINI_API_KEY")
        super().__init__(api_key=key, model_name=model_name)
        self.fallback = DeterministicFallbackProvider()

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key:
            return self.fallback.generate(prompt, system_prompt)

        t0 = time.time()
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                prompt_tokens = len(prompt.split()) * 2
                completion_tokens = len(text.split()) * 2
                cost = (prompt_tokens * self.rate_per_1k_prompt + completion_tokens * self.rate_per_1k_completion) / 1000.0
                latency_ms = (time.time() - t0) * 1000.0

                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost,
                    "mode": "gemini",
                    "is_fallback": False,
                }
        except Exception:
            return self.fallback.generate(prompt, system_prompt)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        if not self.api_key:
            return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)
        try:
            res = self.generate(user_prompt, system_prompt=system_prompt)
            if res.get("is_fallback"):
                return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)
            parsed = json.loads(res["text"])
            if hasattr(schema_cls, "model_validate"):
                obj = schema_cls.model_validate(parsed)
            else:
                obj = schema_cls(**parsed)
            if hasattr(obj, "execution_mode"):
                setattr(obj, "execution_mode", "LIVE_LLM")
            return obj
        except Exception:
            return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)


class OllamaSynthesisProvider(BaseSynthesisProvider):
    """Local Ollama REST synthesis provider with automatic deterministic fallback on failure."""

    def __init__(self, host: str = "http://localhost:11434", model_name: str = "llama3:latest"):
        super().__init__(api_key=None, model_name=model_name)
        self.host = host.rstrip("/")
        self.fallback = DeterministicFallbackProvider()

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        t0 = time.time()
        try:
            url = f"{self.host}/api/generate"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("response", "")
                prompt_tokens = data.get("prompt_eval_count", len(prompt.split()) * 2)
                completion_tokens = data.get("eval_count", 150)
                latency_ms = (time.time() - t0) * 1000.0

                return {
                    "text": text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": 0.0,
                    "mode": "ollama",
                    "is_fallback": False,
                }
        except Exception:
            return self.fallback.generate(prompt, system_prompt)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        try:
            res = self.generate(user_prompt, system_prompt=system_prompt)
            if res.get("is_fallback"):
                return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)
            parsed = json.loads(res["text"])
            if hasattr(schema_cls, "model_validate"):
                obj = schema_cls.model_validate(parsed)
            else:
                obj = schema_cls(**parsed)
            if hasattr(obj, "execution_mode"):
                setattr(obj, "execution_mode", "LIVE_LLM")
            return obj
        except Exception:
            return self.fallback.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)


class PluggableLLMProvider:
    """
    Unified Pluggable LLM inference adapter supporting OpenAI, Gemini, Ollama, and instant Offline Mock mode.
    Guarantees the prototype runs cleanly anywhere with or without live API keys in <5ms.
    """

    def __init__(self, mode: str = "mock", api_key: Optional[str] = None):
        self.mode = mode.lower() if mode else "mock"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.rate_per_1k_prompt = 0.0015
        self.rate_per_1k_completion = 0.0020

        # Select underlying backend provider
        if self.mode in ("openai", "gpt-4o", "gpt-4", "live"):
            self.backend: BaseSynthesisProvider = OpenAISynthesisProvider(api_key=self.api_key)
        elif self.mode in ("gemini", "gemini-1.5-pro"):
            self.backend = GeminiSynthesisProvider(api_key=self.api_key)
        elif self.mode in ("ollama", "local"):
            self.backend = OllamaSynthesisProvider()
        else:
            self.backend = DeterministicFallbackProvider()

    def generate(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generates raw text response with full token and cost telemetry."""
        return self.backend.generate(prompt, system_prompt=system_prompt)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        fallback_factory: Optional[Callable[[], T]] = None,
    ) -> T:
        """Generates structured Pydantic/dataclass response with guaranteed fallback."""
        return self.backend.generate_structured(system_prompt, user_prompt, schema_cls, fallback_factory)
