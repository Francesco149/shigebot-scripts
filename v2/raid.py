# shigebot: v2
"""
trigger: channel.raid — fires when the channel receives an incoming raid.

Stores the raider's login name in the shared channel store so !so can use it.
Sends a thank-you message to chat.

Config::

    [triggers]
    "channel.raid" = ["raid"]
"""
import shigebot as sb


def main():
    from_user   = sb.ctx.event_data.get("from_user", "")
    display     = sb.ctx.event_data.get("from_user_display", from_user)
    viewers     = sb.ctx.event_data.get("viewer_count", 0)

    if not from_user:
        return

    # Store for !so
    sb.channel.set("raids:last", from_user)

    if viewers >= 100:
        emote = "WICKED"
    elif viewers >= 20:
        emote = "POGGERS"
    else:
        emote = "AYAYA"

    sb.say(
        f"{emote} {display} is raiding with {viewers} viewer{'s' if viewers != 1 else ''}! "
        f"Welcome raiders! {emote}"
    )
