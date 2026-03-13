import json
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv():
        return False

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


load_dotenv()


def _build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


client = _build_client()


def ask_llm(prompt, model=None):
    if client is None:
        return None

    response = client.responses.create(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=prompt,
        temperature=0,
    )

    return response.output_text


def ask_llm_json(prompt, model=None):
    text = ask_llm(prompt, model=model)
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
