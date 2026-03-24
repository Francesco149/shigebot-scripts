# originally made by https://twitch.tv/Painketsu

import sys
import requests
import time
import random
import html
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


def cDif(d):
    if "easy" in d.lower():
        return "easy"
    elif "medium" in d.lower():
        return "medium"
    elif "hard" in d.lower():
        return "hard"
    else:
        return None


def cCat(d):
    if "anime" in d.lower():
        return 31
    elif "games" in d.lower():
        return 15
    elif "music" in d.lower():
        return 12
    elif "animals" in d.lower():
        return 27
    elif "comp" in d.lower() or "computers" in d.lower() or "compsci" in d.lower():
        return 18
    elif "math" in d.lower():
        return 19
    elif "history" in d.lower():
        return 23
    elif "geography" in d.lower() or "geo" in d.lower():
        return 22
    elif "mythology" in d.lower():
        return 20
    elif "general" in d.lower():
        return 9
    elif "science" in d.lower() or "sci" in d.lower():
        return 17
    else:
        return None


def cook(a):
    res = requests.get(a)
    jd = res.json() if res and res.status_code == 200 else None

    if jd is not None:
        for i in jd:
            type = jd['results'][0]['type']
            question = html.unescape(jd['results'][0]['question'])
            cAnswer = html.unescape(jd['results'][0]['correct_answer'])
            Answers = jd['results'][0]['incorrect_answers']

        if type == "boolean":
            print(question)
            print("True/False")
        else:
            Answers.append(cAnswer)
            random.shuffle(Answers)
            i = 1
            aa = ""
            for x in Answers:
                aa += str(i) + ". \"" + html.unescape(x) + "\" | "
                i = i + 1
            print(question)
            print(aa)
        time.sleep(12)
        print("Answer: " + cAnswer)
    else:
        print("API error NOOOO")


def dailyCook(a):
    with open(f"{user}DailyAnswered.pickle", "wb") as f:
        pickle.dump("no", f)

    with open(f"{user}DailyTimer.pickle", "wb") as f:
        pickle.dump(datetime.utcnow() + timedelta(seconds=17), f)

    res = requests.get(a)
    jd = res.json() if res and res.status_code == 200 else None

    if jd is not None:
        for i in jd:
            type = jd['results'][0]['type']
            question = html.unescape(jd['results'][0]['question'])
            cAnswer = html.unescape(jd['results'][0]['correct_answer'])
            Answers = jd['results'][0]['incorrect_answers']

        with open(f"{user}DailyCorrectAnswer.pickle", "wb") as f:
            pickle.dump(cAnswer, f)

        if type == "boolean":
            print(question)
            print("True/False")
        else:
            Answers.append(cAnswer)
            random.shuffle(Answers)
            i = 1
            aa = ""
            for x in Answers:
                aa += str(i) + ". \"" + html.unescape(x) + "\" | "
                with open(f"{user}DailyAnswer{i}.pickle", "wb") as f:
                    pickle.dump(x, f)
                i = i + 1
            print(question)
            print(aa)
            # time.sleep(12)
            # print("Answer: " + cAnswer)
    else:
        print("API error NOOOO")


def fixStats(u, o, t):
    # print("Statsfix use: !trivia statsfix [user] [add/remove] [multi/bool]")
    try:
        with open(f"{u}_trivia_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = {'maxStreak': 0, 'totalPlayed': 0, 'totalBoolWins': 0, 'totalChoiceWins': 0,
                 'totalBoolLs': 0, 'totalChoiceLs': 0, 'maxStreakUser': 'None'}

    go = False

    if t == "add" or t == "remove":
        go = True
    else:
        print("invalid operation - opts: add|remove")

    if o == "multi" or o == "bool" or o == "streak":
        go = True
    else:
        print("invalid type - opts: multi|bool")
        go = False

    if o == "streak":
        try:
            with open(f"{u}DailyStreak.pickle", "rb") as f:
                streak = pickle.load(f)
        except BaseException:
            streak = 0
        if t == "add":
            streak += 1
            print(f"Added 1 to streak, now: {streak}")
        else:
            streak = 0
            print(f"Streak reset, now: {streak}")

        with open(f"{u}DailyStreak.pickle", "wb") as f:
            pickle.dump(streak, f)
        go = False

    if go:
        if t == "add":
            if o == "bool":
                stats['totalBoolWins'] += 1
                stats['totalBoolLs'] -= 1
            else:
                stats['totalChoiceWins'] += 1
                stats['totalChoiceLs'] -= 1
        else:
            if o == "bool":
                stats['totalBoolWins'] -= 1
                stats['totalBoolLs'] += 1
            else:
                stats['totalChoiceWins'] -= 1
                stats['totalChoiceLs'] += 1
        with open(f"{u}_trivia_stats.pickle", "wb") as f:
            pickle.dump(stats, f)
        print(f"Succesfully performed: {o} {t} for {u} kk")


