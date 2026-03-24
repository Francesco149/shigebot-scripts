"""
openrouter.py — helper module for calling the OpenRouter API.

Import this from any script:

    import openrouter
    print(openrouter.ask("what is the meaning of life?"))

Or with a system prompt:

    print(openrouter.ask(user_msg, system="respond only in haiku"))
"""
import json
import os
import urllib.request

_API_KEY = os.environ["OPENROUTER_API_KEY"]
_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_MODEL = "openai/gpt-oss-20b" # cheapest good quality but slow
#_MODEL = "meta-llama/llama-3-8b-instruct" # also cheap and fast, not horrible
#_MODEL = "openai/gpt-4o-mini"  # cheap default, override as needed
#_MODEL = "arcee-ai/trinity-mini"


def ask(
    user: str,
    system: str = "",
    model: str = _MODEL,
    timeout: int = 20,
) -> str:
    """
    Send a chat completion request to OpenRouter and return the response text.

    Parameters
    ----------
    user:
        The user message content.
    system:
        Optional system prompt prepended before the user message.
    model:
        OpenRouter model string. Defaults to openai/gpt-4o-mini.
    timeout:
        Request timeout in seconds.

    Returns the response text, or an error string on failure.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})

    payload = json.dumps({"model": model, "messages": messages}).encode()

    req = urllib.request.Request(
        _API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        return f"HTTP {exc.code}: {body[:200]}"
    except Exception as exc:
        return f"error: {exc}"

    if "error" in data:
        return str(data["error"])

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        return f"unexpected response: {exc}"
