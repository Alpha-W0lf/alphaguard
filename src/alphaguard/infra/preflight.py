"""Ollama preflight — fail fast with pull instructions."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from alphaguard.config import Settings


class PreflightError(RuntimeError):
    pass


def _list_models(base_url: str) -> list[str]:
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PreflightError(
            f"Ollama unreachable at {base_url}. Start it with `ollama serve`, then "
            f"`ollama pull gemma4:e2b` (or fallback `ollama pull qwen3.5:4b`)."
        ) from exc
    return [m.get("name", "") for m in payload.get("models", [])]


def resolve_ollama_model(settings: Settings) -> str:
    names = _list_models(settings.ollama_base_url)
    wanted = settings.ollama_model
    fallback = settings.ollama_fallback_model

    def present(tag: str) -> bool:
        return any(n == tag or n.startswith(tag + ":") or n.split(":")[0] == tag for n in names) or (
            tag in names
        )

    # Exact or prefix match (ollama often returns name:tag)
    if any(n == wanted or n.startswith(wanted) for n in names):
        return wanted
    if any(n == fallback or n.startswith(fallback) for n in names):
        return fallback
    raise PreflightError(
        f"Ollama model {wanted!r} not found. Available={names}. "
        f"Pull with: `ollama pull {wanted}` "
        f"(or set OLLAMA_MODEL={fallback} after `ollama pull {fallback}`). "
        f"Note: gemma4:e2b may return HTTP 412 on older Ollama — upgrade Ollama "
        f"or use the documented fallback {fallback!r}."
    )


def preflight_ollama(settings: Settings) -> str:
    return resolve_ollama_model(settings)
