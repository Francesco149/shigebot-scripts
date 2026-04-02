# shigebot scripts (v2)

v2 is a clean rewrite of the script API. All scripts import
`shigebot as sb` to access a rich context object, typed data stores, and
output helpers. v1 and v2 scripts coexist without changes to the runner.

See [`SPEC.md`](SPEC.md) for the full API contract.

---

## Setup

1. Copy `shigebot.py` to the bot's `working_dir` (same directory as your scripts).
2. Apply the changes described in `RUNNER_PATCH.py` to `shigebot/runner.py`
   and `shigebot/bot.py` to enable `SHIGEBOT_CTX` injection.
3. Add v2 script gist URLs to `[scripts]` in `shigebot.toml` as normal.

---

## Writing a v2 script

Every v2 script starts with the version marker and imports the runtime:

```python
# shigebot: v2
import shigebot as sb

# sb.ctx  — full invocation context (user, channel, args, ...)
# sb.data — per-script, per-channel key-value store
# sb.channel — channel-shared key-value store (cross-script)
# sb.global_ — global key-value store (cross-channel)
# print() / sb.say() — send a line to chat
```

All data stores are backed by SQLite with WAL journaling and are safe for
concurrent access from multiple script processes.

### Quick example

```python
# shigebot: v2
"""!points — show your campbucks balance."""
import shigebot as sb

bal = sb.channel.get(f"bank:balance:{sb.ctx.user}", 0)
sb.say(f"{sb.ctx.user} has {bal} campbucks 💰")
```

### Data store cheatsheet

```python
# script-private data (namespace "script:<name>")
sb.data.get("key", default)
sb.data.set("key", value)
sb.data.incr("key", amount=1)

# shared channel data (bank balances, game state, etc.)
sb.channel.get("bank:balance:alice", 0)
sb.channel.set("bank:balance:alice", 500)

# atomic multi-key operation
with sb.channel.transaction() as tx:
    a = tx.get("bank:balance:alice", 0)
    b = tx.get("bank:balance:bob",   0)
    tx.set("bank:balance:alice", a - 100)
    tx.set("bank:balance:bob",   b + 100)

# raw SQLite for complex queries
with sb.db() as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS my_table ...")

# global data (rarely needed)
sb.global_.get("key", default)
```

### Migrating v1 pickle state

```python
# Run once per channel — safe to call repeatedly
sb.migrate.from_pickle(sb.data, "state", "old_state.pickle")

# Bulk per-user migration (e.g. bank balances)
for stem, val in sb.migrate.pickles_in(sb.ctx.channel_dir).items():
    if not stem.startswith("__"):
        sb.channel.set(f"bank:balance:{stem}", int(val))
```

---

## Scripts

### `!hi`

```toml
hi = "https://gist.github.com/Francesco149/43beeeda657c2fc99cb68fa64a72cd82"
```

Ping command. Replies with `hi :)` and a random float 0–100.

---

### `!8ball`

