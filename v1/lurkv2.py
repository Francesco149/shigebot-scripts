"""
lurk chatter — called once per incoming chat message, then exits.

Storage is handled entirely by db.py (one lurk.db file).
"""

import os
import random
import sys
import time

import openrouter
import ratelimit as rl
from lurk_db import DB

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

#DIALOGUE_MODEL = "meta-llama/llama-3.1-8b-instruct" # super cheap and fast
#DIALOGUE_MODEL = "meta-llama/llama-3-8b-instruct" # super cheap and fast
DIALOGUE_MODEL = "openai/gpt-4o-mini" # not that cheap but fast and good quality
MEMORY_MODEL = "openai/gpt-oss-20b" # prio reasoning

MAX_RECENT = 20
MAX_MSG_LEN = 200
MESSAGE_WINDOW_SECS = 600

INACTIVITY_TRIGGER = 60 * 30
COOLDOWN_AFTER_SPEAK = 60 * 5

MEMORY_MAX_WORDS = 100
MEMORY_PRUNE_TO = 3
MEMORY_SIM_THRESH = 0.45   # Jaccard on content-word fingerprints

# Each entry is a distinct behavioural mode injected into the response prompt.
# One is chosen per response, avoiding the last STYLE_AVOID_LAST_N used.
# This enforces variety with zero extra LLM calls.
RESPONSE_STYLES = [
    # cold/dismissive
    "Dismiss them in 3 words or fewer. Flat, not dramatic. Like you barely registered they exist.",
    # targeted observation
    "Point out one specific dumb thing they just did or said. State it like a fact, no editorializing.",
    # memory callback
    "Reference one thing from your memories of them. Make it feel like you've been keeping score.",
    # dry sarcasm
    "Agree with them in a way that makes it worse. Keep it short and deadpan.",
    # silence treatment
    "Acknowledge them with minimal words — like you're doing them a favour by even responding.",
    # factual contempt
    "Say the most obvious, undeniable negative truth about what they just said or did.",
    # redirect
    "Ask them a single question that implies they're an idiot without saying it directly.",
]
STYLE_AVOID_LAST_N = 3

# ---------------------------------------------------------------------------
# Rate limiters (state files kept external, owned by another module)
# ---------------------------------------------------------------------------

mem_rlim = rl.RateLimit(
    state_file="../lurk-memory-rate_limit_state.json",
    global_limit_per_hour=100,
    user_limit_per_week=1000,
)
mention_rlim = rl.RateLimit("../lurk-mention-rate_limit_state.json")

# ---------------------------------------------------------------------------
# Persona (single source of truth — referenced in every prompt)
# ---------------------------------------------------------------------------

