import random
from datetime import datetime, timezone

EVENT_SETS = {
    10: ["FeelsPumpkinMan"],
    12: ["FeelsSnowyMan", "FeelsSnowMan"],
}


def get_set(month=datetime.now(timezone.utc).month):
    return EVENT_SETS.get(month, []) + [
        "FeelsAmazingMan",
        "FeelsGoodMan",
        "FeelsBadMan",
        "FeelsBirthdayMan"
    ]


if __name__ == "__main__":
    print(random.choice(get_set()))
