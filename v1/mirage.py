# originally made by https://twitch.tv/HK_BLAU

import numpy as np
import pickle
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import time
import re

user = os.environ['NICK']


def getBalance(user=user):
    try:
        with open(f"{user}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(0, f)
    return bankedPoints


def chess_notation(coords):
    columns = "abcd"
    row, column = coords
    chess_row = 4 - row
    chess_notation = f"{columns[column]}{chess_row}"
    return chess_notation


def generate_grid(n=4):
    board = np.zeros((n, n))
    answer = tuple(np.random.randint(0, n, size=2))
    board[answer] = 1
    return board, chess_notation(answer)


def freebie_seed(arr):
    def is_corner(i, j):
        return (i, j) in [(0, 0), (0, 3), (3, 0), (3, 3)]

    def is_edge(i, j):
        return (i in [0, 3] or j in [0, 3]) and not is_corner(i, j)

    def count_zeros_adjacent(i, j):
        adjacent_positions = [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]
        return sum(1 for x, y in adjacent_positions if 0 <=
                   x < 4 and 0 <= y < 4 and arr[x, y] == 0)

    def count_zeros_diagonal(i, j):
        adjacent_positions = [
            (i - 1, j - 1), (i - 1, j + 1), (i + 1, j - 1), (i + 1, j + 1)]
        return sum(1 for x, y in adjacent_positions if 0 <=
                   x < 4 and 0 <= y < 4 and arr[x, y] == 0)

    for i in range(4):
        for j in range(4):
            zeros_adjacent = count_zeros_adjacent(i, j)
            zeros_diagonal = count_zeros_diagonal(i, j)
            if is_corner(i, j):
                if (arr[i, j] == 4 or
                    (arr[i, j] >= 2 and zeros_adjacent >= 1) or
                        (arr[i, j] == 1 and zeros_adjacent >= 2)):
                    return True
                if ((arr[i, j] >= 2 and zeros_diagonal >= 1) or
                        (arr[i, j] >= 1 and zeros_adjacent >= 1 and zeros_diagonal >= 1)):
                    return True
            elif is_edge(i, j):
                if ((arr[i, j] >= 3 and zeros_adjacent >= 1) or
                    (arr[i, j] >= 2 and zeros_adjacent >= 2) or
                        (arr[i, j] >= 1 and zeros_adjacent >= 3)):
                    return True
                if ((arr[i, j] >= 3 and zeros_diagonal >= 1) or
                    (arr[i, j] >= 1 and zeros_adjacent >= 1 and zeros_diagonal >= 1) or
                        (arr[i, j] >= 1 and zeros_diagonal >= 2)):
                    return True
            else:
                if ((arr[i, j] == 4 and zeros_adjacent >= 1) or
                    (arr[i, j] == 3 and zeros_adjacent >= 2) or
                    (arr[i, j] == 2 and zeros_adjacent >= 3) or
                        (arr[i, j] == 1 and zeros_adjacent >= 4)):
                    return True
    return False


def add_nodes(board, n=4, nodes=5):
    all_indices = np.array(np.meshgrid(range(n), range(n))).T.reshape(-1, 2)
    original_board = board.copy()
    rows = np.random.choice(all_indices.shape[0], size=nodes, replace=False)
    indices = all_indices[rows]
    for k in range(nodes):
        i, j = tuple(indices[k, :])
        board[i, j] += 1
        if i > 0:
            board[i - 1, j] += 1
        if i < n - 1:
            board[i + 1, j] += 1
        if j > 0:
            board[i, j - 1] += 1
        if j < n - 1:
            board[i, j + 1] += 1
    if freebie_seed(board):
        return add_nodes(original_board, n=4, nodes=5)
    return board


def print_mirage_emotes(board):
    mapping = {
        0: 'Mirage0',
        1: 'Mirage1',
        2: 'Mirage2',
        3: 'Mirage3',
        4: 'Mirage4',
        5: 'Mirage5',
        6: 'ppAutismo'
    }
    vfunc = np.vectorize(lambda x: mapping[x])
    board = vfunc(board.astype(int))
    for row in board:
        print(' '.join(row))


def check_daily_status():
    time_now = time.time()
    try:
        with open('mirage_statuses.pickle', "rb") as f:
            users = pickle.load(f)
        if user in users:
            daily_status = users[user]
        else:
            daily_status = (time_now, 0)
            users[user] = daily_status
    except BaseException:
        with open('mirage_statuses.pickle', "wb") as f:
            daily_status = (time_now, 0)
            users = {user: daily_status}
            pickle.dump(users, f)

    return daily_status


def update_daily_status():
    time_now = time.time()
    with open('mirage_statuses.pickle', "rb") as f:
        users = pickle.load(f)
    if user in users:
        status = users[user][1]
        status = (status + 1) % 2
        users[user] = (time_now, status)
    else:
        status = 1
        users[user] = (time_now, status)
    with open('mirage_statuses.pickle', "wb") as f:
        pickle.dump(users, f)
    return (time_now, status)


def start_daily():
    board, answer = generate_grid()
    board = add_nodes(board)
    try:
        with open('mirage_answers.pickle', "rb") as f:
            users = pickle.load(f)
        users[user] = answer
        first = False
    except BaseException:
        first = True

    with open('mirage_answers.pickle', "wb") as f:
        if first:
            users = {user: answer}
        pickle.dump(users, f)

    update_daily_status()
    print_mirage_emotes(board)


def check_answer_time():
    old_time = check_daily_status()[0]
    new_time = time.time()
    answer_time = new_time - old_time
    time_left = max(round(30 - answer_time, 2), 0)
    reward = round(500 + 10 * time_left**1.6 + 30 * time_left)
    if time_left >= 15:
        emotes = ['WICKED', 'MILKMANRAVE', 'WAYTOOSMART']
        print(f"{np.random.choice(emotes)} You found the fish! You had {time_left} seconds left. You are awarded {reward} campbucks!!")
    elif time_left >= 10:
        emotes = ['5Head', 'POGGERS', 'AWOO']
        print(f"{np.random.choice(emotes)} You found the fish! You had {time_left} seconds left. You are awarded {reward} campbucks!")
    elif time_left >= 5:
        emotes = ['monkaMath', 'Blindfold', 'forsen']
        print(f"{np.random.choice(emotes)} You found the fish! You had {time_left} seconds left. You are awarded {reward} campbucks.")
    elif time_left >= 1:
        emotes = ['Saved', 'dentt', 'Dentge', 'ApuDent']
        print(f"{np.random.choice(emotes)} You found the fish! You had {time_left} seconds left. You are awarded {reward} campbucks.")
    elif time_left > 0:
        print(
            f"monkaW You found the fish! You had {time_left} seconds left DOPIUM You are awarded {reward} campbucks...")
    else:
        emotes = ['dumbb', 'forsenLaughingAtYou', 'BocchiArrive']
        print(f"{np.random.choice(emotes)} You were {abs(round(30 - answer_time,
                                                               2))} seconds late and the mirage fish moved on. You receive nothing myIQ")
        stat_track(round(answer_time, 2), 0)
    if time_left > 0:
        balance = getBalance()
        balance += reward
        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(balance, f)
        stat_track(round(answer_time, 2), reward)


