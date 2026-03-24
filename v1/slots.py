# originally made by https://twitch.tv/Painketsu

import random
import pickle
import os
import sys
import math
import re
import time
import numpy as np
from scipy.ndimage import label
from datetime import datetime
from datetime import timedelta
opts = ["shinobuWOW", "guraBlush", "AYAYA"]
optsAnim = ["POGGIES", "kitaFuwaFuwa", "Fukkireta"]
optsDaily = ["WOO", "catDisco", "KleeRave"]
optsBonus1 = ["BonusX1", "BonusX1", "BonusX1"]
optsBonus2 = ["BonusX2", "BonusX2", "BonusX2"]
optsBonus5 = ["BonusX5"]
optsDebug = ["FRICK", "forsenPuke"]
aya = ["AYAYARRR", "AYAYAsip", "AYAYAWeird"]
spEmot = ["SheCrazy", "kleeRAGEY"]
spEmot2 = ["heCrazy", "kleeRAGEY"]
spGoog = ["SheCrazy", "heCrazy"]
exEmot = ["HYPERDANSU", "deadlole"]

user = os.environ['NICK']
# user = "painketsu"  ## change into this for local
bet = 100
bonus = 1
BonusBonus = 0
reset = False  # globals cause cba WOOOO


if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg.isdigit() and int(arg) > 100:
        bet = arg


def checkBalance(u):
    try:
        with open(f"{u}.pickle", "rb") as f:
            balance = pickle.load(f)
    except BaseException:
        balance = 0
    return (balance)


def map_elements_to_012(lst):
    array = np.array(lst).reshape(4, 4)
    unique_elements = np.unique(array)
    mapping = {element: i for i, element in enumerate(unique_elements)}
    mapped_array = np.vectorize(mapping.get)(array)
    return mapped_array


def find_probs(array):
    probs = {(0, 0, 0): 2.3, (5, 0, 0): 5.0, (6, 0, 0): 7.6,
             (7, 0, 0): 12.1, (8, 0, 0): 20.4, (9, 0, 0): 37.7,
             (6, 5, 0): 62.4, (5, 5, 0): 62.5, (10, 0, 0): 80.3,
             (7, 5, 0): 139.4, (11, 0, 0): 207.2, (6, 6, 0): 278.0,
             (8, 5, 0): 360.2, (7, 6, 0): 366.6, (12, 0, 0): 707.8,
             (9, 5, 0): 1196, (8, 6, 0): 1214, (7, 7, 0): 2404,
             (13, 0, 0): 3617, (8, 7, 0): 5630, (9, 6, 0): 5889,
             (10, 5, 0): 6250, (5, 5, 5): 11519, (6, 5, 5): 22022,
             (14, 0, 0): 31857, (10, 6, 0): 52994, (9, 7, 0): 54142,
             (11, 5, 0): 63452, (8, 8, 0): 100200, (15, 0, 0): 478469,
             (16, 0, 0): 14348907}

    # array = np.random.choice([0, 1, 2], size=(4, 4))
    array = map_elements_to_012(array)
    structure = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]

    # Find and store sizes of connected regions for each value (0, 1, 2)
    region_sizes = []
    for value in range(3):
        labeled_array, num_features = label(
            array == value, structure=structure)
        for i in range(1, num_features + 1):
            region_size = (labeled_array == i).sum()
            if region_size >= 5:
                region_sizes.append(region_size)

    # Sort the region sizes in descending order
    region_sizes.sort(reverse=True)

    # Fill in the tuple with up to three largest regions, padding with zeros
    # if necessary
    while len(region_sizes) < 3:
        region_sizes.append(0)
    region_sizes_tuple = tuple(region_sizes)
    return [probs[region_sizes_tuple], region_sizes_tuple]


def log_points(gains=0):
    for i in [user, 'camp']:
        try:
            with open(f"{i}_slots_stats.pickle", "rb") as f:
                stats = pickle.load(f)
        except BaseException:
            stats = {'spent': 0, 'gains': 0}
        stats['spent'] += int(bet)
        stats['gains'] += gains
        with open(f"{i}_slots_stats.pickle", "wb") as f:
            pickle.dump(stats, f)


