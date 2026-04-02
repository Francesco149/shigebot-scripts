# shigebot: v2
"""
ambient: simple — hardcoded text command dispatcher.

Called for every message (list with #simple). Matches messages that *start
with* a trigger string (case-insensitive). Edit _CMDS to customise.
"""
import shigebot as sb

# Populated after sb is initialised (inside main) so sb.ctx.prefix is available.
# If your triggers are all static strings, you can also hardcode them here.

def _cmds():
    p = sb.ctx.prefix
    return {
        f"{p}area": "https://i.imgur.com/sxdISDi.jpeg",
        f"{p}camp": "people are always here because the camp never dies",
    }


def main():
    if not sb.ctx.args:
        return
    msg = " ".join(sb.ctx.args).lower()
    for trigger, response in _cmds().items():
        if msg.startswith(trigger.lower()):
            sb.say(response)
            return
