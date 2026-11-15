"""The only file that talks to the language model (OpenAI).

Before running, set your key in PowerShell:
    $env:OPENAI_API_KEY="your-key"
Optional: $env:LLM_MODEL="gpt-4o-mini"   (this is the default)
"""
import json
import os
import re

_client = None


def _get_client():
    global _client
    if _client is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError('OPENAI_API_KEY is not set. In PowerShell run: $env:OPENAI_API_KEY="your-key"')
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("The openai library is missing. Run: pip install openai")
        _client = OpenAI()
    return _client


def chat(task, system, messages, temperature=0.7):
    """Send the messages to OpenAI and return the reply text.
    `task` is only a label ('agent', 'skillmap', 'generate', 'solve'); the other files pass it in."""
    r = _get_client().chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        messages=[{"role": "system", "content": system}] + messages)
    return r.choices[0].message.content


def parse_json(text):
    """Pull the first JSON object out of a model reply. Returns None if it fails."""
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text)
    a, b = t.find("{"), t.rfind("}")
    if a == -1 or b <= a:
        return None
    try:
        return json.loads(t[a:b + 1])
    except json.JSONDecodeError:
        return None