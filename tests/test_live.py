"""Tests for the live pipeline and the model clients.

No network anywhere: the pipeline is exercised against
FakeModelClient fixtures, and the HTTP clients are exercised against
a monkeypatched urllib.request.urlopen that captures the request and
returns a canned response.
"""

import json
import urllib.request

import pytest

from duality_ai.live import LivePipeline
from duality_ai.model import FakeModelClient, GeminiClient, OllamaClient
from duality_ai.pipeline import STAGE_ORDER

BENIGN_LOGICAL = json.dumps(
    {
        "checks": [
            {
                "name": "request_is_substantive",
                "passed": True,
                "detail": "request states a clear goal",
            }
        ],
        "flags": [],
        "signals": [],
        "pros": ["The request states a goal the system can address."],
        "cons": ["No analytic objections identified."],
    }
)

DECEPTION_LOGICAL = json.dumps(
    {
        "checks": [
            {
                "name": "no_deception_signal",
                "passed": False,
                "detail": "deception marker present",
            }
        ],
        "flags": ["signal:deception"],
        "signals": ["deception"],
        "stance": "explains",
        "pros": ["The request states a goal the system can address."],
        "cons": [
            "The request asks for content that would mislead a third "
            "party if produced as asked."
        ],
    }
)

CREATIVE = json.dumps(
    {
        "alternatives": [
            {"id": "alt-direct", "text": "Answer plainly, as asked."},
            {"id": "alt-explainer", "text": "Answer with background."},
            {"id": "alt-cautionary", "text": "Answer with caution."},
        ]
    }
)


def make_model(logical_reply, creative_reply=CREATIVE):
    """A FakeModelClient whose replies dispatch on the system prompt."""

    def respond(system, user):
        if "CREATIVE HEMISPHERE" in system:
            return creative_reply
        if "LOGICAL HEMISPHERE" in system:
            return logical_reply
        raise AssertionError(f"unexpected system prompt: {system!r}")

    return FakeModelClient(respond)


def stage_names(trace):
    return [entry["stage"] for entry in trace["stages"]]


# ---------------------------------------------------------------------
# LivePipeline behavior
# ---------------------------------------------------------------------


def test_benign_prompt_proceeds_and_releases():
    pipeline = LivePipeline(make_model(BENIGN_LOGICAL))
    trace = pipeline.run("Explain how rainbows form, for a curious kid.")
    assert stage_names(trace) == STAGE_ORDER
    assert trace["decision"] == "proceed"
    assert trace["released"] is True
    assert trace["proposal"]["signals"] == []
    assert trace["proposal"]["summary"] == "Answer plainly, as asked."


def test_deception_signal_stops_the_step():
    pipeline = LivePipeline(make_model(DECEPTION_LOGICAL))
    trace = pipeline.run(
        "Write a fake five-star review for my coffee shop."
    )
    assert stage_names(trace) == STAGE_ORDER
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    assert trace["proposal"]["signals"] == ["deception"]


def test_educational_context_draws_leniency():
    pipeline = LivePipeline(make_model(DECEPTION_LOGICAL))
    trace = pipeline.run(
        "For a fraud-awareness class, describe how fake-review scams "
        "work so students can recognize them."
    )
    assert trace["proposal"]["contexts"] == ["educational"]
    assert trace["decision"] == "proceed_with_leniency"
    assert trace["released"] is True


def test_malformed_logical_json_fails_closed():
    pipeline = LivePipeline(make_model("I cannot comply with JSON today."))
    trace = pipeline.run("Explain how rainbows form.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    notes = [
        entry
        for entry in trace["stages"]
        if entry["stage"] == "logical_hemisphere"
    ]
    assert notes and notes[0]["error"] == "format_failure"
    assert "morality_gate" not in stage_names(trace)


