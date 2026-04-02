# shigebot: v2
"""
!urban [term] — Urban Dictionary lookup.

Usage:
  !urban          — random definition
  !urban <term>   — definition for term

⚠ Explicit language — only enable in consenting channels.
"""
import json
import sys
import urllib.parse
import urllib.request

import shigebot as sb

_BASE = "https://api.urbandictionary.com/v0"
_MAX  = 400


def main():
    term = " ".join(sb.ctx.args).strip()
    url = (
        f"{_BASE}/define?{urllib.parse.urlencode({'term': term})}"
        if term else f"{_BASE}/random"
    )

    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        sb.say(f"error: {exc}")
        return

    entries = data.get("list", [])
    if not entries:
        sb.say(f"no definition found for: {term}" if term else "no results")
        return

    entry   = entries[0]
    word    = entry.get("word", "?")
    defn    = entry.get("definition", "").replace("\r", "").replace("\n", " ").strip()
    example = entry.get("example",    "").replace("\r", "").replace("\n", " ").strip()

    if len(defn) > _MAX:
        defn = defn[:_MAX].rsplit(" ", 1)[0] + "…"

    sb.say(f"{word}: {defn}")

    if example:
        if len(example) > _MAX:
            example = example[:_MAX].rsplit(" ", 1)[0] + "…"
        sb.say(f"e.g. {example}")