PERSONA = (
    "You are an ice-cold anime girl lurking in Twitch chat. "
    "You are contemptuous, not theatrical. Your insults are short, flat, and specific — "
    "never elaborate metaphors or flowery similes. You talk like someone who can't be "
    "bothered to waste more than one breath on these people. "
    "BAD (too wordy/metaphor-heavy): 'Your attempts at conversation are as coherent as a broken printer.' "
    "GOOD (flat, specific, Twitch-native): 'you've said this three times now. embarrassing.' "
    "Users call you <you> or 'the bot'. You appear as <you> in chat logs."
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def replace_bot_nick(text: str) -> str:
    """Replace occurrences of the bot's nick with the <you> placeholder."""
    nick = os.environ["BOT_NICK"].lower()
    return " ".join(
        "<you>" if nick in word.lower() else word
        for word in text.split()
    )


def format_messages(messages: list[dict]) -> str:
    """
    Render a message list as a prompt-ready chat log. Includes the message ID
    so the model can reference it unambiguously when picking a reply target.

    Format: [seen] [HH:MM:SS] #<id> username: content (reply to …)
    """
    lines = []
    for m in messages[-10:]:
        seen = "[seen] " if m.get("seen") else ""
        ts = time.strftime("%H:%M:%S", time.localtime(m["ts"]))
        mid = f"#{m['id']}"
        reply = (
            f" (reply to `{m['reply_to_user']}: {m['reply_to_msg']}`)"
            if m.get("reply_to_user") else ""
        )
        lines.append(
            f"{seen}[{ts}] {mid} {m['username']}: {m['content']}{reply}")
    return "\n".join(lines)


def format_memories(memories: list[dict]) -> str:
    """
    Render memories with relative-age labels so the model has real recency
    signals rather than relying purely on list ordering.
    """
    if not memories:
        return "(none)"
    now = time.time()
    lines = []
    for m in memories:
        age = now - m["created_at"]
        if age < 3600:
            label = f"{int(age / 60)}m ago"
        elif age < 86400:
            label = f"{int(age / 3600)}h ago"
        else:
            label = f"{int(age / 86400)}d ago"
        lines.append(f"[{label}] {m['content']}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Cross-reference helpers
# ---------------------------------------------------------------------------


def _users_mentioned_in(db: DB, text: str, exclude: str) -> set[str]:
    """Return any word in `text` that has memories and isn't `exclude`."""
    return {w for w in text.split() if w != exclude and db.get_memories(w)}


def _cross_reference_block(db: DB, users: set[str]) -> str:
    parts = []
    for user in users:
        mems = db.get_memories(user)
        if mems:
            parts.append(
                f"User also mentions '{user}', your memories of them:\n"
                + format_memories(mems)
            )
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Response style selection
# ---------------------------------------------------------------------------


def _pick_style(history: list[int]) -> int:
    recent = set(history[-STYLE_AVOID_LAST_N:])
    candidates = [i for i in range(len(RESPONSE_STYLES)) if i not in recent]
    return random.choice(candidates or list(range(len(RESPONSE_STYLES))))

# ---------------------------------------------------------------------------
# Memory deduplication
# ---------------------------------------------------------------------------


_STOPWORDS = {
    "is", "the", "a", "an", "and", "or", "to", "at", "in", "of", "for",
    "you", "they", "their", "about", "with", "has", "was", "were", "been",
    "but", "not", "its", "also", "just",
}


def _fingerprint(text: str) -> set[str]:
    return {w for w in text.lower().split() if len(w) >
            3 and w not in _STOPWORDS}


def _proper_nouns(text: str) -> set[str]:
    """
    Words that appear capitalised mid-sentence are likely named entities
    (game titles, usernames, etc.) — useful for topic-collision detection.
    We skip the first word since that's capitalised by grammar, not meaning.
    """
    words = text.split()
    return {w.rstrip(".,!?")
            for w in words[1:] if w and w[0].isupper() and len(w) > 2}


def _too_similar(new_line: str, existing: list[dict]) -> bool:
    """
    Returns True if new_line is too similar to any existing memory.

    Two checks, either sufficient to reject:
    1. Content-word Jaccard above threshold (catches paraphrases).
    2. Shared proper noun + at least one other shared content word
       (catches "three different sentences all about Deep Rock Galactic").
    """
    new_fp = _fingerprint(new_line)
    new_pn = _proper_nouns(new_line)

    for m in existing:          # check ALL memories, not just last N
        content = m["content"]
        fp = _fingerprint(content)
        union = new_fp | fp

        # Check 1: general content similarity
        if union and len(new_fp & fp) / len(union) > MEMORY_SIM_THRESH:
            return True

        # Check 2: same named entity + overlapping topic
        # e.g. two memories both mentioning "Galactic" and "brags"
        if new_pn & _proper_nouns(content) and len(new_fp & fp) >= 1:
            return True

    return False

# ---------------------------------------------------------------------------
# Core LLM calls
# ---------------------------------------------------------------------------


def should_respond(messages: list[dict], gap: int, since_spoke: int) -> bool:
    prompt = f"""{PERSONA}

Recent chat:
{format_messages(messages)}

Context:
- Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Recent message count: {len(messages)}
- Seconds since last message: {gap}
- Seconds since you last spoke: {since_spoke}

Should you send a message right now?

Guidelines:
- Be rare and unpredictable
- More likely if chat is dead or awkward
- Occasionally jump in naturally
- Avoid interrupting fast-paced chat too often

Respond ONLY with 'yes' or 'no'.
"""
    try:
        return openrouter.ask(prompt, model=MEMORY_MODEL).strip().lower().startswith("y")
    except Exception:
        return False


def _pick_reply_target(messages: list[dict]) -> int | None:
    """
    Ask the model which message ID to respond to.
    Returns the message ID, or None to fall back to the latest.
    """
    chat_log = format_messages(messages)
    prompt = f"""{PERSONA}

Recent chat (message IDs shown as #N):
{chat_log}

Which message should you respond to? Output ONLY the integer message ID (the # number).
- Prioritize newer messages and messages that mention you
- Do NOT pick messages marked [seen]
"""
    try:
        return int(openrouter.ask(prompt, model=MEMORY_MODEL).strip().lstrip("#"))
    except Exception:
        return None


def generate_message(
        db: DB, messages: list[dict], mentioned: bool = False) -> str | None:
    # Pick target message
    if mentioned or len(messages) <= 1:
        target = messages[-1]
    else:
        picked_id = _pick_reply_target(messages)
        target = next(
            (m for m in messages if m["id"] == picked_id), messages[-1])

    user = target["username"]
    memories = db.get_memories(user)
    chan_memories = db.get_memories("#channel")

    cross_users = (
        _users_mentioned_in(db, format_memories(memories), user)
        | _users_mentioned_in(db, target["content"], user)
    )
    cross_block = _cross_reference_block(db, cross_users)

    style_history = db.get_state("style_history", [])
    style_idx = _pick_style(style_history)
    style_label = RESPONSE_STYLES[style_idx]

    prompt = f"""{PERSONA}

Your memories of this user (oldest → newest):
{format_memories(memories)}

{cross_block}

Channel memories:
{format_memories(chan_memories)}

Recent chat:
{format_messages(messages)}

Responding to:
{format_messages([target])}

**Response style for THIS message ONLY: {style_label}**

Rules:
- One sentence or fewer; no timestamps; no username prefix in your reply
- Do not open with "oh honey / oh sweetie / oh please"
- Do not overuse emoji
- Newer memories carry more weight unless context demands otherwise
- Never repeat a roast topic you used recently with this user
- The message is your focus; memories add sharpness, not the whole reply
"""
    db.mark_seen(target["id"])

    response = openrouter.ask(prompt, model=DIALOGUE_MODEL)
    if not response:
        return None

    # Persist the bot's own reply so it appears in future context windows
    bot_msg_id = db.add_message(
        ts=int(time.time()),
        username="<you>",
        content=response,
        reply_to_user=user,
        reply_to_msg=target["content"],
        is_bot=True,
    )
    db.mark_seen(bot_msg_id)

    style_history.append(style_idx)
    db.set_state("style_history", style_history[-10:])

    return response

# ---------------------------------------------------------------------------
# Memory update (deferred — runs after the bot has already printed its reply)
# ---------------------------------------------------------------------------


def update_memory(db: DB, messages: list[dict]):
    # Separate the bot's response (last message) from the conversation
    response = ""
    if messages and messages[-1]["username"] == "<you>":
        response = messages[-1]["content"]
        messages = messages[:-1]

    if not messages:
        return

    user = messages[-1]["username"]
    last_log = format_messages(messages[-1:])
    prior_log = format_messages(messages[:-1])

    # 1. Channel-level memory
    chan_mems = db.get_memories("#channel")
    chan_prompt = f"""{PERSONA}

Channel memories so far:
{format_memories(chan_mems)}

Prior chat:
{prior_log}

Latest message:
{last_log}

Your response: {response or "(you didn't respond)"}

Write ONE new thing to remember about this chatroom interaction. Under 15 words.
- Always name the user (e.g. "alice: asked the same question twice", "bob: rage-quit mid-match")
- State the bare fact. Do NOT explain, editorialize, or add "showcasing/proving/resulting in" clauses.
- BAD: "alice consistently fails to read the map, showcasing poor spatial awareness"
- GOOD: "alice ignores the map every single time"
- Write it as a cold internal log entry, not a performance review.
"""
    new_chan = openrouter.ask(chan_prompt, model=MEMORY_MODEL).strip()
    if new_chan and not _too_similar(new_chan, chan_mems):
        db.add_memory("#channel", new_chan)
    if db.memory_word_count("#channel") > MEMORY_MAX_WORDS:
        db.prune_memories("#channel", MEMORY_PRUNE_TO)

    # 2. Per-user memory
    user_mems = db.get_memories(user)
    chan_mems = db.get_memories("#channel")   # re-fetch after channel update

    cross_users = (
        _users_mentioned_in(db, format_memories(user_mems), user)
        | _users_mentioned_in(db, messages[-1]["content"], user)
    )
    cross_block = _cross_reference_block(db, cross_users)

    user_prompt = f"""{PERSONA}

Your memories of this user:
{format_memories(user_mems)}

{cross_block}

Channel memories:
{format_memories(chan_mems)}

Prior chat:
{prior_log}

Latest message from this user:
{last_log}

Your response: {response or "(you didn't respond)"}

Write ONE new thing to remember about this user. Under 15 words.
- State the bare fact. Do NOT explain, editorialize, or add "showcasing/proving/resulting in" clauses.
- BAD: "consistently underestimates mechanics, showcasing a lack of understanding"
- GOOD: "doesn't understand how stamina works"
- Write it as a cold internal log entry, not a performance review.
- Do not include the username.
"""
    new_user = openrouter.ask(user_prompt, model=MEMORY_MODEL).strip()
    if new_user and not _too_similar(new_user, user_mems):
        db.add_memory(user, new_user)
    if db.memory_word_count(user) > MEMORY_MAX_WORDS:
        db.prune_memories(user, MEMORY_PRUNE_TO)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    now = int(time.time())
    username = os.environ["NICK"]
    content = replace_bot_nick(" ".join(sys.argv[1:])[:MAX_MSG_LEN])
    reply_to_user = replace_bot_nick(os.environ.get("REPLY_TO_USER", ""))
    reply_to_msg = os.environ.get("REPLY_TO_MESSAGE", "")

    mentioned = "<you>" in content or "<you>" in reply_to_user

    with DB() as db:
        db.prune_old_messages(MESSAGE_WINDOW_SECS)

        # Read the previous last-message timestamp BEFORE inserting the new
        # message — otherwise gap is always ~0 since messages[-1] would be
        # the message we're currently processing.
        prev_messages = db.get_recent_messages(MESSAGE_WINDOW_SECS, limit=1)
        prev_last_msg_ts = prev_messages[-1]["ts"] if prev_messages else now
        last_spoke = db.get_state("last_spoke_ts", 0)
        gap = now - prev_last_msg_ts
        since_spoke = now - last_spoke

        db.add_message(
            ts=now,
            username=username,
            content=content,
            reply_to_user=reply_to_user,
            reply_to_msg=reply_to_msg,
        )

        messages = db.get_recent_messages(
            MESSAGE_WINDOW_SECS, limit=MAX_RECENT)

        run_memory_update = mentioned or mem_rlim.allow(username)[0]

        # --- Decide whether to speak ---

        spoke = False

        if mentioned:
            allowed, wait_msg = mention_rlim.allow(username)
            if username == "lolisamurai":
                allowed = True # for debugging
            if not allowed:
                print(wait_msg, file=sys.stderr)
            else:
                msg = generate_message(db, messages, mentioned=True)
                if msg:
                    print(msg)
                    spoke = True

        elif gap > INACTIVITY_TRIGGER:
            if since_spoke >= COOLDOWN_AFTER_SPEAK:
                if should_respond(messages, gap, since_spoke):
                    msg = generate_message(db, messages)
                    if msg:
                        print(msg)
                        spoke = True

        else:
            span = messages[-1]["ts"] - messages[0]["ts"]
            rate = len(messages) / span if span > 0 else 0
            p = 0.6 * (1 - min(rate * 0.3, 1.0))

            if (
                random.random() <= p
                and since_spoke >= COOLDOWN_AFTER_SPEAK
                and should_respond(messages, gap, since_spoke)
            ):
                msg = generate_message(db, messages)
                if msg:
                    print(msg)
                    spoke = True

        if spoke:
            db.set_state("last_spoke_ts", now)

        if run_memory_update:
            # Re-fetch so the snapshot includes any bot reply we just wrote
            update_memory(db, db.get_recent_messages(
                MESSAGE_WINDOW_SECS, limit=MAX_RECENT))


if __name__ == "__main__":
    main()
