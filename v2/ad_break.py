# shigebot: v2
"""
trigger: channel.ad_break — fires when an ad break begins.

Sends an announcement with the break duration.

Config::

    [triggers]
    "channel.ad_break" = ["ad_break"]

    # Ad break events require the bot to have channel:read:ads scope.
    # Run shigebot-auth to regenerate tokens after adding this scope.
"""
import math
import shigebot as sb


def main():
    duration_secs = sb.ctx.event_data.get("duration", 0)
    duration_mins = math.ceil(duration_secs / 60)

    sb.announce(
        f"We're taking a quick ad break. RIP to whatever I was saying. "
        f"See you in {duration_mins} min{'s' if duration_mins != 1 else ''}! Ok"
    )
