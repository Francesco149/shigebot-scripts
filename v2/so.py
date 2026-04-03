# shigebot: v2
"""
!so [username] — give a shoutout to a user.

Without an argument, shouts out the last raider (stored by the raid trigger
script). With an argument, shouts out the specified username.

Sends a Twitch shoutout via the API (requires moderator:manage:shoutouts)
and posts a chat message with a channel link.

Config::

    [scripts]
    so = "..."

    [triggers]
    "channel.raid" = ["raid"]   # so reads raids:last written by raid.py
"""
import shigebot as sb


def main():
    target = (sb.ctx.args[0].lstrip("@") if sb.ctx.args
               else sb.channel.get("raids:last", ""))

    if not target:
        sb.reply("No recent raid on record. Usage: !so <username>")
        return

    sb.shoutout(target)
    sb.say(f"Go show some love to @{target}! twitch.tv/{target} CHEER")
