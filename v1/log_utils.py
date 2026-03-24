import sqlite3
import re
import sys
import os
import uuid

DB_FILE = "logs.db"
MAX_RESULTS = 10
RETRO_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "twitch.markov.bot")


def get_effective_id(username, message):
    twitch_uuid = os.environ.get('MSG_ID')
    if twitch_uuid:
        return twitch_uuid

    # Generate a deterministic UUID based on username + message
    # This is "idempotent": same input = same UUID every time
    combined_string = f"{username}:{message}"
    return str(uuid.uuid5(RETRO_NAMESPACE, combined_string))


def regexp(expr, item):
    """Regex helper for SQLite."""
    try:
        reg = re.compile(expr, re.IGNORECASE)
        return reg.search(item) is not None
    except Exception:
        return False


def open_db():
    """Returns a connection with WAL mode and Regex support."""
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.create_function("REGEXP", 2, regexp)
    init_db(conn)
    return conn


def init_db(conn):
    """Creates the necessary tables if they don't exist."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    current_version = cursor.fetchone()[0]

    # MIGRATION: Version 0 -> 1 (Initial Setup)
    # (If the table is new, user_version is 0)

    if current_version < 1:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                username TEXT,
                message TEXT,
                reply_to_msg_id TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS markov_chain (
                username TEXT,
                word1 TEXT,
                word2 TEXT,
                next_word TEXT,
                frequency INTEGER DEFAULT 1,
                PRIMARY KEY (username, word1, word2, next_word)
            )
        ''')

        cursor.execute('''
          CREATE INDEX IF NOT EXISTS idx_logs_user_time ON chat_logs (
            username, timestamp DESC);
        ''')

        cursor.execute('PRAGMA user_version = 1')
        conn.commit()


def log_message(conn, username, message):
    """
    Returns True if the message was successfully inserted (new).
    Returns False if the msg_id already exists (duplicate).
    """
    msg_id = get_effective_id(username, message)
    cursor = conn.cursor()
    try:
        # INSERT OR IGNORE skips the write if the Primary Key exists
        cursor.execute('''
            INSERT OR IGNORE INTO chat_logs
            (id, timestamp, username, message, reply_to_msg_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            msg_id,
            os.environ.get('TIMESTAMP', 'UNKNOWN'),
            username,
            message,
            os.environ.get('REPLY_TO_ID', None)
        ))
        conn.commit()
        # If rowcount is 0, nothing was inserted (it was a duplicate)
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False


def update_markov(conn, username, message):
    """Tokenizes a message and updates the user's Markov chain."""
    words = message.split()
    if len(words) < 2:
        return  # Need at least 2 words for a bigram model

    # Add Start/End tokens so the bot knows how to begin and end sentences
    tokens = ["__START__", "__START__"] + words + ["__END__"]

    cursor = conn.cursor()
    for i in range(len(tokens) - 2):
        w1, w2, next_word = tokens[i], tokens[i + 1], tokens[i + 2]

        # Upsert: Insert new transition, or increment frequency if it exists
        cursor.execute('''
            INSERT INTO markov_chain (username, word1, word2, next_word, frequency)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(username, word1, word2, next_word)
            DO UPDATE SET frequency = frequency + 1
        ''', (username, w1, w2, next_word))

    conn.commit()


def parse_twitch_cmd(full_message, cmd_name):
    prefix = full_message
    query = None
    mode = None

    # 1. Hard Split
    if '=?' in full_message:
        prefix, query = full_message.split('=?', 1)
        mode = 'contains'
    elif '=' in full_message:
        prefix, query = full_message.split('=', 1)
        mode = 'starts'
    elif '/' in full_message:
        prefix, query = full_message.split('/', 1)
        mode = 'regex'

    if query:
        query = query.strip()

    # 2. Parse Base Command
    match = re.match(
        rf'^{os.environ["PREFIX"]}{cmd_name}(\d*)',
        prefix
    )
    if not match:
        return None

    limit = min(max(1, int(match.group(1))
                if match.group(1) else 1), MAX_RESULTS)

    # 3. Handle Exclusions
    exclude_list = {'shigebot', 'shigemirror'}

    # Process manual flags first
    for u in re.findall(r'\+u (\S+)', prefix.lower()):
        exclude_list.discard(u)
    for u in re.findall(r'-u (\S+)', prefix.lower()):
        exclude_list.add(u)

    # 4. Target User Identification
    clean_prefix = re.sub(r'[+-]u \S+', '', prefix)
    user = None
    user_match = re.search(r'\bu (\S+)\b|\bme\b', clean_prefix, re.IGNORECASE)

    if user_match:
        val = (user_match.group(1) or user_match.group(0)).lower()
        user = os.environ.get('NICK', '').lower() if val == 'me' else val

        # --- NEW LOGIC: Explicit targeting overrides exclusion ---
        if user in exclude_list:
            exclude_list.discard(user)

    return {
        'limit': limit,
        'user': user,
        'exclude_users': list(exclude_list),
        'query': query,
        'mode': mode,
        'show_commands': '+commands' in prefix.lower(),
    }


def format_ts(ts_str):
    """
    Converts ISO '2026-03-26T17:11:31' to '[2026-03-26 17:11]'
    """
    if "UNKNOWN" in ts_str:
        return ""
    try:
        # isoformat() is very predictable: YYYY-MM-DDTHH:MM:SS...
        date_part = ts_str[:10]  # Gets YYYY-MM-DD
        time_part = ts_str[11:16]  # Gets HH:MM
        return f"[{date_part} {time_part}]"
    except Exception:
        return "[????-??-?? ??:??]"
