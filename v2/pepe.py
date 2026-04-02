# shigebot: v2
"""
!pepe — random pepe emote. Also importable as a module.

Seasonal sets:
  October   — FeelsPumpkinMan added
  December  — FeelsSnowyMan, FeelsSnowMan added

Module exports::

    import pepe
    current_set = pepe.get_set()
    october_set = pepe.get_set(month=10)
"""
import random
from datetime import datetime, timezone

import shigebot as sb

_BASE = ["FeelsAmazingMan", "FeelsGoodMan", "FeelsBadMan", "FeelsBirthdayMan"]

_SEASONAL: dict[int, list[str]] = {
    10: ["FeelsPumpkinMan"],
    12: ["FeelsSnowyMan", "FeelsSnowMan"],
}


def get_set(month: int | None = None) -> list[str]:
    """Return the full pepe set for the given UTC month (default: now)."""
    if month is None:
        month = datetime.now(timezone.utc).month
    return _SEASONAL.get(month, []) + _BASE


def main():
    sb.say(random.choice(get_set()))
