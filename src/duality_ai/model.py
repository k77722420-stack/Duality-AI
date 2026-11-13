"""Model clients — the real-model edge of the Duality AI.

The skeleton stages in ``hemispheres.py`` are deterministic stand-ins.
This module defines the seam where a real language model plugs in:
a tiny protocol, ``complete(system, user) -> str``, with three
implementations — ``GeminiClient`` (Google Gemini over HTTPS),
``OllamaClient`` (a local Ollama server), and ``FakeModelClient``
(a test fixture that makes no network calls).

Pure standard library (``urllib``): no new dependencies enter the
package for the sake of this edge. Clients return the model's raw
text; deciding whether that text is well-formed enough to act on is
the caller's job — see ``live.py``, where a malformed reply fails
closed and the step does not proceed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable, Protocol, Union


class ModelClient(Protocol):
    """The model seam: one system instruction, one user turn, one reply."""

    def complete(self, system: str, user: str) -> str:
        """Return the model's reply text for this system/user pair."""
        ...


def _post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    """POST `payload` as JSON to `url` and return the parsed reply."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


class GeminiClient:
    """A ModelClient backed by the Google Gemini API.

    The API key comes from the `api_key` argument or the
    GEMINI_API_KEY environment variable. No key, no request: the
    client raises before any network call is attempted.
    """

    def __init__(
        self, model: str = "gemini-2.0-flash", api_key: str | None = None
    ) -> None:
        self.model = model
        self.api_key = (
            api_key if api_key is not None else os.environ.get("GEMINI_API_KEY")
        )

    def complete(self, system: str, user: str) -> str:
        if not self.api_key:
            raise RuntimeError(
                "GeminiClient has no API key: set the GEMINI_API_KEY "
                "environment variable or pass api_key=... to the "
                "constructor."
            )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json",
            },
        }
        try:
            data = _post_json(url, payload, headers={"x-goog-api-key": self.api_key})
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Gemini request failed with HTTP {error.code}: {detail}"
            ) from error
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError(
                f"Gemini reply had no usable candidate text: {data!r}"
            ) from error


class OllamaClient:
    """A ModelClient backed by a local Ollama server's /api/chat.

    The base URL comes from the `base_url` argument, the OLLAMA_HOST
    environment variable, or the Ollama default
    http://localhost:11434.
    """

    def __init__(
        self, model: str = "llama3.2:3b", base_url: str | None = None
    ) -> None:
        self.model = model
        self.base_url = (
            base_url
            or os.environ.get("OLLAMA_HOST")
            or "http://localhost:11434"
        ).rstrip("/")

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        try:
            data = _post_json(f"{self.base_url}/api/chat", payload)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama request failed with HTTP {error.code}: {detail}"
            ) from error
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as error:
            raise RuntimeError(
                f"Ollama reply had no usable message content: {data!r}"
            ) from error


class FakeModelClient:
    """A ModelClient fixture for tests: canned replies, no network.

    `responses` is either a callable ``(system, user) -> str`` or a
    dict mapping a substring of the user text to the reply to return.
    With a dict, the first key found inside the user text wins; the
    special key "*" is the default reply when nothing else matches;
    if neither matches, KeyError is raised — a fixture should say what
    it means, not improvise. Every call is recorded in ``.calls`` as
    ``{"system": ..., "user": ...}`` dicts, in order.
    """

    def __init__(
        self, responses: Union[dict, Callable[[str, str], str]]
    ) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        if callable(self.responses):
            return self.responses(system, user)
        for key, reply in self.responses.items():
            if key != "*" and key in user:
                return reply
        if "*" in self.responses:
            return self.responses["*"]
        raise KeyError(
            f"FakeModelClient has no fixture for user text: {user!r}"
        )