def calcPoints(p):
    p = p**(1 / 1.5)
    points = round(int(bet) * p / 2.75 * bonus)
    bb = random.randint(0, 24)
    if bb == 22:
        # if bb >=0:
        bouns = bonusSpin()
        if bouns == 0:
            bouns = 1
        points = points * bouns

        log_points(int(points))
        bankedPoints = checkBalance(user)
        bankedPoints += int(points)
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(bankedPoints, f)

        houseBalance = checkBalance("house")
        houseBalance -= int(points)
        with open(f"house.pickle", "wb") as f:
            pickle.dump(houseBalance, f)

        if bouns > 0:
            if bouns == 1:
                print(f"You hit a {bouns}x bonus ErmDog")
            elif bouns == 2:
                print(f"YAAAY You hit a {bouns}x bonus YAAAY")
            elif bouns == 3:
                print(f"YAAY You hit a {bouns}x bonus YAAY")
            elif bouns == 4:
                print(f"WOOOOO You hit a {bouns}x bonus WOOOOO")
            elif bouns > 4:
                print(f"WakuWakuHyper You hit a {bouns}x bonus WakuWakuHyper")

        print(f"You won {points} campbucks! (+{points - int(bet)}) DANKIES")
    else:
        log_points(int(points))
        bankedPoints = checkBalance(user)
        bankedPoints += int(points)
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(bankedPoints, f)

        houseBalance = checkBalance("house")
        houseBalance -= int(points)
        with open(f"house.pickle", "wb") as f:
            pickle.dump(houseBalance, f)

        print(f"You won {points} campbucks! (+{points - int(bet)}) DANKIES")


def calcPointsDaily(p):
    p = p**(1 / 1.5)
    points = round(int(bet) * p / 2.75 * bonus)

    bb = random.randint(0, 22)
    # if bb > 0:
    if bb == 22:
        bouns = bonusSpin()
        if bouns == 0:
            bouns = 1
        points = points * bouns
        # print("bouns" + bouns)

        log_points(int(points))
        bankedPoints = checkBalance(user)
        bankedPoints += int(points)
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(bankedPoints, f)

        houseBalance = checkBalance("house")
        houseBalance -= int(points)
        with open(f"house.pickle", "wb") as f:
            pickle.dump(houseBalance, f)

        if bouns == 1:
            print(
                f"{bouns}x bonus Classic You won {points} campbucks and can go agane! rainbowPls")
        elif bouns == 2:
            print(
                f"{bouns}x bonus! YAAY You won {points} campbucks and can go agane! rainbowPls")
        elif bouns == 3:
            print(
                f"{bouns}x bonus!! YAAY You won {points} campbucks and can go agane! rainbowPls")
        elif bouns == 4:
            print(
                f"{bouns}x bonus!!! WOOOOO You won {points} campbucks and can go agane! rainbowPls")
        elif bouns > 4:
            print(
                f"WakuWakuHyper You hit a {bouns}x bonus WakuWakuHyper You won {points} campbucks and can go agane! WOOOOO")

    else:
        log_points(int(points))
        bankedPoints = checkBalance(user)
        bankedPoints += int(points)
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(bankedPoints, f)

        houseBalance = checkBalance("house")
        houseBalance -= int(points)
        with open(f"house.pickle", "wb") as f:
            pickle.dump(houseBalance, f)

        print(f"You won {points} campbucks and can go agane! rainbowPls")

    global reset
    reset = True


def payBet():
    bankedPoints = checkBalance(user)
    bankedPoints -= int(bet)
    with open(f"{user}.pickle", "wb") as f:
        pickle.dump(bankedPoints, f)
    # to 'ouse
    houseBalance = checkBalance("house")
    houseBalance += int(bet)
    with open(f"house.pickle", "wb") as f:
        pickle.dump(houseBalance, f)


def daily():
    t = datetime.utcnow()
    next = t + timedelta(days=1)
    next = t.replace(year=next.year, month=next.month,
                     day=next.day, hour=0, minute=0, second=0, microsecond=0)

    try:
        with open(f"{user}SlotsDailyLock.pickle", "rb") as f:
            prev = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True

    if first == True or t > prev:
        global bet, reset
        bet = 209
        playDaily()
        if reset:
            with open(f"{user}SlotsDailyLock.pickle", "wb") as f:
                pickle.dump(prev, f)
        else:
            with open(f"{user}SlotsDailyLock.pickle", "wb") as f:
                pickle.dump(next, f)
    else:
        nn = prev - t
        print(
            f"Daily slots already played Bites Next daily available in {str(nn)[:-7]} hrs Waitingg")


