
"""
!translate [text]

Use AI to translate to english
"""
import os
import sys
import openrouter
import ratelimit as rl

tl_rlim = rl.RateLimit(
    state_file="../translate-rate_limit_state.json",
    global_limit_per_hour=100,
    user_limit_per_week=1000,
)


def smart(text):
    allow, _ = tl_rlim.allow(os.environ['NICK'])
    if not allow:
        return "<english>"

    system = """
Determine whether the message is non-english or contains enough non-english to
be worth translating.

CRITICAL RULES:
- Do not bother translating messages that only contain single words that look
foreign, this is a twitch chat and sometimes people mis spell or use
abbreviations and emojis.

Your response can only be one of two:
- <english> for messages that contain only english
- <translate> for messages worth translating
Message:
"""
    answer = openrouter.ask(
        system + text, model="meta-llama/llama-3.1-8b-instruct")
    if "<english>" in answer:
        return "<english>"

    system = """
Respond with a translation of the chat message if it's non-english, otherwise respond <english>.
If it's partially english, respond with the translation of the non-english
parts.

CRITICAL RULES:
- Do not bother translating messages that only contain single words that look
foreign, this is a twitch chat and sometimes people mis spell or use
abbreviations and emojis.

Your response can only be one of two:
- <english> for messages that contain only english
- translation for messages that contain any foreign text, with no preamble or anything. just the translation, wrap the message with the emoji of the flag that represents the language. Transliterate any foreign names as well, there must be no non-english characters left.
Message:
"""
    return openrouter.ask(system + text)


if __name__ == "__main__":
    args = sys.argv[1:]
    text = " ".join(args).strip()
    resp = smart(text)
    if "<english>" not in resp:
        print(resp)
