# shigebot: v2
"""
!echo [text] — repeat given text.
this is exclusively for operators to test sanitiziation

only for operators
"""
import shigebot as sb

def main():
  if sb.ctx.is_operator:
    sb.say(" ".join(sb.ctx.args))
  else:
    sb.reply("buddy you are not an operator, scram")