def dailyTest():
    global bet
    bet = 250
    play()


def getRand(n):
    p = []
    o = opts + optsAnim
    for i in range(n):
        p.append(o[random.randint(0, len(o) - 1)])
        # p.append(optsDebug[random.randint(0,len(optsDebug)-1)])
    return p


def getRanDaily(n):
    p = []
    o = optsDaily
    for i in range(n):
        p.append(o[random.randint(0, len(o) - 1)])
    return p


def getRanBonus(n):
    p = []
    o = optsBonus1 + optsBonus2 + optsBonus5
    for i in range(n):
        p.append(o[random.randint(0, len(o) - 1)])
    return p


def getSp(n):
    s = spEmot if random.randint(0, 1) == 0 else spEmot2
    p = []
    for i in range(n):
        p.append(s[random.randint(0, len(s) - 1)])
    return p


def getAya(n):
    p = []
    for i in range(n):
        p.append(aya[random.randint(0, len(aya) - 1)])
    return p


def extraGame():
    go = True
    e = []
    print("Dansu EXTRA GAME! Dansu")
    while go:
        e.append(exEmot[random.randint(0, len(exEmot) - 1)])
        print(*e, sep=' ')
        if exEmot[1] in e:
            go = False


def checkLines(pos):
    lines = 0
    linesIn = []
    emotLines = []
    global bonus

    li = [
        [pos[0], pos[1], pos[2]],
        [pos[3], pos[4], pos[5]],
        [pos[6], pos[7], pos[8]],
        [pos[0], pos[3], pos[6]],
        [pos[1], pos[4], pos[7]],
        [pos[2], pos[5], pos[8]],
        [pos[0], pos[4], pos[8]],
        [pos[2], pos[4], pos[6]]]

    for i, l in enumerate(li):
        if (all(e == l[0] for e in l)):
            lines += 1
            linesIn.append(i)

    if lines > 0:
        for n in linesIn:
            emotLines.append(li[n][0])

        if (all(emot == emotLines[0] for emot in emotLines)):
            if emotLines[0] in optsAnim:
                bonus += 0.5

    return [lines, bonus]


def checkLinesDaily(pos):
    lines = 0
    linesIn = []
    emotLines = []

    li = [
        [pos[0], pos[1], pos[2], pos[3]],
        [pos[4], pos[5], pos[6], pos[7]],
        [pos[8], pos[9], pos[10], pos[11]],
        [pos[12], pos[13], pos[14], pos[15]],
        [pos[0], pos[5], pos[10], pos[15]],
        [pos[3], pos[6], pos[9], pos[12]],
        [pos[0], pos[4], pos[8], pos[12]],
        [pos[1], pos[5], pos[9], pos[13]],
        [pos[2], pos[6], pos[10], pos[14]],
        [pos[3], pos[7], pos[11], pos[15]]]

    for i, l in enumerate(li):
        if (all(e == l[0] for e in l)):
            lines += 1
            linesIn.append(i)

    if lines > 0:
        for n in linesIn:
            emotLines.append(li[n][0])

    return lines


def checkSpLines(pos):
    lines = 0

    if (pos[0] in spGoog and pos[1] in spGoog and pos[2] in spGoog):
        lines += 1
    if (pos[3] in spGoog and pos[4] in spGoog and pos[5] in spGoog):
        lines += 1
    if (pos[6] in spGoog and pos[7] in spGoog and pos[8] in spGoog):
        lines += 1
    if (pos[6] in spGoog and pos[4] in spGoog and pos[2] in spGoog):
        lines += 1
    if (pos[0] in spGoog and pos[4] in spGoog and pos[8] in spGoog):
        lines += 1
    if (pos[0] in spGoog and pos[3] in spGoog and pos[6] in spGoog):
        lines += 1
    if (pos[1] in spGoog and pos[4] in spGoog and pos[7] in spGoog):
        lines += 1
    if (pos[2] in spGoog and pos[5] in spGoog and pos[8] in spGoog):
        lines += 1
    return lines


