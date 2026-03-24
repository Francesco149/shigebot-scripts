"""
!urban [term]
Look up a term on Urban Dictionary.
If no term is given, returns a random definition.
"""
import sys
import urllib.request
import urllib.parse
import json

term = " ".join(sys.argv[1:]).strip()

if term:
    url = "https://api.urbandictionary.com/v0/define?" + \
        urllib.parse.urlencode({"term": term})
else:
    url = "https://api.urbandictionary.com/v0/random"

try:
    with urllib.request.urlopen(url, timeout=8) as resp:
        data = json.loads(resp.read())
except Exception as e:
    print(f"error: {e}")
    sys.exit(1)

entries = data.get("list", [])

if not entries:
    print(f"no definition found for: {term}" if term else "no results")
    sys.exit(0)

entry = entries[0]
word = entry.get("word", "?")
defn = entry.get("definition", "").replace("\r", "").replace("\n", " ").strip()
example = entry.get("example", "").replace(
    "\r", "").replace("\n", " ").strip()

MAX = 400

if len(defn) > MAX:
    defn = defn[:MAX].rsplit(" ", 1)[0] + "…"

print(f"{word}: {defn}")

if example:
    if len(example) > MAX:
        example = example[:MAX].rsplit(" ", 1)[0] + "…"

    print(f"e.g. {example}")
