# shigebot: v2
"""
!flip — coin flip. 1/101 chance of landing on the side.
"""
import random
import shigebot as sb

def main():
    roll = random.randint(0, 100)
    if roll < 50:
        sb.say("Heads HOT")
    elif roll > 50:
        sb.say("Tails THAT")
    else:
        sb.say("uh Landed on the side..")