def checkSpLinesDaily(pos):
    lines = 0

    if (pos[0] in spGoog and pos[1] in spGoog and pos[2]
            in spGoog and pos[3] in spGoog):
        lines += 1
    if (pos[4] in spGoog and pos[5] in spGoog and pos[6]
            in spGoog and pos[7] in spGoog):
        lines += 1
    if (pos[8] in spGoog and pos[9] in spGoog and pos[10]
            in spGoog and pos[11] in spGoog):
        lines += 1
    if (pos[12] in spGoog and pos[13] in spGoog and pos[14]
            in spGoog and pos[15] in spGoog):
        lines += 1
    if (pos[0] in spGoog and pos[5] in spGoog and pos[10]
            in spGoog and pos[15] in spGoog):  # \
        lines += 1
    if (pos[3] in spGoog and pos[6] in spGoog and pos[9]
            in spGoog and pos[12] in spGoog):  # /
        lines += 1
    if (pos[0] in spGoog and pos[4] in spGoog and pos[8]
            in spGoog and pos[12] in spGoog):  # |1
        lines += 1
    if (pos[1] in spGoog and pos[5] in spGoog and pos[9]
            in spGoog and pos[13] in spGoog):  # |2
        lines += 1
    if (pos[2] in spGoog and pos[6] in spGoog and pos[10]
            in spGoog and pos[14] in spGoog):  # |3
        lines += 1
    if (pos[3] in spGoog and pos[7] in spGoog and pos[11]
            in spGoog and pos[15] in spGoog):  # |4
        lines += 1
    return lines


def line(n):
    r = random.randint(0, 4)
    emot = ["YAAY", "YAAAY", "Drake", "miyanoHype", "moky"]
    if (n == 1):
        print(emot[r] + " LINE! (1/6)")
        calcPoints(6)
    elif (n == 2):
        print("PogRikka DOUBLE LINE! (1/73)")
        calcPoints(73)
    elif (n == 3):
        print("SheCrazy TRIPLE LINE! (1/792)")
        calcPoints(792)
    elif (n == 4):
        print("WakuWakuHyper FOUR LINES! (1/6460)")
        calcPoints(6460)
    elif (n == 5):
        print("WakuWakuHyper FIVE LINES! (1/25840)")
        calcPoints(25840)
    elif (n == 6):
        print("WakuWakuHyper SIX LINES! (1/83981)")
        calcPoints(83981)
    elif (n == 8):
        print("/me WakuWakuHyper WakuWakuHyper FULLSCREEN! WakuWakuHyper WakuWakuHyper　(1/1679616)")
        calcPoints(1679616)


def ayaLine(n):
    r = random.randint(0, 1)
    emot = ["SoCute", "YouMu"]
    if (n == 1):
        print(emot[r] + " AYALINE! (1/126)")
        calcPoints(126)
    elif (n == 2):
        print("SoCute DOUBLE AYALINE! SoCute (1/350)")
        calcPoints(350)
    elif (n == 3):
        print("SheCrazy TRIPLE AYALINE! (1/1745)")
        calcPoints(1745)
    elif (n == 4):
        print("WakuWakuHyper FOUR AYALINES! (1/7450)")
        calcPoints(7450)
    elif (n == 5):
        print("WakuWakuHyper FIVE AYALINES! (1/23400)")
        calcPoints(23400)
    elif (n == 6):
        print("WakuWakuHyper SIX AYALINES! (1/41000)")
        calcPoints(41000)
    elif (n == 8):
        print("/me WakuWakuHyper WakuWakuHyper FULLAYASCREEN! WakuWakuHyper WakuWakuHyper (1/328050)")
        calcPoints(328050)


