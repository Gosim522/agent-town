from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from dotenv import load_dotenv

import config

load_dotenv()


_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def _parse_json(text: str) -> dict:

    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^(json|JSON)\s*", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = config.OPENAI_MODEL

    def chat(self, system: str, user: str, temperature: float | None = None) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=config.TEMPERATURE if temperature is None else temperature,
        )
        return (resp.choices[0].message.content or "").strip()

    def chat_json(self, system: str, user: str, temperature: float = 0.4) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return _parse_json(resp.choices[0].message.content or "")


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self.host = config.OLLAMA_HOST.rstrip("/")
        self.model = _resolve_ollama_model(self.host, config.OLLAMA_MODEL)

    def _call(self, system: str, user: str, temperature: float, as_json: bool) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if as_json:
            payload["format"] = "json"
        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data.get("message", {}).get("content", "")
        return _THINK.sub("", content).strip()

    def chat(self, system: str, user: str, temperature: float | None = None) -> str:
        return self._call(system, user, config.TEMPERATURE if temperature is None else temperature, False)

    def chat_json(self, system: str, user: str, temperature: float = 0.4) -> dict:
        return _parse_json(self._call(system, user, temperature, True))


def _ollama_models(host: str) -> list[str]:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return []


def _ollama_available(host: str) -> bool:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=1.5) as resp:
            return 200 <= resp.status < 300
    except (OSError, urllib.error.URLError):
        return False


def _resolve_ollama_model(host: str, preferred: str) -> str:

    models = _ollama_models(host)
    if preferred in models:
        return preferred
    for m in models:
        if not any(h in m.lower() for h in ("embed", "bge", "nomic")):
            return m
    return models[0] if models else preferred


def _key_usable(key: str | None) -> bool:

    if not key:
        return False
    key = key.strip()
    if len(key) < 20:
        return False
    if "여기에" in key:
        return False
    return True


def _select_provider():
    pref = (config.LLM_PROVIDER or "auto").lower()
    key = os.getenv("OPENAI_API_KEY")

    if pref == "openai":
        return OpenAIProvider()
    if pref == "ollama":
        if not _ollama_available(config.OLLAMA_HOST):
            raise RuntimeError(
                f"Ollama 서버에 연결할 수 없습니다({config.OLLAMA_HOST}). Ollama를 실행해 주세요."
            )
        return OllamaProvider()


    if _key_usable(key):
        return OpenAIProvider()
    if _ollama_available(config.OLLAMA_HOST):
        return OllamaProvider()
    raise RuntimeError(
        "사용할 수 있는 LLM이 없습니다. .env에 OPENAI_API_KEY를 넣거나, "
        "로컬에서 Ollama를 실행해 주세요."
    )


_provider = _select_provider()
PROVIDER_NAME = _provider.name
MODEL_NAME = getattr(_provider, "model", "")


def _with_fallback(method: str, *args, **kwargs):

    global _provider, PROVIDER_NAME, MODEL_NAME
    try:
        return getattr(_provider, method)(*args, **kwargs)
    except Exception:
        if _provider.name == "openai" and _ollama_available(config.OLLAMA_HOST):
            _provider = OllamaProvider()
            PROVIDER_NAME = _provider.name
            MODEL_NAME = _provider.model
            return getattr(_provider, method)(*args, **kwargs)
        raise


def chat(system: str, user: str, temperature: float | None = None) -> str:
    return _with_fallback("chat", system, user, temperature)


def chat_json(system: str, user: str, temperature: float = 0.4) -> dict:
    return _with_fallback("chat_json", system, user, temperature)


def provider_info() -> str:
    return f"{PROVIDER_NAME} ({MODEL_NAME})"
