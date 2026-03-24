# originally made by https://twitch.tv/Painketsu

import sys
import time
import random
import os
import pickle
import re
from datetime import datetime
from datetime import timedelta

go = True
user = os.environ['NICK']


def getBalance(u):
    try:
        with open(f"{u}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
    return bankedPoints


def statTrack(u, shot, pay, pos):
    try:
        with open(f"{u}_rr_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = {'totalPlayed': 0, 'timesDead': 0, 'totalEarned': 0,
                 'topEarned': 0, 'topEarnedUser': 'None'}

    if '1st' not in stats:
        # List is [successes, fails] for each trigger pull
        stats['1st'] = [0, 0]
        stats['2nd'] = [0, 0]
        stats['3rd'] = [0, 0]
        stats['4th'] = [0, 0]
        stats['5th'] = [0, 0]

    positions = ['1st', '2nd', '3rd', '4th', '5th']
    key = positions[pos]

    if not shot:
        stats[key][0] += 1
    else:
        stats[key][1] += 1

    totalEarned = stats['totalEarned'] + pay
    stats['totalEarned'] = totalEarned

    stats['totalPlayed'] += 1
    if shot:
        stats['timesDead'] += 1
    else:
        if totalEarned > stats['topEarned']:
            stats['topEarned'] = totalEarned
            stats['topEarnedUser'] = u

    with open(f"{u}_rr_stats.pickle", "wb") as f:
        pickle.dump(stats, f)


def checkStats(u):
    try:
        with open(f"{u}_rr_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = "nai"
        print(f"{u.capitalize()}'s gotta play first mf UglyWhiteCatStaring")

    if stats != "nai":
        print(f"Roulette stats for {u.capitalize()} Nerdge")
        if u == 'camp':
            print(
                f"Trigger pulls: {
                    stats['totalPlayed']} | Times shot: {
                    stats['timesDead']} | Total payout: {
                    stats['totalEarned']} | Profit record: {
                    stats['topEarned']} by {
                        stats['topEarnedUser'].capitalize()}")
        else:
            print(
                f"Trigger pulls: {stats['totalPlayed']} | Times shot: {stats['timesDead']} | Total payout: {stats['totalEarned']} | Profit record: {stats['topEarned']}")


def check_stats_detailed(u):
    try:
        with open(f"{u}_rr_stats.pickle", "rb") as f:
            stats = pickle.load(f)
        if '1st' not in stats:
            # List is [successes, fails] for each trigger pull
            stats['1st'] = [0, 0]
            stats['2nd'] = [0, 0]
            stats['3rd'] = [0, 0]
            stats['4th'] = [0, 0]
            stats['5th'] = [0, 0]
            with open(f"{u}_rr_stats.pickle", "wb") as f:
                pickle.dump(stats, f)
    except BaseException:
        stats = "nai"
        print(f"{u.capitalize()}'s gotta play first mf UglyWhiteCatStaring")
        return None

    def calculate_percentage(values):
        total = sum(values)
        return round(values[0] * 100 / total, 3) if total != 0 else 0

    success_rates = []
    for key, values in stats.items():
        if key in ['1st', '2nd', '3rd', '4th', '5th']:
            percentage = calculate_percentage(values)
            success_rates.append(f"{key}: {percentage}%")

    print("Trigger pull success rates Donki " + " | ".join(success_rates))


def statsfix(u):
    try:
        with open(f"{u}_rr_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = {'totalPlayed': 0, 'timesDead': 0, 'totalEarned': 0,
                 'topEarned': 0, 'topEarnedUser': 'None'}

    stats = {'totalPlayed': 0, 'timesDead': 0, 'totalEarned': 0,
             'topEarned': 0, 'topEarnedUser': 'None'}

    with open(f"{u}_rr_stats.pickle", "wb") as f:
        pickle.dump(stats, f)

    with open(f"{u}RRDailyLock.pickle", "wb") as f:
        pickle.dump(datetime.utcnow() - timedelta(days=1), f)

    print(f"Stats fixed and reset for {u} WOO")


def checkDayChanged():
    t = datetime.utcnow()
    next = t + timedelta(days=1)
    next = t.replace(year=next.year, month=next.month,
                     day=next.day, hour=0, minute=0, second=0, microsecond=0)

    try:
        with open(f"{user}RRDailyLock.pickle", "rb") as f:
            prev = pickle.load(f)
        with open(f"{user}RRChamberPosition.pickle", "rb") as f:
            pos = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True

    if first == True or t > prev:
        with open(f"{user}RRDailyLock.pickle", "wb") as f:
            pickle.dump(next, f)
        reload()
        fire(0)
    else:
        if pos >= 5:
            nn = prev - t
            print(
                f"Dead people can't play WeirdCat Wait {str(nn)[:-7]} hrs to respawn SkillIssue")
        else:
            fire(pos)


def reload():
    chamber = [1, 0, 0, 0, 0, 0]
    random.shuffle(chamber)
    with open(f"{user}RRChamber.pickle", "wb") as f:
        pickle.dump(chamber, f)
    with open(f"{user}RRChamberPosition.pickle", "wb") as f:
        pickle.dump(0, f)
    with open(f"{user}RRwonToday.pickle", "wb") as f:
        pickle.dump(0, f)


def fire(pos):
    try:
        with open(f"{user}RRChamber.pickle", "rb") as f:
            chamber = pickle.load(f)
        with open(f"{user}RRwonToday.pickle", "rb") as f:
            wonToday = pickle.load(f)
    except BaseException:
        wonToday = 0

    if pos == 0 or pos == 1:
        points = 100
    else:
        points = int((wonToday + 100) / (6 - (pos) - 1))

    if chamber[pos] == 1:
        points = wonToday + 100
        print("/me *BANG* deadfr spilledBlood")
        balance = getBalance(user) - points
        jamalBalance = getBalance('jamal') + points
        print(
            f"YOUDIED Deadge {points}lts were taken from your corpse kek Yoink")
        statTrack(user, True, -points, pos)
        statTrack('camp', True, -points, pos)
        with open(f"{user}RRChamberPosition.pickle", "wb") as f:
            pickle.dump(pos + 6, f)
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(balance, f)
        with open(f"jamal.pickle", "wb") as f:
            pickle.dump(jamalBalance, f)
    else:
        if pos < 4:
            if pos == 0:
                print(f"/me *click* Saved ⚪⚫⚫⚫⚫⚫ (+{int(points)}lts)")
            elif pos == 1:
                print(f"/me *click* Saved ⚪⚪⚫⚫⚫⚫ (+{int(points)}lts)")
            elif pos == 2:
                print(f"/me *click* Saved ⚪⚪⚪⚫⚫⚫ (+{int(points)}lts)")
            elif pos == 3:
                print(f"/me *click* Saved ⚪⚪⚪⚪⚫⚫ (+{int(points)}lts)")
            # print(f"You won {int(points)} campbucks and get to live another day WICKED ...or to try your luck again if you dare SMUGGERS")
            with open(f"{user}RRChamberPosition.pickle", "wb") as f:
                pickle.dump(pos + 1, f)
            with open(f"{user}RRwonToday.pickle", "wb") as f:
                pickle.dump(wonToday + points, f)
            statTrack(user, False, points, pos)
            statTrack('camp', False, points, pos)
            balance = getBalance(user) + points
            jamalBalance = getBalance('jamal') - points
            with open(f"{user}.pickle", "wb") as f:
                pickle.dump(balance, f)
            with open(f"jamal.pickle", "wb") as f:
                pickle.dump(jamalBalance, f)
        elif pos == 4:
            print(f"/me *click* Saved ⚪⚪⚪⚪⚪⚫")
            print(
                f"You survived the entire chamber NOWAYING You win another {int(points)} campbucks and the gun is reloaded! CHEER")
            statTrack(user, False, points, pos)
            statTrack('camp', False, points, pos)
            balance = getBalance(user) + points
            with open(f"{user}.pickle", "wb") as f:
                pickle.dump(balance, f)
            reload()


def checkChamber():
    try:
        with open(f"{user}RRChamberPosition.pickle", "rb") as f:
            pos = pickle.load(f)
    except BaseException:
        pos = 0

    if pos == 0:
        print(f"⚫⚫⚫⚫⚫⚫")
    elif pos == 1:
        print(f"⚪⚫⚫⚫⚫⚫")
    elif pos == 2:
        print(f"⚪⚪⚫⚫⚫⚫")
    elif pos == 3:
        print(f"⚪⚪⚪⚫⚫⚫")
    elif pos == 4:
        print(f"⚪⚪⚪⚪⚫⚫")
    elif pos == 5:
        print(f"⚪⚪⚪⚪⚪⚫")
    elif pos == 6:
        print(f"💀⚫⚫⚫⚫⚫")
    elif pos == 7:
        print(f"⚪💀⚫⚫⚫⚫")
    elif pos == 8:
        print(f"⚪⚪💀⚫⚫⚫")
    elif pos == 9:
        print(f"⚪⚪⚪💀⚫⚫")
    elif pos == 10:
        print(f"⚪⚪⚪⚪💀⚫")


n = len(sys.argv)
if n == 1:
    go = True
else:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2].lower() if n > 2 else None
    arg3 = sys.argv[3].lower() if n > 3 else None
    arg4 = sys.argv[4].lower() if n > 4 else None

    if arg1 == "help" or arg1 == "elp":
        print("Args for rr: help | check | stats [user]")
        go = False
    elif arg1 == "check":
        checkChamber()
        go = False
    elif arg1 == "stats":
        if arg2 is None or arg2 == "me":
            checkStats(user)
        else:
            checkStats(arg2)
        go = False
    elif arg1 == 'details':
        if arg2 is None or arg2 == "me":
            check_stats_detailed(user)
        else:
            check_stats_detailed(arg2)
        go = False
    elif arg1 == "statsfix" and user == "painketsu":
        if arg2 is None or arg2 == "me":
            statsfix(user)
        else:
            statsfix(arg2)
        go = False
    else:
        go = True

if go:
    checkDayChanged()
