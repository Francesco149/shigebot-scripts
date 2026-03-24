#
# Helper to rate limit scripts.
# - Weekly limit per username.
# - Global limit per hour.
# - Fixed weekly reset day (UTC).
# - Same state_file = shared rate limits.
# - Should not have race condition issues with concurrent calls.
#
# Installation: Add to scripts, but don't enable it directly on channels, import it.
#
# Example usage:
#
# rl = RateLimit(
#     state_file="rate_limit_state.json",
#     global_limit_per_hour=50,
#     user_limit_per_week=100,
#     weekly_reset_day=3,  # Thursday
#     message_template="🚫 Chill. Reset in {time}"
# )
#
# allowed, msg = rl.allow("alice")
#
# if not allowed:
#     print(msg)
# else:
#     print("Request allowed")
#

import json
import os
import time
import fcntl
from datetime import datetime, timedelta, timezone
import logging


class RateLimit:
    def __init__(
        self,
        state_file="rate_limit_state.json",
        global_limit_per_hour=50,
        user_limit_per_week=100,
        # 0=Monday ... 6=Sunday (default: Thursday boundary from Wed->Thu)
        weekly_reset_day=3,
        weekly_reset_hour=0,
        message_template="Slow down! Next reset in {time}"
    )
    self.state_file = state_file
    self.global_limit = global_limit_per_hour
    self.user_limit = user_limit_per_week
    self.weekly_reset_day = weekly_reset_day
    self.weekly_reset_hour = weekly_reset_hour
    self.message_template = message_template
    self.logger = logging.getLogger(f"RateLimit/{self.state_file}")

    if not os.path.exists(self.state_file):
        self._write_state({
            "global": {"count": 0, "reset_at": 0},
            "users": {}
        })

    def _info(self, username: str, text: str):
        self.logger.info(f"[{username}] {text}")

    # -------------------------
    # Public API
    # -------------------------
    def allow(self, username: str):
        with open(self.state_file, "r+") as f:
            self._lock(f)

            state = self._read_state(f)
            now = self._now()

            # Handle global reset
            if now >= state["global"]["reset_at"]:
                state["global"]["count"] = 0
                state["global"]["reset_at"] = self._next_hour_reset()

            # Handle user reset
            user = state["users"].setdefault(username, {
                "count": 0,
                "reset_at": self._next_weekly_reset()
            })

            if now >= user["reset_at"]:
                user["count"] = 0
                user["reset_at"] = self._next_weekly_reset()
                self._info(username, "First call of the week")

            # Check limits
            if state["global"]["count"] >= self.global_limit:
                msg = self._format_message(state["global"]["reset_at"] - now)
                self._write_state(state, f)
                self._info(username, "Global limit hit")
                return False, msg

            if user["count"] >= self.user_limit:
                msg = self._format_message(user["reset_at"] - now)
                self._write_state(state, f)
                self._info(username, "User limit hit")
                return False, msg

            # Increment
            state["global"]["count"] += 1
            user["count"] += 1

            self._write_state(state, f)
            return True, None

    def time_until_global_reset(self):
        state = self._read_state_file()
        return self._format_message(state["global"]["reset_at"] - self._now())

    def time_until_user_reset(self, username):
        state = self._read_state_file()
        user = state["users"].get(username)
        if not user:
            return "No usage yet."
        return self._format_message(user["reset_at"] - self._now())

    # -------------------------
    # Internal helpers
    # -------------------------
    def _now(self):
        return int(time.time())

    def _next_hour_reset(self):
        now = datetime.now(timezone.utc)
        next_hour = (now.replace(minute=0, second=0, microsecond=0)
                     + timedelta(hours=1))
        return int(next_hour.timestamp())

    def _next_weekly_reset(self):
        now = datetime.now(timezone.utc)
        days_ahead = (self.weekly_reset_day - now.weekday()) % 7

        reset = now.replace(hour=self.weekly_reset_hour,
                            minute=0, second=0, microsecond=0)

        if days_ahead == 0 and now >= reset:
            days_ahead = 7

        reset = reset + timedelta(days=days_ahead)
        return int(reset.timestamp())

    def _format_message(self, seconds):
        seconds = max(0, int(seconds))

        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, _ = divmod(seconds, 60)

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        if not parts:
            parts.append("less than a minute")

        return self.message_template.format(time=", ".join(parts))

    def _lock(self, file):
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)

    def _read_state(self, file):
        file.seek(0)
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {"global": {"count": 0, "reset_at": 0}, "users": {}}

    def _read_state_file(self):
        with open(self.state_file, "r") as f:
            return json.load(f)

    def _write_state(self, state, file=None):
        if file is None:
            with open(self.state_file, "w") as f:
                json.dump(state, f)
            return

        file.seek(0)
        file.truncate()
        json.dump(state, file)
        file.flush()
        os.fsync(file.fileno())
