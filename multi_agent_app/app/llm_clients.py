"""Thin wrappers over OpenAI, Gemini and Claude + mock fallback."""
import time
from . import config, mock_llm


def _openai(system, user):
    from openai import OpenAI
    r = OpenAI(api_key=config.OPENAI_API_KEY).chat.completions.create(
        model=config.OPENAI_MODEL, temperature=0.3,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return r.choices[0].message.content


def _gemini(system, user):
    from google import genai
    from google.genai import types
    r = genai.Client(api_key=config.GEMINI_API_KEY).models.generate_content(
        model=config.GEMINI_MODEL, contents=user,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0.3))
    return r.text


def _claude(system, user):
    import anthropic
    r = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
        model=config.CLAUDE_MODEL, max_tokens=800, system=system,
        messages=[{"role": "user", "content": user}])
    return r.content[0].text


_PROVIDERS = {
    "openai": (_openai, lambda: config.OPENAI_API_KEY),
    "gemini": (_gemini, lambda: config.GEMINI_API_KEY),
    "claude": (_claude, lambda: config.ANTHROPIC_API_KEY),
}


def call(provider: str, role: str, system: str, user: str, live: bool):
    """Returns (text, latency_ms). Falls back to mock if live=False or key missing."""
    start = time.time()
    fn, key = _PROVIDERS[provider]
    try:
        if live and key():
            text = fn(system, user)
        else:
            text = mock_llm.MOCK[role](user)
    except Exception as e:                      # an API crash is itself a coordination failure
        text = f"[AGENT_ERROR] {provider}: {e}"
    return text or "", int((time.time() - start) * 1000)
