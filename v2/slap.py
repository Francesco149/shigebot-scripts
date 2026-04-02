# shigebot: v2
"""
!slap [target] — slap someone with a large trout.

Usage:
  !slap           — slap yourself
  !slap <target>  — slap target
"""
import shigebot as sb

def main():
    target = sb.ctx.args[0] if sb.ctx.args else "themselves"
    sb.say(f"{sb.ctx.user} slaps {target} around a bit with a large trout")