def statTrack(u, streak, isBool, correct):
    try:
        with open(f"{u}_trivia_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = {'maxStreak': 0, 'totalPlayed': 0, 'totalBoolWins': 0, 'totalChoiceWins': 0,
                 'totalBoolLs': 0, 'totalChoiceLs': 0, 'maxStreakUser': 'None'}

    stats['totalPlayed'] += 1
    if correct and isBool:
        stats['totalBoolWins'] += 1
    elif correct and not isBool:
        stats['totalChoiceWins'] += 1
    elif not correct and isBool:
        stats['totalBoolLs'] += 1
    elif not correct and not isBool:
        stats['totalChoiceLs'] += 1

    if streak > stats['maxStreak']:
        stats['maxStreak'] = streak
        stats['maxStreakUser'] = user

    with open(f"{u}_trivia_stats.pickle", "wb") as f:
        pickle.dump(stats, f)


def checkStats(u):
    try:
        with open(f"{u}_trivia_stats.pickle", "rb") as f:
            stats = pickle.load(f)
    except BaseException:
        stats = "nai"
        print(f"{u.capitalize()}'s gotta play first bozo Eating ")

    if stats != "nai":
        print(f"Trivia stats for {u.capitalize()} Nerdge ")
        if stats['totalBoolWins'] != 0 or stats['totalBoolLs'] != 0:
            boolPercent = round(
                (stats['totalBoolWins'] / (stats['totalBoolWins'] + stats['totalBoolLs'])) * 100, 2)
        else:
            boolPercent = 100
        if stats['totalChoiceWins'] != 0 or stats['totalChoiceLs'] != 0:
            choicePercent = round(
                (stats['totalChoiceWins'] / (stats['totalChoiceWins'] + stats['totalChoiceLs'])) * 100, 2)
        else:
            choicePercent = 100
        if u == 'camp':
            print(
                f"Total dalies: {
                    stats['totalPlayed']} | Total multichoice wins: {
                    stats['totalChoiceWins']} ({choicePercent}%) | Total T/F wins: {
                    stats['totalBoolWins']} ({boolPercent}%) | Highest streak: {
                    stats['maxStreak']} by {
                        stats['maxStreakUser'].capitalize()}")
        else:
            print(
                f"Total dalies: {
                    stats['totalPlayed']} | Total multichoice wins: {
                    stats['totalChoiceWins']} ({choicePercent}%) | Total T/F wins: {
                    stats['totalBoolWins']} ({boolPercent}%) | Highest streak: {
                    stats['maxStreak']}")


def daily(a):
    t = datetime.utcnow()
    next = t + timedelta(days=1)
    next = t.replace(year=next.year, month=next.month,
                     day=next.day, hour=0, minute=0, second=0, microsecond=0)

    try:
        with open(f"{user}DailyLock.pickle", "rb") as f:
            prev = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True

    # next = t + timedelta(days=1, hours=(22 - t.hour), minutes=(59 - t.minute), seconds=(59 - t.second))
    # nextDaily = lastT + timedelta(days=1)
    # print(next)
    if first == True or t > prev:
        dailyCook(a)
        with open(f"{user}DailyLock.pickle", "wb") as f:
            pickle.dump(next, f)
    else:
        nn = prev - t
        print(
            f"Daily trivia already played Loser Next daily available in {str(nn)[:-7]} hrs agreege")


