# shigebot: v2
"""
!hi — ping command. Replies with "hi :)" and a random float.
"""
import random
import shigebot as sb

def main():
    sb.say(f"hi :) [{random.uniform(0, 100):.2f}]")
