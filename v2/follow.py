# shigebot: v2
"""
trigger: channel.follow — fires when someone follows the channel.

Sends a welcome message to chat.

Config::

    [triggers]
    "channel.follow" = ["follow"]

    # Follow events require the bot to have moderator:read:followers scope.
    # Run shigebot-auth to regenerate tokens after adding this scope.
"""
import shigebot as sb


def main():
    display = sb.ctx.event_data.get("from_user_display",
              sb.ctx.event_data.get("from_user", ""))

    if not display:
        return

    sb.say(f"@{display} just followed! Welcome to the headpats factory! AYAYA")