def answer_daily(answer):
    answer = answer.lower()
    with open('mirage_answers.pickle', "rb") as f:
        answers = pickle.load(f)
    if answer == answers[user]:
        check_answer_time()
    else:
        emotes = ['NT', 'idiot.', 'forsenLaughingAtYou', 'WHOLETHIMCOOK']
        print(
            f"You missed the fish {np.random.choice(emotes)} The correct location was {answers[user]}")
        stat_track(np.nan, 0)
    update_daily_status()


def check_mirage(answer='a0'):
    daily_status = check_daily_status()
    if daily_status[1] == 1:
        if answer == 'a0':
            print('Erm You have one active already.')
            return None
        return answer_daily(answer)

    t = datetime.utcnow()
    next = t + timedelta(days=1)
    next = t.replace(year=next.year, month=next.month,
                     day=next.day, hour=0, minute=0, second=0, microsecond=0)

    try:
        with open(f"mirage_lock.pickle", "rb") as f:
            users = pickle.load(f)
        if user in users:
            prev = users[user]
            first = False
        else:
            users[user] = next
            first = True
    except BaseException:
        with open('mirage_lock.pickle', "wb") as f:
            users = {user: next}
            pickle.dump(users, f)
        first = True

    if first or t > prev:
        start_daily()
        with open('mirage_lock.pickle', "wb") as f:
            users[user] = next
            pickle.dump(users, f)
    else:
        nn = prev - t
        total_seconds = int(nn.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_string = "{}h{}m{}s".format(hours, minutes, seconds)
        print(
            f"You already tried to catch the mirage fish peepoStop Next availability in {time_string} annystare")


def stat_track(answer_time, reward):
    try:
        with open('mirage_stats.pickle', 'rb') as f:
            stats = pickle.load(f)
    except BaseException:
        stats = pd.DataFrame(columns=["user", "solve time", "reward"])
    row = pd.DataFrame(
        [{"user": user, "solve time": answer_time, "reward": reward}])
    stats = pd.concat([stats, row], ignore_index=True)
    with open('mirage_stats.pickle', 'wb') as f:
        pickle.dump(stats, f)


def print_stats(user=user):
    try:
        stats = pd.read_pickle('mirage_stats.pickle')
    except BaseException:
        print(f"Camp hasn't played yet MyHonestReaction")
        return None
    if user not in ['camp', 'all']:
        stats = stats[stats['user'] == user]
        if len(stats) == 0:
            print(f"{user} hasn't played yet annystare")
            return None
    else:
        user = 'camp'
    success_rate = len(stats[stats['reward'] > 0]) / len(stats)
    illegal_success_rate = len(stats[stats['solve time'] > 0]) / len(stats)
    avg_solve_time = stats[stats['solve time'] < 30]['solve time'].mean()
    illegal_solve_time = stats['solve time'].mean()
    total_attempts = len(stats)
    total_reward = stats['reward'].sum()
    if success_rate < 0.25:
        emotes = ['ApuDent', 'dentt', 'Dentge', 'bAware']
    else:
        emotes = ['annystare', 'catPls', 'CLEZ']
    print(f"Stats for {user} {np.random.choice(emotes)}")
    print(
        f"Success rate: {
            round(
                success_rate * 100,
                2)}% ({
            round(
                illegal_success_rate * 100,
                2)}%) | Average solve time: {
            round(
                avg_solve_time,
                2)}s ({
            round(
                illegal_solve_time,
                2)}s) | Total attempts: {total_attempts} | Total campbucks gained: {total_reward}")
    if user in ['camp', 'all']:
        total_rewards_by_user = stats.groupby(
            'user')['reward'].sum().sort_values(ascending=False)

        if total_rewards_by_user.empty:
            print("No one has played yet... SAD")
        else:
            for i, (user, total_reward) in enumerate(
                    total_rewards_by_user.head(5).items(), start=1):
                print(f"{i}. {user}: {total_reward} campbucks gained")


def encrypt(answer):
    seed = np.random.randint(1, 1000)
    int_answer = int(answer, 16)
    encrypted_answer = int_answer ^ seed
    encrypted_answer = str(encrypted_answer) + '|' + str(seed)
    print(f"Decode: !mirage decode {encrypted_answer}")


def decrypt(encrypted_answer):
    code = int(encrypted_answer.split('|')[0])
    seed = int(encrypted_answer.split('|')[1])
    answer = code ^ seed
    answer = hex(answer)[2:]
    return answer

# Returns True if there is an active challenge


def check_active_challenge():
    try:
        duels = pd.read_pickle('mirage_duels.pickle')
        age = time.time() - duels.loc[duels.index[-1], 'time']
        winner = duels.loc[duels.index[-1], 'winner']
        consent = duels.loc[duels.index[-1], 'consent']
        if winner:
            return False
        if consent and age > 330:
            return False
        if not consent and age > 30:
            return False
        return True
    except BaseException:
        return False


def challenge(opponent, bet):
    if check_active_challenge():
        print(f"peepoStop There is a challenge active already.")
        return None
    if user == opponent:
        print('stfu')
        return None
    balance = getBalance()
    opp_balance = getBalance(opponent)
    duel = {'challenger': [user],
            'opponent': [opponent],
            'consent': 0,
            'winner': [''],
            'bet': [bet],
            'answer': [''],
            'time': [time.time()]
            }
    duel = pd.DataFrame(duel)
    try:
        duels = pd.read_pickle('mirage_duels.pickle')
    except BaseException:
        duels = pd.DataFrame(columns=duel.keys())
    if bet < 100:
        print(f"Bet at least 100lts. We don't have all day thismf")
        return None
    if balance < bet:
        print(
            f"Brokeass mf you don't have enough campbucks for this bet. You can bet at most {balance}lts")
        return None
    if opp_balance < bet:
        print(f"Your opponent can only pay for a bet of {opp_balance}lts Nono")
        return None
    duels = pd.concat([duels, duel], ignore_index=True)
    pd.to_pickle(duels, 'mirage_duels.pickle')
    print(
        f"Challenge sent to {opponent} for {bet}lts! Accept/deny with !mirage (accept/deny) | Answer with !mirage a (answer)")


def load_duels():
    try:
        duels = pd.read_pickle('mirage_duels.pickle')
        challenger = duels.loc[duels.index[-1], 'challenger']
        opponent = duels.loc[duels.index[-1], 'opponent']
        consent = duels.loc[duels.index[-1], 'consent']
        age = time.time() - duels.loc[duels.index[-1], 'time']
        answer = duels.loc[duels.index[-1], 'answer']
        return duels, challenger, opponent, consent, age, answer
    except BaseException:
        return 'No challenges have been made yet MyHonestReaction'


def accept_duel():
    try:
        duels, challenger, opponent, consent, age, answer = load_duels()
    except BaseException:
        print(load_duels())
        return None

    if opponent != user:
        print(f"No one asked you for a challenge Awkward")
        return None

    if consent:
        print(f"You already accepted the duel SMH")
        return None

    if age > 30:
        print(
            f"The challenge has already expired... ({round(age - 30, 2)} seconds ago)")
        return None

    start_duel(challenger, opponent, duels)


def start_duel(challenger, opponent, duels):
    emotes = ['BAP', 'WeebSmash']
    board, answer = generate_grid()
    board = add_nodes(board)
    duels.loc[duels.index[-1], 'consent'] = 1
    duels.loc[duels.index[-1], 'answer'] = answer
    pd.to_pickle(duels, 'mirage_duels.pickle')
    print(
        f"{opponent} has accepted the duel from {challenger}! {
            np.random.choice(emotes)} May the lesser dent win o7")
    print_mirage_emotes(board)


def select_winner(duels, winner):
    bet = duels.loc[duels.index[-1], 'bet']
    duels.loc[duels.index[-1], 'winner'] = winner
    if winner == duels.loc[duels.index[-1], 'challenger']:
        loser = duels.loc[duels.index[-1], 'opponent']
    else:
        loser = duels.loc[duels.index[-1], 'challenger']

    emotes = ['FlanClap', 'EZ', 'ApuCross', 'AYAYA', 'HACKERMANS',
              'HOT', 'donkWalk', 'POGGIES', 'CHEER', 'WICKED']
    loser_emotes = ['dentt', 'Dentge', 'ApuDent', 'HeadEmpty',
                    'ryoApprove', 'Copeless', 'Coping', 'COPIUM']
    print(
        f"{winner} won the duel and gained {bet} campbucks! {
            np.random.choice(emotes)} Better luck next time {loser} {
            np.random.choice(loser_emotes)}")
    pd.to_pickle(duels, 'mirage_duels.pickle')
    winner_bank = getBalance(winner)
    loser_bank = getBalance(loser)
    winner_bank += bet
    loser_bank -= bet
    with open(f"{winner}.pickle", "wb") as f:
        pickle.dump(winner_bank, f)
    with open(f"{loser}.pickle", "wb") as f:
        pickle.dump(loser_bank, f)


def answer_duel(guess):
    if not check_active_challenge():
        print(f"There is no active duel...")
        return None
    try:
        duels, challenger, opponent, consent, age, answer = load_duels()
    except BaseException:
        print(load_duels())
        return None

    if user not in [challenger, opponent]:
        print(f"You aren't participating in the duel stfu")
        return None
    if not consent:
        print(f"You haven't started the duel yet...?")
        return None
    if age > 330:
        print(f"The duel has already expired.")
        return None
    if guess == answer:
        print(f"CORRECT!")
        select_winner(duels, user)

    elif user == challenger:
        print(f"INCORRECT! The correct answer was {answer}")
        select_winner(duels, opponent)

    else:
        print(f"INCORRECT! The correct answer was {answer}")
        select_winner(duels, challenger)


def fix_stats(user, amount):
    if user == 'all' and amount == 'all':
        stats = pd.DataFrame(columns=["user", "solve time", "reward"])
        with open('mirage_stats.pickle', 'wb') as f:
            pickle.dump(stats, f)
        print("All stats reset!")
        return None
    try:
        with open('mirage_stats.pickle', 'rb') as f:
            stats = pickle.load(f)
    except BaseException:
        print("There's no stats to fix homie MyHonestReaction")
        return None
    user_indices = stats[stats['user'] == user].index
    indices_to_remove = user_indices[-amount:]
    stats_cleaned = stats.drop(indices_to_remove)
    with open('mirage_stats.pickle', 'wb') as f:
        pickle.dump(stats_cleaned, f)
    print(f"Removed last {amount} entries from user {user}.")


def handle_daily(args=None):
    if args:
        check_mirage(args[0])
    else:
        check_mirage()


def handle_tutorial(args=None):
    board, answer = generate_grid()
    board = add_nodes(board)
    print_mirage_emotes(board)
    code = encrypt(answer)


def handle_decode(args):
    try:
        print(f"Answer: {decrypt(args[0])}")
    except BaseException:
        print("you did something wrong idiot")


def handle_help(args=None):
    print("Minigame: Find the mirage fish! In a 4x4 pond (grid), each cell starts with 0. The cell with the mirage fish is incremented by 1. The mirage fish places 5 decoys in the pond, each adding 1 to adjacent cells and itself (+ shape).")
    print("The decoys cannot be placed on top of each other, but can be placed on the mirage fish itself. You have 30 seconds to catch it.")
    print("Use chess notation to attempt a catch, e.g '!mirage a1' to attempt a catch on the bottom left corner, or '!mirage d4' to attempt a catch on the top right.")


def handle_print_stats(args=None):
    if args:
        if args[0] in ['help', 'elp', 'hep']:
            print(f"Prints stats for a given user or for camp. Values in brackets include correct answers outside of the allocated time.")
            return None
        print_stats(args[0])
    else:
        print_stats()


def handle_fix_stats(args):
    if user == 'hk_blau':
        fix_stats(args[0], args[1])


def handle_challenge(args):
    if not args:
        print(
            f"Challenges usage: !mirage challenge (user) (bet) | Answer with: !mirage a (answer)")
    elif len(args) < 2:
        print(
            f"Challenges usage: !mirage challenge (user) (bet) | Answer with: !mirage a (answer)")
    else:
        try:
            challenge(args[0], int(args[1]))
        except BaseException:
            print(f"Challenges usage: !mirage challenge (user) (bet)")


def handle_accept(args):
    accept_duel()


def handle_answer(args):
    if not args:
        print(f"Pepega you have to answer something")
        return None
    if args[0] in accepted_answers:
        answer_duel(args[0])


def handle_cancel(args=None):
    if not check_active_challenge():
        print(f"There is no duel active")
        return None
    duels, challenger, opponent, _, _, _ = load_duels()
    if user not in [challenger, opponent]:
        print(f"You can't cancel someone else's duel BAP")
        return None
    duels.loc[duels.index[-1], 'time'] = time.time() - 30
    pd.to_pickle(duels, 'mirage_duels.pickle')

    if user == challenger:
        print(f"Challenge rescinded")
    else:
        print(f"Challenge refused")


accepted_answers = [f"{chr(letter)}{number}" for letter in range(
    ord('a'), ord('e')) for number in range(1, 5)]


for i in range(len(sys.argv)):
    if i < 4:
        sys.argv[i] = sys.argv[i].lower()


commands = {
    'help': handle_help,
    'elp': handle_help,
    'hep': handle_help,
    'daily': handle_daily,
    'fix': handle_fix_stats,
    'example': handle_tutorial,
    'decode': handle_decode,
    'stats': handle_print_stats,
    'challenge': handle_challenge,
    'duel': handle_challenge,
    'accept': handle_accept,
    'a': handle_answer,
    'cancel': handle_cancel,
    'deny': handle_cancel
}

command = sys.argv[1] if len(sys.argv) > 1 else None
args = sys.argv[2:] if len(sys.argv) > 2 else None

if command in accepted_answers:
    check_mirage(command)
elif command in commands:
    commands[command](args)
else:
    handle_tutorial()
