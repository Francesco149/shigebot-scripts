# shigebot: v2
"""
!4/4 — simulate guessing N/N pepes.

Repetition is allowed as the outcomes would only be 2 and 4 otherwise.

Requires: pepe (module, listed in [scripts])

Example output:
    !pepe FeelsBirthdayMan
    FeelsBirthdayMan
    !pepe FeelsBadMan
    FeelsAmazingMan
    !pepe FeelsAmazingMan
    FeelsAmazingMan
    !pepe FeelsBadMan
    FeelsAmazingMan
    2/4
"""
import shigebot as sb
import pepe
import random


_emotes = {
  0: "WhenLifeGetsAtYou",
  1: "FeelsBadMan",
  2: "FeelsWeirdMan",
  3: "NOOOOvanish",
  4: "NOWAYING",
}


def main():
    current_set = pepe.get_set()
    bets  = [random.choice(current_set) for _ in current_set]
    pulls = [random.choice(current_set) for _ in current_set]
    hits  = sum(b == p for b, p in zip(bets, pulls))

    for bet, pull in zip(bets, pulls):
        sb.say(f"{sb.ctx.prefix}pepe {bet}")
        sb.say(pull)

    sb.reply(f"{hits}/{len(current_set)} {_emotes[hits]}")