def spLine(n):
    if (n == 1):
        print("PogRikka SPECIAL LINE! (1/172)")
        calcPoints(172)
    elif (n == 2):
        print("AAAA DOUBLE SPECIAL LINE! AAAA (1/376)")
        calcPoints(376)
    elif (n == 3):
        print("WakuWakuHyper TRIPLE SPECIAL LINE! WakuWakuHyper (1/853)")
        calcPoints(853)
    elif (n == 4):
        print("WakuWakuHyper FOUR SPECIAL LINES! WakuWakuHyper (1/2133)")
        calcPoints(2133)
    elif (n == 5):
        print("WakuWakuHyper FIVE SPECIAL LINES! WakuWakuHyper (1/5120)")
        calcPoints(5120)
    elif (n == 6):
        print("WakuWakuHyper SIX SPECIAL LINES! WakuWakuHyper (1/6400)")
        calcPoints(6400)
    elif (n == 8):
        print("/me WakuWakuHyper WakuWakuHyper SPECIAL FULLSCREEN! WakuWakuHyper WakuWakuHyper (1/25600)")
        calcPoints(25600)


def chainDaily(n):
    r = random.randint(0, 4)
    prob = n[0]
    emot = ["YAAY", "YAAAY", "Drake", "miyanoHype", "moky"]
    if (n[1] == (5, 0, 0)):
        print(f"{emot[r]} 5x CHAIN! (1/5)")
        calcPointsDaily(prob)
    elif (n[1] == (6, 0, 0)):
        print(f"PogRikka 6x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (7, 0, 0)):
        print(f"PogRikka 7x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (8, 0, 0)):
        print(f"WOOOOO 8x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (9, 0, 0)):
        print(f"WOOOOO 9x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (6, 5, 0)):
        print(f"WOOOOO 6x + 5x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (5, 5, 0)):
        print(f"WOOOOO DOUBLE 5x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (10, 0, 0)):
        print(f"NoFuckingWay 10x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (7, 5, 0)):
        print(f"NoFuckingWay 7x + 5x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (11, 0, 0)):
        print(f"SheCrazy 11x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (6, 6, 0)):
        print(f"SheCrazy DOUBLE 6x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (8, 5, 0)):
        print(f"SheCrazy 8x + 5x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (7, 6, 0)):
        print(f"SheCrazy 7x + 6x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (12, 0, 0)):
        print(f"WakuWakuHyper 12x CHAIN! (1/{round(prob)})")
        calcPointsDaily(prob)
    elif (n[1] == (9, 5, 0)):
        print(f"WakuWakuHyper 9x + 5x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (8, 6, 0)):
        print(f"WakuWakuHyper 8x + 6x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (7, 7, 0)):
        print(f"WakuWakuHyper DOUBLE 7x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (13, 0, 0)):
        print(f"WakuWakuHyper 13x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (8, 7, 0)):
        print(f"WakuWakuHyper 8x + 7x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (9, 6, 0)):
        print(f"WakuWakuHyper 9x + 6x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (10, 5, 0)):
        print(f"WakuWakuHyper 10x + 5x CHAIN! (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (5, 5, 5)):
        print(f"WakuWakuHyper TRIPLE 5x CHAIN! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (6, 5, 5)):
        print(f"WakuWakuHyper 6x + DOUBLE 5x CHAIN! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (14, 0, 0)):
        print(f"WakuWakuHyper 14x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (10, 6, 0)):
        print(f"WakuWakuHyper 10x + 6x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (9, 7, 0)):
        print(f"WakuWakuHyper 9x + 7x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (11, 5, 0)):
        print(f"WakuWakuHyper 11x + 5x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (8, 8, 0)):
        print(f"WakuWakuHyper DOUBLE 8x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (15, 0, 0)):
        print(f"/me WakuWakuHyper 15x CHAIN?! WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)
    elif (n[1] == (15, 0, 0)):
        print(
            f"/me WakuWakuHyper WakuWakuHyper FULLSCREEN!!! WakuWakuHyper WakuWakuHyper (1/{prob})")
        calcPointsDaily(prob)


def spLineDaily(n):
    if (n == 1):
        # return "a"
        print("PogRikka SPECIAL LINE! (1/180)")
        calcPointsDaily(100 / 0.555)
    elif (n == 2):
        # return "b"
        print("AAAA DOUBLE SPECIAL LINE! AAAA (1/508)")
        calcPointsDaily(508)
    elif (n == 3):
        # return "c"
        print("WakuWakuHyper TRIPLE SPECIAL LINE! WakuWakuHyper (1/1604)")
        calcPointsDaily(1604)
    elif (n == 4):
        # return "d"
        print("WakuWakuHyper FOUR SPECIAL LINES! WakuWakuHyper (1/5063)")
        calcPointsDaily(5063)
    elif (n == 5):
        # return 'e'
        print("WakuWakuHyper FIVE SPECIAL LINES! WakuWakuHyper (1/17921)")
        calcPointsDaily(17921)
    elif (n == 6):
        # return 'f'
        print("WakuWakuHyper SIX SPECIAL LINES! WakuWakuHyper (1/52632)")
        calcPointsDaily(52632)
    elif (n == 7):
        # return 'g'
        print("WakuWakuHyper SEVEN SPECIAL LINES! WakuWakuHyper (1/188679)")
        calcPointsDaily(188679)
    elif (n == 8):
        # return 'h'
        print("WakuWakuHyper EIGHT SPECIAL LINES! WakuWakuHyper (1/454545)")
        calcPointsDaily(454545)
    elif (n == 10):
        # return 'j'
        print("/me WakuWakuHyper WakuWakuHyper SPECIAL FULLSCREEN! WakuWakuHyper WakuWakuHyper (1/10500000)")
        calcPointsDaily(10500000)


def print_logs(u=user):
    try:
        with open(f"{u}_slots_stats.pickle", "rb") as f:
            stats = pickle.load(f)
        print(
            f"Stats for {u}: {stats['spent']}lts spent | {stats['gains']}lts gained | {round(stats['gains'] / stats['spent'], 5)} return ratio")
    except BaseException:
        print(f"Maybe try playing slots first. MyHonestReaction")


def bonusSpin():
    pos = getRanBonus(16)
    print(f"{pos[0]} {pos[1]} {pos[2]} {pos[3]}")
    print(f"{pos[4]} {pos[5]} {pos[6]} {pos[7]}")
    print(f"{pos[8]} {pos[9]} {pos[10]} {pos[11]}")
    print(f"{pos[12]} {pos[13]} {pos[14]} {pos[15]}")
    lines = checkLinesBonus(pos)
    return lines[1]


def checkLinesBonus(pos):
    lines = 0
    linesIn = []
    emotLines = []

    li = [
        [pos[0], pos[1], pos[2], pos[3]],
        [pos[4], pos[5], pos[6], pos[7]],
        [pos[8], pos[9], pos[10], pos[11]],
        [pos[12], pos[13], pos[14], pos[15]],
        [pos[0], pos[5], pos[10], pos[15]],
        [pos[3], pos[6], pos[9], pos[12]],
        [pos[0], pos[4], pos[8], pos[12]],
        [pos[1], pos[5], pos[9], pos[13]],
        [pos[2], pos[6], pos[10], pos[14]],
        [pos[3], pos[7], pos[11], pos[15]]]

    for i, l in enumerate(li):
        if (all(e == l[0] for e in l)):
            lines += 1
            linesIn.append(i)

    if lines > 0:
        for n in linesIn:
            emotLines.append(li[n][0])

        c = 0
        global BonusBonus
        for emot in emotLines:
            if emotLines[c] in optsBonus1:
                BonusBonus += 1
            elif emotLines[c] in optsBonus2:
                BonusBonus += 2
            elif emotLines[c] in optsBonus5:
                BonusBonus += 5
            c += 1
    return [lines, BonusBonus]


def play():
    sp = random.randint(0, 49)
    if sp == 22:
        pos = getSp(9)
        print(pos[0] + " " + pos[1] + " " + pos[2])
        print(pos[3] + " " + pos[4] + " " + pos[5])
        print(pos[6] + " " + pos[7] + " " + pos[8])
        lines = checkSpLines(pos)
        if lines > 0:
            spLine(lines)
        else:
            log_points()
    elif sp == 44:
        pos = getAya(9)
        print(pos[0] + " " + pos[1] + " " + pos[2])
        print(pos[3] + " " + pos[4] + " " + pos[5])
        print(pos[6] + " " + pos[7] + " " + pos[8])
        lines = checkLines(pos)
        bonus = lines[1]
        if lines[0] > 0:
            ayaLine(lines[0])
        else:
            log_points()
    else:
        pos = getRand(9)
        print(pos[0] + " " + pos[1] + " " + pos[2])
        print(pos[3] + " " + pos[4] + " " + pos[5])
        print(pos[6] + " " + pos[7] + " " + pos[8])
        lines = checkLines(pos)
        bonus = lines[1]
        if lines[0] > 0:
            line(lines[0])
        else:
            log_points()


def playDaily():
    sp = random.randint(0, 49)
    if sp == 22:
        pos = getSp(16)
        print(f"{pos[0]} {pos[1]} {pos[2]} {pos[3]}")
        print(f"{pos[4]} {pos[5]} {pos[6]} {pos[7]}")
        print(f"{pos[8]} {pos[9]} {pos[10]} {pos[11]}")
        print(f"{pos[12]} {pos[13]} {pos[14]} {pos[15]}")
        lines = checkSpLinesDaily(pos)
        if lines > 0:
            spLineDaily(lines)
        else:
            log_points()
    else:
        pos = getRanDaily(16)
        print(f"{pos[0]} {pos[1]} {pos[2]} {pos[3]}")
        print(f"{pos[4]} {pos[5]} {pos[6]} {pos[7]}")
        print(f"{pos[8]} {pos[9]} {pos[10]} {pos[11]}")
        print(f"{pos[12]} {pos[13]} {pos[14]} {pos[15]}")
        erm = find_probs(pos)
        if erm[1] != (0, 0, 0):
            chainDaily(erm)
        else:
            log_points()


bankedPoints = checkBalance(user)
halt = False
betted = False
if len(sys.argv) > 1:
    arg1 = sys.argv[1].lower()
    if arg1 == 'daily':
        halt = True
        daily()
    elif arg1 == 'reset' and user == "painketsu":
        halt = True
        arg2 = sys.argv[2].lower()

        t = datetime.utcnow()
        res = t - timedelta(days=1)
        res = t.replace(month=res.month, day=res.day, hour=0,
                        minute=0, second=0, microsecond=0)

        with open(f"{arg2}SlotsDailyLock.pickle", "wb") as f:
            pickle.dump(res, f)
        print(f"{arg2}'s daily has been reset, dont get used to it neuroTsun")
        # print("There's nothing to test bozo ryoApprove")

        # with open(f"{user}.pickle", "wb") as f:
        #    pickle.dump(100000, f)

        # dailyTest()
        # sim
        # types = []
        # c = 0
        # n = 10000000
        # while c < n:
        # types.append(dailyTest())
        # c += 1
        # print(f"1: {types.count('1')} 2: {types.count('2')} 3: {types.count('3')} 4: {types.count('4')} 5: {types.count('5')} 6: {types.count('6')} 7: {types.count('7')} 8: {types.count('8')} 10: {types.count('10')}")
        # print(f"s1: {types.count('a')} s2: {types.count('b')} s3: {types.count('c')} s4: {types.count('d')} s5: {types.count('e')} s6: {types.count('f')} s7: {types.count('g')} s8: {types.count('h')} s10: {types.count('j')}")

    elif arg1 in ['stats', 'logs']:
        halt = True
        if len(sys.argv) >= 3:
            arg2 = sys.argv[2].lower()
            if arg2 in ['help', 'elp']:
                print(f"Slot stats usage:")
                print(f"!slots stats/logs (user)/me/camp")
                print(
                    f"(user) is any username, 'me' gives stats for you and 'camp' gives the collective stats for camp.")
            elif arg2 == 'me':
                print_logs(user)
            else:
                print_logs(arg2)
        else:
            print(f"Slot stats usage:")
            print(f"!slots stats/logs (user)/me/camp")
            print(
                f"(user) is any username, 'me' gives stats for you and 'camp' gives the collective stats for camp.")


if bankedPoints < int(bet) and not halt:
    print(f"You have {bankedPoints} campbucks you broke ass mf Disgust")
elif not halt:
    if len(sys.argv) > 1:
        arg1 = sys.argv[1].lower()
        if arg1 in ['all', 'allin']:
            if bankedPoints > 0:
                bet = bankedPoints
                betted = True
        if not betted and sys.argv[1].isdigit() and int(sys.argv[1]) > 100:
            bet = sys.argv[1]

    try:
        with open(f"{user}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
    payBet()
    play()
