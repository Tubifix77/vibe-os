"""VibeOS Computer — Ollama streaming client."""

import json
import requests
from config import Config


def chat_stream(cfg: Config, messages: list[dict]) -> str:
    """Send messages to Ollama and stream the response.

    Yields printed tokens in real-time and returns the full
    assembled response text when the stream ends.
    """
    payload = {
        "model": cfg.ollama_model,
        "messages": messages,
        "stream": True,
        "think": False,
    }

    try:
        resp = requests.post(
            f"{cfg.ollama_base}/api/chat",
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
    except requests.ConnectionError:
        return "[ERROR] Cannot reach Ollama at {cfg.ollama_base}. Is it running?"
    except requests.Timeout:
        return "[ERROR] Ollama request timed out."
    except requests.HTTPError as e:
        return f"[ERROR] Ollama returned {e.response.status_code}: {e.response.text}"

    full = []
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line)
        except json.JSONDecodeError:
            continue

        token = chunk.get("message", {}).get("content", "")
        if token:
            print(token, end="", flush=True)
            full.append(token)

        if chunk.get("done", False):
            break

    print()  # newline after stream ends
    return "".join(full)


# ── quick self-test ──────────────────────────────────────
if __name__ == "__main__":
    cfg = Config()
    msgs = [
        {"role": "system", "content": "Reply in one sentence."},
        {"role": "user", "content": "What is warp drive?"},
    ]
    print(f"Model: {cfg.ollama_model}")
    print(f"Endpoint: {cfg.ollama_base}")
    print("-" * 40)
    result = chat_stream(cfg, msgs)
    print("-" * 40)
    print(f"Total length: {len(result)} chars")