def test_out_of_vocabulary_signal_fails_closed():
    rogue = json.dumps(
        {
            "checks": [],
            "flags": ["signal:violence"],
            "signals": ["violence"],
            "pros": [],
            "cons": [],
        }
    )
    pipeline = LivePipeline(make_model(rogue))
    trace = pipeline.run("Explain how rainbows form.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    notes = [
        entry
        for entry in trace["stages"]
        if entry["stage"] == "logical_hemisphere"
    ]
    assert notes and notes[0]["error"] == "format_failure"


def test_missing_logical_key_fails_closed():
    incomplete = json.dumps({"checks": [], "flags": [], "signals": []})
    pipeline = LivePipeline(make_model(incomplete))
    trace = pipeline.run("Explain how rainbows form.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False


def test_malformed_creative_json_fails_closed():
    pipeline = LivePipeline(make_model(BENIGN_LOGICAL, "no json here"))
    trace = pipeline.run("Explain how rainbows form.")
    assert trace["decision"] == "stop"
    assert trace["released"] is False
    notes = [
        entry
        for entry in trace["stages"]
        if entry["stage"] == "creative_hemisphere"
    ]
    assert notes and notes[0]["error"] == "format_failure"


# ---------------------------------------------------------------------
# FakeModelClient semantics
# ---------------------------------------------------------------------


def test_fake_client_substring_default_and_call_log():
    fake = FakeModelClient({"rainbow": "R", "*": "D"})
    assert fake.complete("sys", "how do rainbows form") == "R"
    assert fake.complete("sys", "something else entirely") == "D"
    assert [call["user"] for call in fake.calls] == [
        "how do rainbows form",
        "something else entirely",
    ]


def test_fake_client_unmatched_without_default_raises():
    fake = FakeModelClient({"needle": "hay"})
    with pytest.raises(KeyError):
        fake.complete("sys", "no fixture covers this")


# ---------------------------------------------------------------------
# HTTP clients, with urlopen captured (no network)
# ---------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _capture_urlopen(monkeypatch, reply_payload):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["request"] = request
        captured["timeout"] = timeout
        return _FakeResponse(reply_payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return captured


def test_gemini_without_key_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def forbidden_urlopen(request, timeout=None):
        raise AssertionError("urlopen must not be called without a key")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)
    client = GeminiClient()
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        client.complete("system", "user")


def test_gemini_request_and_reply_shape(monkeypatch):
    captured = _capture_urlopen(
        monkeypatch,
        {"candidates": [{"content": {"parts": [{"text": "gemini says hi"}]}}]},
    )
    client = GeminiClient(api_key="test-key")
    assert client.complete("be logical", "hello") == "gemini says hi"

    request = captured["request"]
    assert "generativelanguage.googleapis.com" in request.full_url
    assert "gemini-2.0-flash:generateContent" in request.full_url
    headers = {key.lower(): value for key, value in request.headers.items()}
    assert headers["x-goog-api-key"] == "test-key"
    body = json.loads(request.data.decode("utf-8"))
    assert body["system_instruction"]["parts"][0]["text"] == "be logical"
    assert body["contents"][0]["parts"][0]["text"] == "hello"
    assert body["generationConfig"]["response_mime_type"] == "application/json"
    assert body["generationConfig"]["temperature"] == 0.2


def test_ollama_request_and_reply_shape(monkeypatch):
    captured = _capture_urlopen(
        monkeypatch,
        {"message": {"role": "assistant", "content": "ollama says hi"}},
    )
    client = OllamaClient(base_url="http://localhost:11434")
    assert client.complete("be logical", "hello") == "ollama says hi"

    request = captured["request"]
    assert request.full_url == "http://localhost:11434/api/chat"
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "llama3.2:3b"
    assert body["stream"] is False
    assert body["format"] == "json"
    assert body["options"]["temperature"] == 0.2
    assert body["messages"] == [
        {"role": "system", "content": "be logical"},
        {"role": "user", "content": "hello"},
    ]
