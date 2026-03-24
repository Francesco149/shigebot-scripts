# originally made by https://twitch.tv/Painketsu

import re
import pickle
import sys
import os
from datetime import datetime
from datetime import timedelta

user = os.environ['NICK']


def getBalance(u):
    try:
        with open(f"{u}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
    return bankedPoints


def checkBalance(u):
    print(f"💰 {u.capitalize()} has {getBalance(u)} campbucks💰")


def transfer(amount, u):
    # sender
    if user is not u:
        balance = getBalance(user)
        if balance >= amount:
            balance -= amount
            with open(f"{user}.pickle", "wb") as f:
                pickle.dump(balance, f)
            # receiver
            b = getBalance(u)
            b += amount
            with open(f"{u}.pickle", "wb") as f:
                pickle.dump(b, f)
            print(
                f"Corpa {user.capitalize()} transfered {amount} to {u.capitalize()} and now has {balance} Corpa")
    else:
        print("How u gonna send urself money mf.. MyHonestReaction")


def addBalance(amount, u):
    if user == "painketsu":
        balance = getBalance(u)
        balance += int(amount)

        with open(f"{u}.pickle", "wb") as f:
            pickle.dump(balance, f)

        print("Added " + str(amount) + " to " +
              u + ". New total: " + str(balance))
    else:
        print("Ur dick too smol to do this.")


def removeBalance(amount, u):
    if user == "painketsu":
        balance = getBalance(u)
        balance -= int(amount)

        with open(f"{u}.pickle", "wb") as f:
            pickle.dump(balance, f)

        print("Removed " + str(amount) + " from " +
              u + ". New total: " + str(balance))
    else:
        print("Ur dick too smol to do this.")


def claim():
    t = datetime.utcnow()
    try:
        with open(f"{user}Claim.pickle", "rb") as f:
            prev = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True
    if (t.weekday() == 6):
        next = t + timedelta(days=1)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 5):
        next = t + timedelta(days=2)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 4):
        next = t + timedelta(days=3)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 3):
        next = t + timedelta(days=4)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 2):
        next = t + timedelta(days=5)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 1):
        next = t + timedelta(days=6)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)
    elif (t.weekday() == 0):
        next = t + timedelta(days=7)
        next = t.replace(year=next.year, month=next.month,
                         day=next.day, hour=0, minute=0, second=0, microsecond=0)

        # next = t + timedelta(days=7, hours=(22 - t.hour), minutes=(59 - t.minute), seconds=(59 - t.second))
        # next=t.replace(day=t.day+1, hour=0, minute=0, second=0, microsecond=0)
    # else:
        # next = t + timedelta(days=(7 - (t.weekday() + 1)), hours=(22 - t.hour), minutes=(59 - t.minute), seconds=(59 - t.second))
        # next=t.replace(days=t.weekday()+7-(t.weekday()+1), hour=0, minute=0, second=0, microsecond=0)
    nn = next - t
    #

    if first == True or t > prev:
        with open(f"{user}Claim.pickle", "wb") as f:
            pickle.dump(next, f)
        balance = getBalance(user)
        balance += 1000
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(balance, f)
        print(
            f"{
                user.capitalize()} claimed 1000 points and now has {balance} campbucks! Drake Next claim available in {
                str(nn)} hours UMU")
    else:
        print(
            f"Weekly gib already claimed NOPERS Next claim available in {str(nn)} hours kk")


if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg == "transfer" and len(sys.argv) > 3:
        if sys.argv[2].isdigit():
            transfer(int(sys.argv[2]), sys.argv[3].lower())
        else:
            print("Nice amount dumbass Awkward")
    elif arg == "add" and len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            addBalance(int(sys.argv[2]), sys.argv[3].lower())
        else:
            print("Nice amount dumbass Awkward")
    elif arg == "rem" and len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            removeBalance(int(sys.argv[2]), sys.argv[3].lower())
        else:
            print("Nice amount dumbass Awkward")
    elif arg == "help":
        print("Args: !bank [user] or [transfer |user| |amount|]")
    elif arg == "claim":
        claim()
    elif arg == "toint":
        a = sys.argv[2].lower()
        bal = int(getBalance(a))
        print(bal)
        with open(f"{a}.pickle", "wb") as f:
            pickle.dump(bal, f)
        print("Fixd, now don't fuck it up again king agreege")
    else:
        checkBalance(arg)

else:
    checkBalance(user)
