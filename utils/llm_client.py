import json
import os
import socket
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


def load_local_env():
    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip("'\"")


load_local_env()


def build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(
        api_key=api_key,
        timeout=float(os.getenv("OPENAI_TIMEOUT", "8")),
    )


client = build_client()
last_error = None


def get_llm_status():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"mode": "fallback", "reason": "OPENAI_API_KEY is missing"}

    if OpenAI is None:
        return {"mode": "fallback", "reason": "openai package is not installed in this interpreter"}

    try:
        socket.gethostbyname("api.openai.com")
    except OSError as error:
        return {"mode": "fallback", "reason": f"DNS lookup failed for api.openai.com: {error}"}

    if client is None:
        return {"mode": "fallback", "reason": "OpenAI client could not be initialized"}

    if last_error:
        return {"mode": "api", "reason": f"Last API error: {last_error}"}

    return {"mode": "api", "reason": "OpenAI API is configured"}


def ask_llm(prompt):
    global last_error

    if client is None:
        last_error = "OpenAI client is not initialized"
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"    LLM request started ({model})")

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        last_error = None
    except Exception as error:
        last_error = f"{type(error).__name__}: {error}"
        print(f"    LLM request failed: {last_error}")
        return None

    print("    LLM request finished")
    return response.output_text


def ask_llm_json(prompt):
    text = ask_llm(prompt)
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def close_client():
    if client is None:
        return

    try:
        client.close()
    except Exception:
        pass