Originally made by [Painketsu](https://twitch.tv/Painketsu).

```toml
8ball = "https://gist.github.com/Francesco149/087c9dffeaa90a03b0dff68e883de79a"
```

Magic 8-ball. Prints a random answer. Ask it any question and let it decide
your fate. We take no responsibility for any resulting life choices.

---

### `!flip`

Originally made by [Painketsu](https://twitch.tv/Painketsu).

```toml
flip = "https://gist.github.com/Francesco149/cebae605c965260db8d9a0e3dcea60f6"
```

Coin flip. 1/101 chance of landing on the side.

- `!flip`

---

### `!slap [target]`

```toml
slap = "https://gist.github.com/Francesco149/47e663b1a71ba97885be5b9de7268e04"
```

Classic IRC slap.

- `!slap` — slap yourself
- `!slap <target>` — slap target

---

### `!area`

```toml
area = "https://gist.github.com/Francesco149/..."
```

Posts the tablet area image.

---

### `!camp`

```toml
camp = "https://gist.github.com/Francesco149/..."
```

The camp never dies.

---

### `!pepe`

```toml
pepe = "https://gist.github.com/Francesco149/cd81efba346932dc58efe6a50c7b752f"
```

Prints a random pepe emote from the current seasonal set.

Base set: `FeelsAmazingMan`, `FeelsGoodMan`, `FeelsBadMan`, `FeelsBirthdayMan`

October: `FeelsPumpkinMan` added.
December: `FeelsSnowyMan`, `FeelsSnowMan` added.

#### pepe exports

```python
import pepe

current = pepe.get_set()        # current month's set
october = pepe.get_set(month=10)
```

---

### `!4/4`

```toml
"4/4" = "https://gist.github.com/Francesco149/c12a9d0cc5b5c02b8b4b8eb47ce556f5"
```

Simulate guessing N/N pepes. For each pepe in the current set, bets a random
pepe then draws a random result. Prints the pairs and final score.

Requires: `pepe` module listed in `[scripts]`.

---

### ambient: simple

```toml
simple = "https://gist.github.com/Francesco149/91b1837fccd26b49394e9b03b0337faa"
```

Ambient dispatcher for hardcoded text responses. Edit `_CMDS` at the top of
the script to add responses for your channel. Matches messages that *start
with* the trigger string (case-insensitive).

Default commands:
- `!area` — tablet area image
- `!camp` — the camp never dies

---

### `!urban [term]`

```toml
urban = "https://gist.github.com/Francesco149/722223e7af346eb1e2dbc3e9f6fe1a53"
```

Urban Dictionary lookup.

- `!urban` — random definition
- `!urban <term>` — definition for term

⚠ May return explicit or politically charged content. Only enable in channels
where users have consented to this.

---

### `!weather <city>`

```toml
weather = "https://gist.github.com/Francesco149/97deeabf4b8af0991df890da927a972e"
```

Current weather via OpenWeatherMap.

- `!weather Rome`
- `!weather London, GB`

Required env var: `OPENWEATHERMAP_API_KEY`

---

## Shared channel data key reference

All scripts that read or write `sb.channel` must use these key names.
Adding new keys requires updating both this table and `SPEC.md §5`.

| Key | Type | Written by | Description |
|-----|------|------------|-------------|
| `bank:balance:{user}` | int | bank, slots, rr, fish, trivia, mirage | campbucks |
| `bank:claim:{user}` | float (timestamp) | bank | next weekly claim time |
| `rr:lock:{user}` | float (timestamp) | rr | next daily reset |
| `rr:chamber:{user}` | dict | rr | `{chamber, pos, won_today}` |
| `rr:stats:{user}` | dict | rr | cumulative stats |
| `slots:lock:{user}` | float (timestamp) | slots | next daily reset |
| `slots:stats:{user}` | dict | slots | cumulative stats |
| `trivia:lock:{user}` | float (timestamp) | trivia | next daily trivia |
| `trivia:stats:{user}` | dict | trivia | cumulative stats |
| `mirage:lock:{user}` | float (timestamp) | mirage | next daily mirage |
| `mirage:stats:{user}` | dict | mirage | cumulative stats |
| `fish:cooldown:{user}` | float (timestamp) | fish | last cast time |
| `fish:items:{user}` | dict | fish | items inventory |
| `fish:dailybait_lock:{user}` | float (timestamp) | fish | next dailybait claim |

---

## v1 → v2 migration status

| Script | v2 status | Data migration |
|--------|-----------|----------------|
| hi | ✅ done | no data |
| 8ball | ✅ done | no data |
| flip | ✅ done | no data |
| slap | ✅ done | no data |
| area | ✅ done | no data |
| camp | ✅ done | no data |
| pepe | ✅ done | no data |
| 4/4 | ✅ done | no data |
| simple | ✅ done | no data |
| urban | ✅ done | no data |
| weather | ✅ done | no data |
| bank | 🔲 pending | `{user}.pickle`, `{user}Claim.pickle` |
| rr | 🔲 pending | `{user}RRChamber.pickle`, stats pickles |
| slots | 🔲 pending | `{user}SlotsDailyLock.pickle`, stats pickles |
| trivia | 🔲 pending | `{user}DailyLock.pickle`, stats pickles |
| fish | 🔲 pending | `fish_catalogue.pickle`, items pickles |
| mirage | 🔲 pending | `mirage_stats.pickle`, lock pickles |
| lurk | 🔲 pending | `lurk.db` already SQLite — minimal migration |
| logs | 🔲 pending | `logs.db` already SQLite — minimal migration |
| translate | 🔲 pending | rate limit state JSON |
| twitter | 🔲 pending | depends on translate + openrouter |
| openrouter | 🔲 pending | module only |
| ratelimit | 🔲 pending | superseded by `sb.data` + `sb.channel` |
