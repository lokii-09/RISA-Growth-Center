from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


class AIProviderError(RuntimeError):
    """Safe, user-displayable provider failure."""


class ChatProvider(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        ...


def _read_streamlit_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except StreamlitSecretNotFoundError:
        return default
    return default if value is None else str(value).strip()


def _configured_value(name: str, default: str = "") -> str:
    environment_value = os.getenv(name)
    if environment_value and environment_value.strip():
        return environment_value.strip()
    return _read_streamlit_secret(name, default)


def _configured_api_key() -> str:
    environment_value = os.getenv("GROQ_API_KEY") or os.getenv("RISA_AI_API_KEY")
    if environment_value and environment_value.strip():
        return environment_value.strip()
    return _read_streamlit_secret("GROQ_API_KEY") or _read_streamlit_secret("RISA_AI_API_KEY")


@dataclass(frozen=True)
class ProviderSettings:
    api_key: str
    model: str
    endpoint: str
    timeout_seconds: float = 25.0

    @classmethod
    def from_environment(cls) -> "ProviderSettings | None":
        api_key = _configured_api_key()
        if not api_key:
            return None
        endpoint = _configured_value(
            "RISA_AI_BASE_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        model = _configured_value("RISA_AI_MODEL", "openai/gpt-oss-120b")
        parsed_endpoint = urlsplit(endpoint)
        if parsed_endpoint.scheme not in {"https", "http"} or not parsed_endpoint.hostname:
            raise AIProviderError("RISA_AI_BASE_URL must be a valid HTTPS URL.")
        if parsed_endpoint.username or parsed_endpoint.password:
            raise AIProviderError("RISA_AI_BASE_URL must not contain credentials.")
        if parsed_endpoint.query or parsed_endpoint.fragment:
            raise AIProviderError("RISA_AI_BASE_URL must not contain query parameters or fragments.")
        if parsed_endpoint.scheme == "http" and parsed_endpoint.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise AIProviderError("RISA_AI_BASE_URL must use HTTPS except for a local development server.")
        if not model:
            raise AIProviderError("RISA_AI_MODEL cannot be empty.")
        if not endpoint.rstrip("/").endswith("/chat/completions"):
            endpoint = endpoint.rstrip("/") + "/chat/completions"
        try:
            timeout = float(_configured_value("RISA_AI_TIMEOUT_SECONDS", "25"))
        except ValueError:
            raise AIProviderError("RISA_AI_TIMEOUT_SECONDS must be a number.") from None
        if not 1 <= timeout <= 120:
            raise AIProviderError("RISA_AI_TIMEOUT_SECONDS must be between 1 and 120.")
        return cls(api_key=api_key, model=model, endpoint=endpoint, timeout_seconds=timeout)


class OpenAICompatibleProvider:
    """Minimal tool-calling client for OpenAI-compatible chat-completions APIs."""

    def __init__(self, settings: ProviderSettings):
        self.settings = settings

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
        }
        request = Request(
            self.settings.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                body = response.read()
        except HTTPError as exc:
            raise AIProviderError(f"AI provider returned HTTP {exc.code}. Check provider settings and availability.") from None
        except (URLError, TimeoutError, OSError):
            raise AIProviderError("AI provider could not be reached. Check the connection and try again.") from None

        try:
            result = json.loads(body.decode("utf-8"))
            if not isinstance(result, dict) or not isinstance(result.get("choices"), list) or not result["choices"]:
                raise ValueError("Missing choices.")
            message = result["choices"][0].get("message")
            if not isinstance(message, dict):
                raise ValueError("Missing assistant message.")
            return result
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, IndexError, TypeError, ValueError):
            raise AIProviderError("AI provider returned a malformed response. Try again or use local analyst mode.") from None
