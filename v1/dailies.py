# originally made by https://twitch.tv/HK_BLAU

import sys
import os
import pickle
import re
from datetime import datetime

user = os.environ['NICK']
t = datetime.utcnow()


def check_daily(path):
    try:
        with open(path, "rb") as f:
            prev = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True

    if first == True or t > prev:
        return False
    else:
        return True


def check_better_daily(path):
    try:
        with open(path, "rb") as f:
            users = pickle.load(f)
        if user in users:
            prev = users[user]
            first = False
        else:
            users[user] = next
            first = True
    except BaseException:
        with open(path, "wb") as f:
            users = {user: next}
            pickle.dump(users, f)
        first = True

    if first or t > prev:
        return False
    else:
        return True


def dailies(user=user):
    output = ''
    if check_daily(f"{user}Claim.pickle"):
        output += "Weekly claim: ✔️, "
    else:
        output += "Weekly claim: ❌, "

    if check_daily(f"{user}DailyLock.pickle"):
        output += "Trivia: ✔️, "
    else:
        output += "Trivia: ❌, "

    if check_daily(f"{user}_dailybait_lock.pickle"):
        output += "Dailybait: ✔️, "
    else:
        output += "Dailybait: ❌, "

    if check_daily(f"{user}SlotsDailyLock.pickle"):
        output += "Slots: ✔️, "
    else:
        output += "Slots: ❌, "

    if check_better_daily('mirage_lock.pickle'):
        output += "Mirage: ✔️, "
    else:
        output += "Mirage: ❌, "

    if check_daily(f"{user}RRDailyLock.pickle"):
        try:
            with open(f"{user}RRChamberPosition.pickle", "rb") as f:
                pos = pickle.load(f)
        except BaseException:
            pos = 0
        if pos == 0:
            output += "Roulette: 6 chambers left CLEZ"
        elif pos == 1:
            output += "Roulette: 5 chambers left Susgi"
        elif pos == 2:
            output += "Roulette: 4 chambers left DOPIUM"
        elif pos == 3:
            output += "Roulette: 3 chambers left GIGADEAD"
        elif pos == 4:
            output += "Roulette: 2 chambers left NOW"
        elif pos > 5:
            output += "Roulette: dejj"
    else:
        output += "Roulette: 6 chambers left CLEZ"

    print(output)


for i in range(len(sys.argv)):
    if i < 4:
        sys.argv[i] = sys.argv[i].lower()

if len(sys.argv) > 1:
    dailies(sys.argv[1])
else:
    dailies()