def answer(a):
    try:
        with open(f"{user}DailyAnswered.pickle", "rb") as f:
            answered = pickle.load(f)
    except BaseException:
        answered = "no"

    if answered == "no":
        t = datetime.utcnow()

        try:
            with open(f"{user}DailyTimer.pickle", "rb") as f:
                lastT = pickle.load(f)
        except BaseException:
            lastT = t
        try:
            with open(f"{user}DailyCorrectAnswer.pickle", "rb") as f:
                cAnswer = pickle.load(f)
        except BaseException:
            noAnswer = True

        isBool = True if cAnswer == "True" or cAnswer == "False" else False
        if lastT > t:
            noAnswer = False
            correct = False

            if "t" in a.lower() and "f" not in a.lower():
                if cAnswer == "True":
                    correct = True
            elif "f" in a.lower() and "t" not in a.lower():
                if cAnswer == "False":
                    correct = True
            else:
                try:
                    with open(f"{user}DailyAnswer{a}.pickle", "rb") as f:
                        uAnswer = pickle.load(f)
                except BaseException:
                    noAnswer = True
                if noAnswer == False:
                    if cAnswer == uAnswer:
                        correct = True
            if correct == True:
                try:
                    with open(f"{user}DailyStreak.pickle", "rb") as f:
                        streak = pickle.load(f)
                except BaseException:
                    streak = 0

                streak += 1
                streakPay = 100 * streak
                balance = getBalance(user) + streakPay
                statTrack(user, streak, isBool, correct)
                statTrack('camp', streak, isBool, correct)
                with open(f"{user}DailyStreak.pickle", "wb") as f:
                    pickle.dump(streak, f)
                with open(f"{user}DailyLock.pickle", "wb") as f:
                    pickle.dump(datetime.utcnow() - timedelta(days=1), f)
                print(
                    f"Correct! YES You earn {streakPay} campbucks and get to go agane! CHEER")
                with open(f"{user}.pickle", "wb") as f:
                    pickle.dump(balance, f)
            else:
                print(
                    f"Incorrect! NOP Correct answer was: {cAnswer}, try again tomorrow ApuCross")
                statTrack(user, 0, isBool, correct)
                statTrack('camp', 0, isBool, correct)
                with open(f"{user}DailyStreak.pickle", "wb") as f:
                    pickle.dump(0, f)
            with open(f"{user}DailyAnswered.pickle", "wb") as f:
                pickle.dump("yes", f)
        else:
            print(f"Question timed out HELP Correct Answer was: {cAnswer}")
            statTrack(user, 0, isBool, False)
            statTrack('camp', 0, isBool, False)
            with open(f"{user}DailyStreak.pickle", "wb") as f:
                pickle.dump(0, f)
            with open(f"{user}DailyAnswered.pickle", "wb") as f:
                pickle.dump("yes", f)
    else:
        print("Maybe start the daily first? xdd")


n = len(sys.argv)
if n == 1:
    api = f"https://opentdb.com/api.php?amount=1"
else:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2].lower() if n > 2 else None
    arg3 = sys.argv[3].lower() if n > 3 else None
    arg4 = sys.argv[4].lower() if n > 4 else None

    if arg1 == "help":
        print(
            "HELP for daily: !trivia [daily] to start it; !trivia a [1/2/3/4]|[true/t/false/f] to answer. You have 13 seconds!")
        print(
            "For regular trivia: !trivia [category] [easy/medium/hard] (nothing = random)")
        print("Categories: anime, games, music, animals, computers/comp, math, history, geography/geo, science/sci, mythology, general")
        go = False
    elif arg1 == "stats":
        u = user if arg2 is None or arg2 == "me" else arg2
        checkStats(u)
        go = False
    elif arg1 == "fixstats" or arg1 == "statsfix":
        u = user if arg2 is None or arg2 == "me" else arg2
        if user == "painketsu":
            if arg3 is not None and arg4 is not None:
                t = arg3
                o = arg4
                fixStats(u, o, t)
            else:
                print(
                    "statsfix use: !trivia statsfix [user] [add/remove] [multi/bool/streak]")
        else:
            print("Dick too smol Loser")

        go = False
    elif arg1 == "a" and arg2 is not None:
        answer(arg2)
        go = False
    elif arg1 == "devreset" and user == "painketsu":
        with open(f"{arg2.lower()}DailyLock.pickle", "wb") as f:
            pickle.dump(datetime.utcnow() - timedelta(days=1), f)
        print("Daily reset for debuging! forsenPuke")
        go = False
    elif arg1 == "daily" or arg1 == "Daily":
        api = f"https://opentdb.com/api.php?amount=1"
        daily(api)
        go = False
    elif arg2 is None:
        cat = cCat(arg1)
        dif = cDif(arg1)
        if dif is None and cat is None:
            api = f"https://opentdb.com/api.php?amount=1"
        else:
            if dif is not None:
                api = f"https://opentdb.com/api.php?amount=1&difficulty={dif}"
            else:
                api = f"https://opentdb.com/api.php?amount=1&category={cat}"
    else:
        cat = cCat(arg1)
        dif = cDif(arg2)
        if dif is None and cat is None:
            api = f"https://opentdb.com/api.php?amount=1"
        elif dif is None or cat is None:
            if dif is not None:
                api = f"https://opentdb.com/api.php?amount=1&difficulty={dif}"
            elif cat is not None:
                api = f"https://opentdb.com/api.php?amount=1&category={cat}"
        else:
            api = f"https://opentdb.com/api.php?amount=1&category={cat}&difficulty={dif}"
if go is True:
    cook(api)
