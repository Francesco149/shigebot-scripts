# originally made by https://twitch.tv/HK_BLAU

import numpy as np
import pandas as pd
import time
from scipy.stats import norm
import pickle
import os
import sys
from datetime import datetime
from datetime import timedelta
import re

disable_sleep = 0
disable_prints = 0
weather_prints = 0

halt = False
user = os.environ['NICK']

# list of fishes
# data format: name, length, emote, weighted probability, fish thinness
cod = np.array(['cod', 20, 'OOO', 150, 6], dtype=object)
trout = np.array(['trout', 20, 'Fesh', 150, 6], dtype=object)
mackerel = np.array(['mackerel', 12, 'Sadgi', 100, 6], dtype=object)
salmon = np.array(['salmon', 30, 'peepoFAT', 100, 6], dtype=object)
catfish = np.array(['catfish', 25, 'OOO', 100, 5], dtype=object)
pike = np.array(['northern pike', 40, 'OOO', 100, 7], dtype=object)
crab = np.array(['crab', 5, '🦀', 100, 2], dtype=object)
FishMoley = np.array(['FishMoley', 20, 'FishMoley', 50, 3], dtype=object)
dwarf_pygmy_goby = np.array(
    ['dwarf pygmy goby', 0.5, 'ppL', 40, 10], dtype=object)
plankton = np.array(['plankton', 0.05, 'pL', 40, 10], dtype=object)
sea_horse = np.array(['sea horse', 8, 'PogRikka', 40, 6], dtype=object)
pufferfish = np.array(['pufferfish', 20, 'DANKIES', 40, 4], dtype=object)
goldfish = np.array(['goldfish', 10, 'FishJam', 40, 7], dtype=object)
sea_cucumber = np.array(['sea cucumber', 30, 'THIS', 40, 3], dtype=object)
star_fish = np.array(['star fish', 10, 'myonWhat', 40, 4], dtype=object)
coconut_octopus = np.array(
    ['coconut octopus', 15, '5Head', 40, 6], dtype=object)
tuna = np.array(['tuna', 100, 'OOO OOO OOO', 30, 7], dtype=object)
shark = np.array(['shark', 150, 'WICKED', 15, 9], dtype=object)
saw_shark = np.array(['saw shark', 100, 'ApuDent', 15, 10], dtype=object)
sword_fish = np.array(['sword fish', 100, 'WeebSmash', 15, 9], dtype=object)
blue_marlin = np.array(['blue marlin', 150, 'monkaW', 15, 7], dtype=object)

fishes = np.array([cod,
                   trout,
                   mackerel,
                   salmon,
                   catfish,
                   pike,
                   crab,
                   FishMoley,
                   dwarf_pygmy_goby,
                   plankton,
                   sea_horse,
                   pufferfish,
                   goldfish,
                   sea_cucumber,
                   star_fish,
                   coconut_octopus,
                   tuna,
                   shark,
                   saw_shark,
                   sword_fish,
                   blue_marlin])
point_normalizer = 4.7 * 1215 / np.sum(fishes[:, 3])

if disable_prints:
    def print(*args, **kwargs):
        pass


def sanitize(w):
    w = w.encode('ascii', 'ignore').decode('ascii')
    w = re.sub(r'(\s|\u180B|\u200B|\u200C|\u200D|\u2060|\uFEFF)+', '', w)
    return w


def load_logs():
    try:
        log = pd.read_pickle('fish_catalogue.pickle')
    except BaseException:
        log = pd.DataFrame(
            columns=[
                'user',
                'fish',
                'length',
                'l_percentile',
                'weight',
                'w_percentile',
                'points',
                'catch',
                'exceptional',
                'date'])
    for i in ['length', 'l_percentile', 'weight',
              'w_percentile', 'points', 'catch', 'date']:
        log[i] = pd.to_numeric(log[i])
    return log


def load_item(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except BaseException:
        return 0


def load_items(user):
    try:
        with open(f"{user}_items.pickle", "rb") as f:
            items = pickle.load(f)
    except BaseException:
        dailybaits = load_item(f"{user}_dailybait.pickle")
        masterbaits = load_item(f"{user}_masterbait.pickle")
        boots = load_item(f"{user}_boots.pickle")
        try:
            os.remove(f"{user}_dailybait.pickle")
            os.remove(f"{user}_masterbait.pickle")
            os.remove(f"{user}_boots.pickle")
        except BaseException:
            pass

        items = {
            'dailybait': dailybaits,
            'apprentice bait': 0,
            'journeyman bait': 0,
            'masterbait': masterbaits,
            'boots': boots}
        with open(f"{user}_items.pickle", "wb") as f:
            pickle.dump(items, f)
    return items


def save_logs(
        user=user,
        fish=np.nan,
        length=np.nan,
        l_percentile=np.nan,
        weight=np.nan,
        w_percentile=np.nan,
        points=0,
        catch=1,
        exceptional=False):
    date = time.time()
    log = load_logs()
    log.loc[len(log.index)] = [user, fish, length, l_percentile,
                               weight, w_percentile, points, catch, exceptional, date]
    pd.to_pickle(log, 'fish_catalogue.pickle')


def generate_fish(length_rng, weight_rng, fishes):
    fish_probs = fishes[:, 3] / np.sum(fishes[:, 3])
    fish_points = 1 / fish_probs
    fish_points = fish_points * calc_multiplier(length_rng, weight_rng)
    fishes = np.insert(fishes, 5, fish_points, axis=1)
    fish = np.random.choice(fishes[:, 0], p=fish_probs.astype('float64'))
    return fishes[fishes[:, 0] == fish].flatten()


def stats(fish, weight_rng, length_rng, density=1.08):
    length = fish[1] * (1 + length_rng)
    weight_var = fish[1] * (1 + weight_rng)
    weight = density * (1 / fish[4])**2 * \
        (0.7 * length**3 + 0.3 * weight_var**3) / 1000
    return weight, length


def exceptional(length_rng, weight_rng):
    if 1 - (1 - norm.cdf(length_rng)) * 2 > 0.98 or 1 - \
            (1 - norm.cdf(weight_rng)) * 2 > 0.98:
        return True, (1 - norm.cdf(length_rng)) * \
            2, (1 - norm.cdf(weight_rng)) * 2
    else:
        return False, (1 - norm.cdf(length_rng)) * \
            2, (1 - norm.cdf(weight_rng)) * 2


def calc_multiplier(length_rng, weight_rng):
    return (1 + length_rng) * (1 + weight_rng)


def calc_points(fish_points):
    # multiply by normalizer
    fish_points = round(fish_points * point_normalizer)
    try:
        with open(f"{user}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
    if fish_points >= 2000:
        print(f"You gained {fish_points} campbucks!!! WakuWakuHyper")
    elif fish_points >= 1000:
        print(f"You gained {fish_points} campbucks! Corpa")
    elif fish_points < 0:
        print(f"You lose {abs(fish_points)} campbucks... docSmash")
    else:
        print(f"You gained {fish_points} campbucks.")
    bankedPoints += int(fish_points)

    with open(f"{user}.pickle", "wb") as f:
        pickle.dump(bankedPoints, f)
    return fish_points


def get_weather():
    t = datetime.utcnow()
    try:
        with open(f"fish_weather.pickle", "rb") as f:
            weather = pickle.load(f)
        first = False
    except BaseException:
        first = True
    if first or t > weather['next']:
        APIKEY = os.environ["OPENWEATHERMAP_API_KEY"]
        from pyowm import OWM
        owm = OWM(APIKEY)
        mgr = owm.weather_manager()
        locs = np.array(['Rome, IT',
                         'Alcala de Henares, ES',
                         'Tuusula, FI',
                         'Odessa, UA',
                         'Chalon-sur-Saône, FR',
                         'Bandung, ID',
                         'La Plata, AR',
                         'Florida, US',
                         'Melbourne, AU',
                         'Republic of Madagascar, MG',
                         'Antarctica,'])
        loc = np.random.choice(locs)
        observation = mgr.weather_at_place(loc)
        next_weather = t.replace(
            microsecond=0, second=0, minute=0) + timedelta(hours=1)
        w = observation.weather
        if '1h' in w.rain:
            rain = w.rain['1h']
        else:
            rain = 0
        weather = {
            'next': next_weather,
            'status': w.detailed_status,
            'clouds': w.clouds,
            'rain': rain,
            'wind': w.wind()['speed'],
            'loc': loc}
        with open(f"fish_weather.pickle", "wb") as f:
            pickle.dump(weather, f)
        global weather_prints
        if not weather_prints:
            weather_prints = 1
            print_weather("forsenCalculating Weather updated: ")
    return weather


def fishing_modifier():
    modifier = {
        'clouds': (
            0, 'clear sky'), 'rain': (
            0, 'no rain'), 'thunder': (
                0, 'no thunder'), 'wind': (
                    0, 'no wind'), 'loc': ''}
    weather = get_weather()
    modifier['loc'] = weather['loc']
    if weather['clouds']:
        if 10 < weather['clouds'] <= 25:
            modifier['clouds'] = 1, 'few clouds'
        elif 25 < weather['clouds'] <= 50:
            modifier['clouds'] = 2, 'scattered clouds'
        elif 50 < weather['clouds'] <= 84:
            modifier['clouds'] = 3, 'broken clouds'
        elif 84 < weather['clouds']:
            modifier['clouds'] = 5, 'overcast'

    if 'thunder' in weather['status']:
        modifier['thunder'] = 10, 'thunder detected monkaLaugh'

    if weather['rain']:
        buffed_rain = weather['rain'] * 1.5
        if 0 < buffed_rain <= 1:
            modifier['rain'] = 3, 'drizzle'
        elif 1 < buffed_rain <= 2.5:
            modifier['rain'] = 5, 'light rain'
        elif 2.5 < buffed_rain <= 5:
            modifier['rain'] = 7, 'moderate rain'
        elif 5 < buffed_rain <= 10:
            modifier['rain'] = 10, 'heavy rain'
        elif 10 < buffed_rain <= 25:
            modifier['rain'] = 12, 'very heavy rain'
        elif 25 < buffed_rain:
            modifier['rain'] = 15, 'extreme rain'

    if weather['wind']:
        buffed_wind = weather['wind'] * 1.5
        if 3 < buffed_wind <= 5:
            modifier['wind'] = 1, 'light breeze'
        elif 5 < buffed_wind <= 7:
            modifier['wind'] = 2, 'moderate breeze'
        elif 7 < buffed_wind <= 10:
            modifier['wind'] = 3, 'fresh breeze'
        elif 10 < buffed_wind <= 14:
            modifier['wind'] = 4, 'strong breeze'
        elif 14 < buffed_wind <= 17:
            modifier['wind'] = 5, 'near gale'
        elif 17 < buffed_wind <= 20:
            modifier['wind'] = 6, 'gale'
        elif 20 < buffed_wind <= 24:
            modifier['wind'] = 7, 'strong gale'
        elif 24 < buffed_wind:
            modifier['wind'] = 10, 'heavy storm'
    return modifier


def calc_mod_buff(mod):
    buff = 25 / (100 - mod) - 25 / 100
    return f"(+{round(buff * 100, 1)}%)"


def fishing():
    weight_rng = np.abs(np.random.normal())
    length_rng = np.abs(np.random.normal())
    ex = exceptional(length_rng, weight_rng)
    emotes = np.array([['HELP',
                        'MURI',
                        'AYAYAWeird'],
                       ['ReallyMad',
                        'POUTING',
                        'waaa',
                        'NOOOOvanish'],
                       ['docSmash',
                        'UltraMad',
                        'RATIO',
                        'kleeRAGEY',
                        'catSmash']],
                      dtype='object')
    modifier = fishing_modifier()
    lower_bound = modifier['clouds'][0] + modifier['rain'][0] + \
        modifier['wind'][0] + modifier['thunder'][0]

    item_statuses = {
        'daily': False,
        'master': False,
        'journeyman': False,
        'apprentice': False,
        'boot': False
    }

    items = load_items(user)
    item_counts = {
        'daily': items['dailybait'],
        'master': items['masterbait'],
        'journeyman': items['journeyman bait'],
        'apprentice': items['apprentice bait'],
        'boot': items['boots']
    }

    if item_counts['daily'] > 0:
        item_statuses['daily'] = True
        lower_bound += 35
        line_break = np.random.choice([0, 1], p=[2 / 3, 1 / 3])
        if item_counts['daily'] > 1:
            print(
                f"You used a dailybait. {
                    item_counts['daily'] -
                    1} left... {
                    calc_mod_buff(lower_bound)}")
        else:
            print(
                f"You cast your last dailybait... plank {
                    calc_mod_buff(lower_bound)}")

    elif item_counts['master'] > 0:
        item_statuses['master'] = True
        lower_bound = 75
        line_break = 0
        if item_counts['master'] > 1:
            print(
                f"You used a masterbait. {
                    item_counts['master'] -
                    1} left... PauseChamp")
        else:
            print(f"You cast your last masterbait... DOPIUM")

    elif item_counts['journeyman'] > 0:
        item_statuses['journeyman'] = True
        lower_bound += 50
        line_break = np.random.choice([0, 1], p=[3 / 4, 1 / 4])
        if item_counts['journeyman'] > 1:
            print(
                f"You used a journeyman bait. {
                    item_counts['journeyman'] -
                    1} left... lookDown {
                    calc_mod_buff(lower_bound)}")
        else:
            print(
                f"You cast your last journeyman bait... borpaSpin {
                    calc_mod_buff(lower_bound)}")

    elif item_counts['apprentice'] > 0:
        item_statuses['apprentice'] = True
        lower_bound += 25
        line_break = np.random.choice([0, 1], p=[2 / 3, 1 / 3])
        if item_counts['apprentice'] > 1:
            print(
                f"You used an apprentice bait. {
                    item_counts['apprentice'] -
                    1} left... eatt {
                    calc_mod_buff(lower_bound)}")
        else:
            print(
                f"You cast your last apprentice bait... eatt {
                    calc_mod_buff(lower_bound)}")

    else:
        line_break = np.random.randint(0, 2)
        print(f"... {calc_mod_buff(lower_bound)}")

    fishing_rng = np.random.randint(lower_bound, 100)
    if fishing_rng < 75:
        if disable_sleep == 0:
            time.sleep(5)
        print('No luck. Life')
        save_logs(catch=0)

    elif 75 <= fishing_rng and fishing_rng < 95:
        if disable_sleep == 0:
            time.sleep(np.random.randint(2, 5))
        fish = generate_fish(length_rng, weight_rng, fishes)
        fish_stats = stats(fish, weight_rng, length_rng)
        print('!')
        if fish_stats[0] > 15:
            print('!!')
        if fish_stats[0] > 50:
            print('!!!')
        if line_break == 0:
            fish_length = round(fish_stats[1], 1)
            fish_weight = round(fish_stats[0], 1)
            length_percentile = round(ex[1] * 100, 3)
            weight_percentile = round(ex[2] * 100, 3)
            print(
                f"You caught a {fish_length} cm long {
                    fish[0]}, weighing {fish_weight} kg! {
                    fish[2]}")
            if ex[0]:
                print(
                    f"It's an exceptional {
                        fish[0]}, with it's length being in the top {length_percentile} percentile and weight in the top {weight_percentile} percentile!")
            save_logs(
                fish=fish[0],
                length=fish_length,
                l_percentile=length_percentile,
                weight=fish_weight,
                w_percentile=weight_percentile,
                points=calc_points(
                    fish[5]),
                exceptional=ex[0])
        else:
            save_logs(catch=0)
            if fish_stats[0] > 50:
                print(
                    f"The fish was too massive and snapped the line. {
                        np.random.choice(
                            emotes[2])}")
            elif fish_stats[0] > 15:
                print(
                    f"The fish snatched the bait and escaped... {
                        np.random.choice(
                            emotes[1])}")
            else:
                print(
                    f"The fish got off the hook... {
                        np.random.choice(
                            emotes[0])}")

    else:
        seaweed = np.array(['seaweed', 400, 0], dtype=object)
        boot = np.array(['boot', 200, 0], dtype=object)
        lobster = np.array(['lobster', 100, 40], dtype=object)
        boots = np.array(['boots', 50, 0], dtype=object)
        corpse = np.array(
            ['corpse', 20, -1000 / point_normalizer], dtype=object)
        carp = np.array(['carp', 15, 2500 / point_normalizer *
                        calc_multiplier(length_rng, weight_rng)], dtype=object)
        masterbait = np.array(['masterbait', 12, 69], dtype=object)
        orca = np.array(['orca', 10, 10000 / point_normalizer *
                        calc_multiplier(length_rng, weight_rng)], dtype=object)
        hippo = np.array(['hippo', 10, 20000 / point_normalizer *
                         calc_multiplier(length_rng, weight_rng)], dtype=object)
        blue_whale = np.array(['blue whale', 5, 2500 /
                               point_normalizer *
                               calc_multiplier(length_rng, weight_rng)], dtype=object)
        if modifier['thunder'][0]:
            thunder = np.array(
                ['thunder', 250, -1000 / point_normalizer], dtype=object)
            specials = np.array([seaweed,
                                 boot,
                                 lobster,
                                 boots,
                                 corpse,
                                 carp,
                                 masterbait,
                                 orca,
                                 hippo,
                                 blue_whale,
                                 thunder])
        else:
            specials = np.array([seaweed,
                                 boot,
                                 lobster,
                                 boots,
                                 corpse,
                                 carp,
                                 masterbait,
                                 orca,
                                 hippo,
                                 blue_whale])
        special_probs = specials[:, 1] / np.sum(specials[:, 1])
        special = np.random.choice(
            specials[:, 0], p=special_probs.astype('float64'))
        if disable_sleep == 0:
            time.sleep(np.random.randint(2, 5))

        if special == 'seaweed':
            print('!')
            print('You caught a pile of seaweed. eShrug')
            save_logs(fish=special)

        if special == 'boot':
            if ex[0]:
                print('!')
                if item_counts['boot'] < 2:
                    if item_counts['boot'] == 0:
                        print(
                            f"You found an exceptional boot! You only have one boot but decide to wear it regardless... Susge")
                    if item_counts['boot'] == 1:
                        print(
                            f"You found another exceptional boot! You now have a pair of fancy boots! POGGERS")
                    item_statuses['boot'] = True
                    item_counts['boot'] += 1
                    save_logs(fish=special, exceptional=ex[0])
                else:
                    print(
                        f"You found yet another exceptional boot, but you already have a pair so you decide to sell it. Corpa")
                    save_logs(fish=special, points=calc_points(
                        1000 / point_normalizer), exceptional=ex[0])
            else:
                print('!')
                print('You found a boot. MyHonestReaction')
                save_logs(fish=special)

        elif special == 'lobster':
            print('!')
            lobster_rng = np.random.randint(0, 500)
            if lobster_rng == 0:
                print(f"!!! AINTNOWAY")
                if disable_sleep == 0:
                    time.sleep(2)
                print(
                    f"It's an incredibly rare blue lobster weighing {
                        round(
                            2 *
                            (
                                1 +
                                weight_rng),
                            1)} kg!!! You've heard that these sell for an incredible amount! WakuWakuHyper")
                save_logs(fish='blue lobster',
                          weight=round(2 * (1 + weight_rng),
                                       1),
                          points=calc_points(
                              lobster[2] * (1 + weight_rng) * 200),
                          w_percentile=round(ex[2] * 100,
                                             3))
            else:
                print(
                    f"You caught a {round(2 * (1 + weight_rng), 1)} kg lobster! VeryPog")
                save_logs(fish='lobster',
                          weight=round(2 * (1 + weight_rng),
                                       1),
                          points=calc_points(lobster[2] * (1 + weight_rng)),
                          w_percentile=round(ex[2] * 100,
                                             3))

        elif special == 'boots':
            print('!')
            print('!!')
            if ex[0]:
                if item_counts['boot'] < 2:
                    if item_counts['boot'] == 0:
                        print(
                            f"You found a pair of fancy boots! You immediately wear them. Nothing bad has ever come from wearing a pair of fancy boots...")
                        save_logs(fish=special, exceptional=ex[0])
                    if item_counts['boot'] == 1:
                        print(
                            f"Unbelievable! You found a pair of exceptional boots. You now have 3 fancy boots, and decide to sell one of them. STONKS")
                        save_logs(fish=special, points=calc_points(
                            1000 / point_normalizer), exceptional=ex[0])
                    item_statuses['boot'] = True
                    item_counts['boot'] = 2
                else:
                    print(
                        f"You found an entangled pair of exceptional boots! Since you already have a pair you decide to sell them. STONKS")
                    save_logs(fish=special, points=calc_points(
                        2000 / point_normalizer), exceptional=ex[0])
            else:
                print('You found a pair of entangled boots. Awkward')
                save_logs(fish=special)

        elif special == 'corpse':
            print('!')
            print('!!')
            print('!!!')
            print('A mangled corpse floats up infront of you. NAHHH')
            if disable_sleep == 0:
                time.sleep(4)
            baits_reel = {
                'daily': 'You reel in the unused dailybait and decide to change fishing spots. Out of sight, out of mind. Clueless',
                'master': 'You reel in the unused masterbait and decide to change fishing spots. Out of sight, out of mind. Clueless',
                'journeyman': 'You reel in the unused journeyman bait and decide to change fishing spots. Out of sight, out of mind. Clueless',
                'apprentice': 'You reel in the unused apprentice bait and decide to change fishing spots. Out of sight, out of mind. Clueless'}

            for bait, message in baits_reel.items():
                if item_statuses[bait]:
                    print(message)
                    item_statuses[bait] = False
                    break
            else:
                print(
                    'You decide to change fishing spots. Out of sight, out of mind. Clueless')
            save_logs(fish=special, points=calc_points(corpse[2]))

        elif special == 'carp':
            print('!')
            print('!!')
            print('!!!')
            special_fish = 'golden carp', 20, 'WakuWakuHyper', 1, 6
            special_stats = stats(special_fish, weight_rng,
                                  length_rng, density=20)
            special_length = round(special_stats[1], 1)
            special_weight = round(special_stats[0], 1)
            length_percentile = round(ex[1] * 100, 3)
            weight_percentile = round(ex[2] * 100, 3)
            print(
                f"It's a legendary catch! You caught a {
                    round(
                        special_stats[1],
                        1)} cm long {
                    special_fish[0]}, weighing {
                    round(
                        special_stats[0],
                        1)} kg! It's made of pure gold and is therefore extremely heavy! {
                            special_fish[2]}")
            if ex[0]:
                print(
                    f"It's an exceptional {
                        special_fish[0]}, with it's length being in the top {
                        round(
                            ex[1] * 100,
                            3)} percentile and weight in the top {
                        round(
                            ex[2] * 100,
                            3)} percentile! You are the luckiest fisher in the world! WAYTOODANK")
            save_logs(
                fish=special_fish[0],
                length=special_length,
                l_percentile=length_percentile,
                weight=special_weight,
                w_percentile=weight_percentile,
                points=calc_points(
                    carp[2]),
                exceptional=ex[0])

        elif special == 'orca':
            print('!')
            print('!!')
            print('!!!')
            print('!!!!!!!!!!!!!!!!!!')
            print("IT'S AN ORCA!!! PAAANNNIIICCC")
            print('INSANECAT INSANECAT INSANECAT')
            if disable_sleep == 0:
                time.sleep(3)
            orca_rng = np.random.randint(0, 4)
            if orca_rng == 0 or item_statuses['master'] or item_statuses['journeyman']:
                special_fish = 'orca', 400, 'SheCrazy SheCrazy SheCrazy', 1, 8
                special_stats = stats(special_fish, weight_rng, length_rng)
                special_length = round(special_stats[1], 1)
                special_weight = round(special_stats[0], 1)
                length_percentile = round(ex[1] * 100, 3)
                weight_percentile = round(ex[2] * 100, 3)
                if item_statuses['master']:
                    print(
                        f"The orca went for the masterbait, putting it into eternal slumber and making it an easy catch! The orca is {
                            round(
                                special_stats[1],
                                1)} cm long, weighing {
                            round(
                                special_stats[0],
                                1)} kg! {
                            special_fish[2]}")
                elif item_statuses['journeyman']:
                    print(
                        f"The orca went for the journeyman bait, putting it into deep slumber, making it an easy catch! The orca is {
                            round(
                                special_stats[1],
                                1)} cm long, weighing {
                            round(
                                special_stats[0],
                                1)} kg! {
                            special_fish[2]}")
                else:
                    print(
                        f"You did the impossible! You caught a {
                            round(
                                special_stats[1],
                                1)} cm long {
                            special_fish[0]}, weighing {
                            round(
                                special_stats[0],
                                1)} kg! {
                            special_fish[2]}")
                if ex[0]:
                    print(
                        f"It's an exceptional {
                            special_fish[0]}, with it's length being in the top {
                            round(
                                ex[1] *
                                100,
                                3)} percentile and weight in the top {
                            round(
                                ex[2] *
                                100,
                                3)} percentile! WAYTOODANK WAYTOODANK WAYTOODANK (this will literally never happen)")
                save_logs(
                    fish=special_fish[0],
                    length=special_length,
                    l_percentile=length_percentile,
                    weight=special_weight,
                    w_percentile=weight_percentile,
                    points=calc_points(
                        orca[2]),
                    exceptional=ex[0])
            else:
                print(f"The orca caught you. deadlole")
                save_logs(fish='orca', catch=0,
                          points=calc_points(-2500 / point_normalizer))

        elif special == 'masterbait':
            print('!')
            print('HUH ???')
            if disable_sleep == 0:
                time.sleep(2)
            item_counts['master'] += 10
            if item_statuses['master']:
                print(
                    f"You found another 10 masterbait WHAT The next {
                        item_counts['master'] -
                        1} casts are guaranteed to catch something!!! SheCrazy")
            else:
                print(
                    f"You found a sealed can of 10 masterbait! Your 10 next fishing casts are guaranteed to catch something!!! WakuWakuHyper")
            save_logs(fish=special)

        if special == 'blue whale':
            print('Binoculars The frick is that?')
            if disable_sleep == 0:
                time.sleep(3)
            print("IT'S A BLUE WHALE!!! WakuWakuHyper")
            if disable_sleep == 0:
                time.sleep(3)
            print(f"You consider the ethical implications of catching such a magnificent and endangered creature. You decide to not try and catch it. Meditate")
            if disable_sleep == 0:
                time.sleep(3)
            baits_reel = {
                'daily': 'You reel your dailybait back and store it.',
                'master': 'You reel your masterbait back and store it.',
                'journeyman': 'You reel your journeyman bait back and store it.',
                'apprentice': 'You reel your apprentice bait back and store it.'}

            for bait, message in baits_reel.items():
                if item_statuses[bait]:
                    print(message)
                    item_statuses[bait] = False
                    break
            save_logs(
                fish=special,
                l_percentile=round(
                    ex[1] * 100,
                    3),
                w_percentile=round(
                    ex[2] * 100,
                    3),
                points=calc_points(
                    blue_whale[2]),
                catch=0)

        elif special == 'hippo':
            print('!')
            print('!!')
            print('!!!')
            print(np.random.choice(['NOOOO', 'catDespair2']))
            print(
                "Death It's a hippo. You accept death as the hippo charges at your boat rapidly... FeelsWeakMan")
            if item_statuses['master'] or item_statuses['journeyman']:
                special_length = round(200 * (1 + length_rng**(1 / 1.5)), 1)
                special_weight = round(
                    1000 * (1 + length_rng**(1 / 2) + weight_rng**(1 / 2)), 1)
                length_percentile = round(ex[1] * 100, 3)
                weight_percentile = round(ex[2] * 100, 3)
                if item_statuses['master']:
                    print(
                        f"... but the hippo went for the masterbait! The wondrous effects of the masterbait put the hippo into eternal slumber {
                            np.random.choice(
                                [
                                    'RATIO',
                                    'NOWAYING',
                                    'WICKED'])}")
                if item_statuses['journeyman']:
                    print(
                        f"... but the hippo went for the journeyman bait! The wondrous effects of the bait put the hippo into deep slumber {
                            np.random.choice(
                                ['NOWAYING'])}")
                if disable_sleep == 0:
                    time.sleep(3)
                print(
                    f"It's a miracle! You caught a {
                        round(
                            special_length,
                            1)} cm long hippo, weighing {
                        round(
                            special_weight,
                            1)} kg! You dodge death by pure happenstance and feel invincible! WICKED WICKED WICKED")
                if ex[0]:
                    print(
                        f"It's an exceptional hippo, with it's length being in the top {
                            round(
                                ex[1] *
                                100,
                                3)} percentile and weight in the top {
                            round(
                                ex[2] *
                                100,
                                3)} percentile! WTF WAYTOODANK WTF WAYTOODANK (if this happens something must be bugged)")
                save_logs(
                    fish='hippo',
                    length=special_length,
                    l_percentile=length_percentile,
                    weight=special_weight,
                    w_percentile=weight_percentile,
                    points=calc_points(
                        hippo[2]),
                    exceptional=ex[0])
            else:
                print(
                    f"The hippo effortlessly devours you. {np.random.choice(['GachiPls', 'billyReady'])}")
                save_logs(fish='hippo', points=calc_points(-2500 /
                          point_normalizer), catch=0, exceptional=ex[0])
        elif special == 'thunder':
            print('BAKOOM NOOOOvanish')
            time.sleep(3)
            print('You got hit by thunder. Deadge')
            save_logs(fish=special, points=calc_points(thunder[2]), catch=0)

    boolin = [
        item_statuses['daily'],
        item_statuses['master'],
        item_statuses['journeyman'],
        item_statuses['apprentice'],
        item_statuses['boot']]
    # updates item counts
    if any(boolin):
        if item_statuses['daily']:
            item_counts['daily'] -= 1
        elif item_statuses['master']:
            item_counts['master'] -= 1
        elif item_statuses['journeyman']:
            item_counts['journeyman'] -= 1
        elif item_statuses['apprentice']:
            item_counts['apprentice'] -= 1
        items = {
            'dailybait': item_counts['daily'],
            'apprentice bait': item_counts['apprentice'],
            'journeyman bait': item_counts['journeyman'],
            'masterbait': item_counts['master'],
            'boots': item_counts['boot']}
        with open(f"{user}_items.pickle", "wb") as f:
            pickle.dump(items, f)

    t = datetime.utcnow()
    with open(f"{user}fishcd.pickle", "wb") as f:
        pickle.dump(t, f)


def print_weather(calc=''):
    global weather_prints
    weather_prints = 1
    mods = fishing_modifier()
    buff = calc_mod_buff(
        mods['clouds'][0] +
        mods['rain'][0] +
        mods['wind'][0] +
        mods['thunder'][0]
    )
    s = ", ".join([
        mods['clouds'][1],
        mods['rain'][1],
        mods['wind'][1],
        mods['thunder'][1],
        buff
    ])
    print(f"{calc}{s} {buff})")


def search_db(user='all', fish=None, casts=False):
    specials = ['seaweed', 'boot', 'lobster', 'blue lobster',
                'boots', 'corpse', 'masterbait', 'blue whale']
    log = load_logs()
    if user != 'all':
        log = log[log.user == user]

    if fish is None and casts != True:
        tot_casts = len(log.index)
        caught = log[log.catch == 1]
        catches = len(caught)
        profit = log['points'].sum()
        if catches > 0:
            best = log.loc[caught['points'].idxmax()]

    if fish not in specials and fish is not None and casts != True:
        caught = log[(log.catch == 1) & (log.fish == fish)]
        catches = len(caught)
        profit = caught['points'].sum()
        if catches > 0:
            best = log.loc[caught['points'].idxmax()]

    if fish in specials:
        caught = log[(log.catch == 1) & (log.fish == fish)]
        catches = len(caught)

    if casts:
        tot_casts = len(log.index)
        catches = len(log[log.catch == 1])
        if user == 'all':
            if tot_casts > 0:
                print(
                    f"Camp has fished {tot_casts} times! They've caught a total of {catches} things! POGGERS")
            else:
                print(f"Camp has not fished a single time yet... Uhmm")
        else:
            if tot_casts > 0:
                print(
                    f"{user} has attempted fishing {tot_casts} times! They've caught a total of {catches} things! POGGERS")
            else:
                print(f"{user} has not fished a single time yet... Uhmm")

    elif fish not in specials:
        if user == 'all':
            if fish is None:
                if catches > 0:
                    print(
                        f"Total number of casts: {tot_casts}. Total number of things caught: {catches}. Total number of campbucks fished: {profit}. catches/cast ratio: {
                            round(
                                catches /
                                tot_casts,
                                3)}. campbucks/cast ratio: {
                            round(
                                profit /
                                tot_casts,
                                3)} Corpa")
                    if best['fish'] in specials:
                        print(
                            f"The best recorded creature was caught by {
                                best['user']} and it's a {
                                best['fish']} with weight {
                                best['weight']}kg (top {
                                best['w_percentile']} percentile) that was worth {
                                best['points']} campbucks! WICKED")
                    else:
                        print(
                            f"The best recorded creature was caught by {
                                best['user']} and it's a {
                                best['fish']} with length {
                                best['length']}cm (top {
                                best['l_percentile']} percentile) and weight {
                                best['weight']}kg (top {
                                best['w_percentile']} percentile) that was worth {
                                best['points']} campbucks! WICKED")
                else:
                    print(f"Camp has not caught any fish yet... FeelsWeakMan")
            else:
                if catches > 0:
                    print(
                        f"The total number of {fish}(s) caught: {catches}. Total value: {profit} campbucks. JustAnotherDay")
                    # print(f"The longest {fish} ever caught was {best['fish']}cm long. The heaviest {fish} ever caught weighed {best['weight']}kg!")
                    print(
                        f"The best recorded {fish} caught was by {
                            best['user']} and had a length of {
                            best['length']}cm (top {
                            best['l_percentile']} percentile), weight {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks. WICKED")
                else:
                    print(f"Camp has not caught a single {fish} yet... Uhmm")
        else:
            if fish is None:
                if catches > 0:
                    print(
                        f"{user} has casted a fishing line {tot_casts} times. They've caught {catches} things. They've earned {profit} campbucks from fishing. catches/casts ratio: {
                            round(
                                catches /
                                tot_casts,
                                3)}. campbucks/cast ratio: {
                            round(
                                profit /
                                tot_casts,
                                3)} Corpa")
                    if best['fish'] in specials:
                        print(
                            f"The best recorded creature they've caught is a {
                                best['fish']} with  weight {
                                best['weight']}kg (top {
                                best['w_percentile']} percentile) that was worth {
                                best['points']} campbucks. WICKED")
                    else:
                        print(
                            f"The best recorded creature they've caught is a {
                                best['fish']} with length {
                                best['length']}cm (top {
                                best['l_percentile']} percentile) and weight {
                                best['weight']}kg (top {
                                best['w_percentile']} percentile) that was worth {
                                best['points']} campbucks. WICKED")
                else:
                    print(f"{user} has not caught any fish yet Disgust")
            else:
                if catches > 0:
                    print(
                        f"{user} has caught a total of {catches} {fish}(s) with a total value of {profit} campbucks.")
                    # print(f"The longest {fish} they've caught was {db['length']}cm long. The heaviest {db['type']} weighed {db['weight']}kg! CHEER")
                    print(
                        f"The best recorded {fish} they've caught had length {
                            best['length']}cm (top {
                            best['l_percentile']} percentile), weight {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks. WICKED")
                else:
                    print(
                        f"{user} has not caught a single {fish} yet. UNPOGGERS")

    elif fish in specials:
        if user == 'all':
            if fish == 'seaweed':
                if catches > 0:
                    print(
                        f"The total number of {fish} caught is {catches}. MyHonestReaction")
                else:
                    print(f"Camp has not caught a single {fish} yet. Ok")

            if fish == 'boot':
                fancy = len(caught[(caught.exceptional)])
                if fancy > 0:
                    print(
                        f"Camp has caught {catches} {fish}s, out of which {fancy} were exceptional! POGGERS")
                elif catches > 0:
                    print(
                        f"The total number of {fish}s caught: {catches}. MyHonestReaction")
                else:
                    print(f"Camp has not caught a single {fish} yet. Sadgi")

            if fish == 'lobster':
                if catches > 0:
                    best = log.loc[caught['points'].idxmax()]
                    profit = caught['points'].sum()
                    print(
                        f"Total number of {fish}s caught: {catches}. Total value: {profit} campbucks. CHEER")
                    print(
                        f"The best {fish} ever caught was by {
                            best['user']}, weighed {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks! PagBounce")
                else:
                    print(f"Camp has not caught a single {fish} yet. Sadgi")

            if fish == 'blue lobster':
                if catches > 0:
                    best = log.loc[caught['points'].idxmax()]
                    profit = caught['points'].sum()
                    print(
                        f"Total number of {fish}s caught: {catches}. Total value: {profit} campbucks. STONKS")
                    print(
                        f"The best {fish} ever caught was by {
                            best['user']}, weighed {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks! WakuWakuHyper")
                else:
                    print(f"Camp has not caught a single {fish} yet. Sadgi")

            if fish == 'boots':
                fancy = len(caught[(caught.exceptional)])
                if fancy > 0:
                    print(
                        f"The total number of entangled {fish} caught: {catches}, but camp has also caught {fancy} fancy pairs of boots! POGGERS")
                elif catches > 0:
                    print(
                        f"The total number of {fish} caught: {catches}. MyHonestReaction")
                else:
                    print(
                        f"Camp has not caught a single pair of {fish} yet. Sadgi")

            if fish == 'corpse':
                if catches > 0:
                    print(
                        f"The total number of {fish}s found: {catches}. NAHHH")
                else:
                    print(
                        f"Why would camp find a corpse while fishing? Clueless")

            if fish == 'masterbait':
                if catches > 0:
                    print(f"Camp has found {catches * 10} masterbait. kok")
                else:
                    print(
                        f"Camp has not found any {fish} yet. MyHonestReaction")

            if fish == 'blue whale':
                encounters = log[(log.fish == fish)]
                if len(encounters) > 0:
                    profit = encounters['points'].sum()
                    best = log.loc[encounters['points'].idxmax()]
                    print(
                        f"PogRikka Camp has encountered {
                            len(encounters)} blue whale(s). They have gained {profit} morality points (campbucks) from these encounters. baseg")
                    print(
                        f"The most magnificent blue whale ever encountered was by {
                            best['user']}! The blue whale had top {
                            best['l_percentile']} percentile length, top {
                            best['w_percentile']} percentile weight and gave {
                            best['points']} morality points! WICKED (our scales broke when trying to measure the blue whale so we only have relative percentile stats)")
                else:
                    print(
                        f"Camp has not encountered a single {fish} yet. MyHonestReaction")

        else:
            if fish == 'seaweed':
                if catches > 0:
                    print(
                        f"{user} has caught a total of {catches} {fish}. MyHonestReaction")
                else:
                    print(f"{user} has not caught a single {fish} yet. Ok")

            if fish == 'boot':
                fancy = len(caught[(caught.exceptional)])
                if fancy > 0:
                    print(
                        f"{user} has caught a total of {catches} {fish}s, but they have also caught {fancy} exceptional boots! POGGERS")
                elif catches > 0:
                    print(
                        f"The total number of {fish}s caught: {catches}. MyHonestReaction")
                else:
                    print(f"{user} has not caught a single {fish} yet. Sadgi")

            if fish == 'lobster':
                if catches > 0:
                    best = log.loc[caught['points'].idxmax()]
                    profit = caught['points'].sum()
                    print(
                        f"{user} has caught a total of {catches} {fish}s with total value of {profit} campbucks. CHEER")
                    print(
                        f"The best {fish} they've ever caught weighed {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks! PagBounce")
                else:
                    print(f"{user} has not caught a single {fish} yet. Sadgi")

            if fish == 'blue lobster':
                if catches > 0:
                    best = log.loc[caught['points'].idxmax()]
                    profit = caught['points'].sum()
                    print(
                        f"{user} has caught a total of {catches} {fish}s with total value of {profit} campbucks. STONKS")
                    print(
                        f"The best {fish} they've ever caught weighed {
                            best['weight']}kg (top {
                            best['w_percentile']} percentile) and was worth {
                            best['points']} campbucks! WakuWakuHyper")
                else:
                    print(f"{user} has not caught a single {fish} yet. Sadgi")

            if fish == 'boots':
                fancy = len(caught[(caught.exceptional)])
                if fancy > 0:
                    print(
                        f"{user} has caught a total of {catches} pairs of entangled {fish}, but they have also caught {fancy} fancy pairs of boots! WICKED")
                elif catches > 0:
                    print(
                        f"The total number of entangled {fish} caught: {catches}. Fukkireta")
                else:
                    print(
                        f"{user} has not caught a single pair of {fish} yet. Sadgi")

            if fish == 'corpse':
                if catches > 0:
                    print(
                        f"{user} has found a total of {catches} {fish}s. NAHHH")
                else:
                    print(
                        f"Why would anyone find a corpse while fishing? Clueless")

            if fish == 'masterbait':
                if catches > 0:
                    print(f"{user} has found {catches * 10} masterbait. kok")
                else:
                    print(
                        f"{user} has not found any {fish} yet. MyHonestReaction")

            if fish == 'blue whale':
                encounters = log[(log.fish == fish)]
                if len(encounters) > 0:
                    profit = caught['points'].sum()
                    best = log.loc[encounters['points'].idxmax()]
                    print(
                        f"{user} has encountered {encounters} blue whale(s). They have {profit} morality points (campbucks) for their ethical actions. baseg")
                    print(
                        f"The most magnificent blue whale {
                            best['user']} has encountered had top {
                            best['l_percentile']} percentile length, top {
                            best['w_percentile']} percentile weight and gave {
                            best['points']} morality points! WICKED (our scales broke when trying to measure the blue whale so we only have relative percentile stats)")
                else:
                    print(
                        f"{user} has not encountered a single {fish} yet. MyHonestReaction")
    else:
        print('What are you trying to do? MyHonestReaction')


def obs_prob(user='all', fish=None):
    log = load_logs()
    if user != 'all':
        log = log[log.user == user]
    tot_casts = len(log.index)
    caught = log[(log.catch == 1) & (log.fish == fish)]
    catches = len(caught)

    if fish is None:
        if user == 'all':
            print(
                f"The total observed probability of catching anything is {
                    round(
                        catches / tot_casts * 100,
                        5)}%")
        else:
            print(
                f"The observed probability of catching anything for {user} is {
                    round(
                        catches / tot_casts * 100,
                        5)}%")
    else:
        if user == 'all':
            print(
                f"The total observed probability of catching a {fish} is {
                    round(
                        catches / tot_casts * 100,
                        5)}%")
        else:
            print(
                f"The observed probability of catching a {fish} for {user} is {
                    round(
                        catches / tot_casts * 100,
                        5)}%")


def lowest(user='all', fish=None):
    log = load_logs()
    if user != 'all':
        log = log[log.user == user]
    if fish is not None:
        log = log[log.fish == fish]
    log = log[log.catch == 1]
    log = log[log.points > 0]
    log = log[log.points == log.points.min()]
    if len(log) < 1:
        print(f"No fish caught... MyHonestReaction")
        return
    log = log.iloc[0]
    if user == 'all':
        print(
            f"The cheapest fish ever caught was by {
                log['user']} and it's a {
                log['fish']} with length {
                log['length']}cm (top {
                    log['l_percentile']} percentile) and weight {
                        log['weight']}kg (top {
                            log['w_percentile']} percentile) that was worth {
                                log['points']}. bAware")
    else:
        print(
            f"The cheapest fish caught by {user} was a {
                log['fish']} with length {
                log['length']}cm (top {
                log['l_percentile']} percentile) and weight {
                    log['weight']}kg (top {
                        log['w_percentile']} percentile) that was worth {
                            log['points']}. BocchiPossessed")


def cooldown():
    t = datetime.utcnow()
    try:
        with open(f"{user}fishcd.pickle", "rb") as f:
            lastT = pickle.load(f)
        first = False
    except BaseException:
        lastT = t
        first = True

    nextClaimable = lastT + timedelta(seconds=6.5)

    if first or t >= nextClaimable:
        return True
    else:
        return False


def show_time(epoch):
    try:
        return time.strftime('%Y-%m-%d %H:%M', time.gmtime(epoch))
    except BaseException:
        return 'date unavailable'


def show_top(user, topn, fish=None, mode='top'):
    log = load_logs()
    log = log[(log.catch == 1) & (log.points > 0)]
    if user != 'all':
        log = log[log.user == user]
        out_user = user
        emote = 'EZ'
        name = f"{user} hasn't"
    else:
        out_user = 'camp'
        emote = 'CHEER'
        name = "Camp hasn't"
    if fish is not None:
        log = log[log.fish == fish]
        out_fish = fish
    else:
        out_fish = 'creature'
    log_len = len(log)
    if log_len == 0:
        print(f"{name} caught (a) {out_fish} yet. Awkward")
        return
    if log_len < topn:
        blanks = topn - log_len
    else:
        blanks = 0
    if mode == 'bottom':
        log = log.sort_values(by=['points'], ascending=True).head(n=topn)
    else:
        log = log.sort_values(by=['points'], ascending=False).head(n=topn)
    log_len = len(log)
    for i in range(log_len):
        catch = log.iloc[[i]]
        date = show_time(catch['date'].values[0])
        if i == 0:
            print(f"{mode.capitalize()} {topn} {out_fish}(s) for {out_user}! {emote}")
        if user != 'all':
            if catch['length'].isnull().values.any():
                print(
                    f"{
                        i +
                        1}. {
                        catch['fish'].values[0]} | {
                        catch['weight'].values[0]}kg ({
                        catch['w_percentile'].values[0]}p) | {
                        catch['points'].values[0]}lts ({date})")
            else:
                print(
                    f"{
                        i +
                        1}. {
                        catch['fish'].values[0]} | {
                        catch['length'].values[0]}cm ({
                        catch['l_percentile'].values[0]}p) | {
                        catch['weight'].values[0]}kg ({
                            catch['w_percentile'].values[0]}p) | {
                                catch['points'].values[0]}lts ({date})")
        else:
            if catch['length'].isnull().values.any():
                print(
                    f"{
                        i +
                        1}. {
                        catch['user'].values[0]}: {
                        catch['fish'].values[0]} | {
                        catch['weight'].values[0]}kg ({
                        catch['w_percentile'].values[0]}p) | {
                            catch['points'].values[0]}lts ({date})")
            else:
                print(
                    f"{
                        i +
                        1}. {
                        catch['user'].values[0]}: {
                        catch['fish'].values[0]} | {
                        catch['length'].values[0]}cm ({
                        catch['l_percentile'].values[0]}p) | {
                            catch['weight'].values[0]}kg ({
                                catch['w_percentile'].values[0]}p) | {
                                    catch['points'].values[0]}lts ({date})")
    if blanks > 0:
        for i in range(blanks):
            print(f"{log_len + i + 1}. -")


def recent(u='all', fish=None):
    log = load_logs()
    log = log[(log.catch == 1)]
    if u != 'all':
        log = log[log.user == u]
    else:
        u = 'camp'
    if fish is not None:
        log = log[log.fish == fish]
    else:
        fish = 'creature'
    try:
        catch = log.tail(1)
        u = catch['user'].values[0]
        date = show_time(catch['date'].values[0])
        if ((catch['fish'] == 'seaweed') | (catch['fish'] == 'boot')
                | (catch['fish'] == 'boots')).any():
            print(
                f"Latest thing caught by {u}: {
                    catch['fish'].values[0]} ({date})")
        elif catch['length'].isnull().values.any():
            print(
                f"Latest {fish} caught by {u}: {
                    catch['fish'].values[0]} | {
                    catch['weight'].values[0]}kg ({
                    catch['w_percentile'].values[0]}p) | {
                    catch['points'].values[0]}lts ({date})")
        else:
            print(
                f"Latest {fish} caught by {u}: {
                    catch['fish'].values[0]} | {
                    catch['length'].values[0]}cm ({
                    catch['l_percentile'].values[0]}p) | {
                    catch['weight'].values[0]}kg ({
                        catch['w_percentile'].values[0]}p) | {
                            catch['points'].values[0]}lts ({date})")
    except BaseException:
        print(f"They haven't caught a {fish} yet. MyHonestReaction")


def check_daily():
    t = datetime.utcnow()
    next = t + timedelta(days=1)
    next = t.replace(year=next.year, month=next.month,
                     day=next.day, hour=0, minute=0, second=0, microsecond=0)

    try:
        with open(f"{user}_dailybait_lock.pickle", "rb") as f:
            prev = pickle.load(f)
        first = False
    except BaseException:
        prev = t
        first = True

    if first or t > prev:
        items = load_items(user)
        items['dailybait'] = 5
        with open(f"{user}_items.pickle", "wb") as f:
            pickle.dump(items, f)
        with open(f"{user}_dailybait_lock.pickle", "wb") as f:
            pickle.dump(next, f)
        print(f"Five dailybait claimed! Surely something big today...")
    else:
        nn = prev - t
        total_seconds = int(nn.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_string = "{}h{}m{}s".format(hours, minutes, seconds)
        print(
            f"Dailybait already claimed TRUEING Next availability in {time_string} Lazy")


def check_log_size():
    file_name = "fish_catalogue.pickle"
    file_stats = os.stat(file_name)
    print(f'{file_stats.st_size / 1000}KB')


def getBalance():
    try:
        with open(f"{user}.pickle", "rb") as f:
            bankedPoints = pickle.load(f)
    except BaseException:
        bankedPoints = 0
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


def add_nodes(board, n=4, nodes=5):
    all_indices = np.array(np.meshgrid(range(n), range(n))).T.reshape(-1, 2)
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
    return board


def print_mirage_emotes(board):
    mapping = {
        0: 'Mirage0',
        1: 'Mirage1',
        2: 'Mirage2',
        3: 'Mirage3',
        4: 'Mirage4',
        5: 'Mirage5'
    }
    vfunc = np.vectorize(lambda x: mapping[x])
    board = vfunc(board.astype(int))
    for row in board:
        print(' '.join(row))


def check_daily_status():
    time_now = time.time() - 8
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
    time_left = max(round(20 - answer_time, 2), 0)
    reward = round(500 + 10 * time_left**2)
    if time_left >= 15:
        emotes = ['WICKED', 'MILKMANRAVE', 'WAYTOOSMART']
        print(f"{np.random.choice(emotes)} You had {time_left} seconds left. You are awarded {reward} campbucks!!")
    elif time_left >= 10:
        emotes = ['5Head', 'POGGERS', 'AWOO']
        print(f"{np.random.choice(emotes)} You had {time_left} seconds left. You are awarded {reward} campbucks!")
    elif time_left >= 5:
        emotes = ['monkaMath', 'Blindfold', 'forsen']
        print(f"{np.random.choice(emotes)} You had {time_left} seconds left. You are awarded {reward} campbucks.")
    elif time_left >= 1:
        emotes = ['Saved', 'dentt', 'Dentge', 'ApuDent']
        print(f"{np.random.choice(emotes)} You had {time_left} seconds left. You are awarded {reward} campbucks.")
    elif time_left > 0:
        print(
            f"monkaW You had {time_left} seconds left DOPIUM You are awarded {reward} campbucks...")
    else:
        emotes = ['dumbb', 'forsenLaughingAtYou', 'BocchiArrive']
        print(f"{np.random.choice(emotes)} You were {abs(round(20 -
                                                               answer_time, 2))} seconds late. You receive nothing myIQ")
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
        users = pickle.load(f)
    if answer == users[user]:
        check_answer_time()
    else:
        emotes = ['NT', 'idiot.', 'forsenLaughingAtYou', 'WHOLETHIMCOOK']
        print(
            f"Wrong answer {
                np.random.choice(emotes)} The correct answer was {
                users[user]}")
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
        [{"user": user, "solve time": f"{answer_time} seconds", "reward": reward}])
    stats = pd.concat([stats, row], ignore_index=True)
    with open('mirage_stats.pickle', 'wb') as f:
        pickle.dump(stats, f)


for i in range(len(sys.argv)):
    if i < 4:
        sys.argv[i] = sanitize(sys.argv[i]).lower()

if len(sys.argv) >= 4:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2]
    arg3 = sys.argv[3]
    if arg1 in ['top3', 'top5', 'bottom3', 'bottom5']:
        halt = True
        if arg1 in ['bottom3', 'bottom5']:
            mode = 'bottom'
            if arg1 == 'bottom3':
                arg1 = 3
            else:
                arg1 = 5
        elif arg1 in ['top3', 'top5']:
            mode = 'top'
            if arg1 == 'top3':
                arg1 = 3
            else:
                arg1 = 5
        if arg2 == 'fishes':
            arg2 = None
        else:
            arg2 = arg2.replace('_', ' ')
        if arg3 in ['camp', 'all']:
            show_top(user='all', topn=arg1, fish=arg2, mode=mode)
        elif arg3 == 'me':
            show_top(user=user, topn=arg1, fish=arg2, mode=mode)
        else:
            show_top(user=arg3, topn=arg1, fish=arg2, mode=mode)

    elif arg1 in ['logs', 'stats']:
        halt = True
        if arg2 == 'fishes':
            arg2 = None
            aarg2 = False
        elif arg2 == 'casts':
            arg2 = None
            aarg2 = True
        else:
            arg2 = arg2.replace('_', ' ')
            aarg2 = False
        if arg3 in ['camp', 'all']:
            search_db(user='all', fish=arg2, casts=aarg2)
        elif arg3 == 'me':
            search_db(user=user, fish=arg2, casts=aarg2)
        else:
            search_db(user=arg3, fish=arg2, casts=aarg2)

    elif arg1 in ['prob', 'p']:
        if arg2 == 'fishes':
            arg2 = None
        else:
            arg2 = arg2.replace('_', ' ')
        if arg3 == 'camp' or arg3 == 'all':
            obs_prob(user='all', fish=arg2)
        elif arg3 == 'me':
            obs_prob(user=user, fish=arg2)
        else:
            obs_prob(user=arg3, fish=arg2)

    elif arg1 == 'recent':
        halt = True
        if arg2 == 'fishes':
            arg2 = None
        else:
            arg2 = arg2.replace('_', ' ')
        if arg3 in ['camp', 'all']:
            recent(u='all', fish=arg2)
        elif arg3 == 'me':
            recent(u=user, fish=arg2)
        else:
            recent(u=arg3, fish=arg2)

    elif arg1 in ['worst', 'lowest', 'cheapest']:
        halt = True
        if arg2 == 'fishes':
            if arg3 in ['camp', 'all']:
                lowest()
            elif arg3 == 'me':
                lowest(user=user)
            else:
                lowest(user=arg3)
        else:
            if arg3 in ['camp', 'all']:
                lowest(fish=arg2)
            elif arg3 == 'me':
                lowest(user=user, fish=arg2)
            else:
                lowest(user=arg3, fish=arg2)
    elif arg1 == "devreset":
        halt = True
        with open(f"mirage_lock.pickle", "rb") as f:
            users = pickle.load(f)
        with open('mirage_lock.pickle', "wb") as f:
            users[arg2] = datetime.utcnow() - timedelta(days=1)
            pickle.dump(users, f)
            print("Daily reset for debuging! forsenPuke")

if len(sys.argv) >= 2 and not halt:
    arg1 = sys.argv[1]
    if arg1 in ['logs', 'stats']:
        halt = True
        if len(sys.argv) in [2, 3]:
            print(f"logs usage: !fish logs/stats casts/fishes/(fish) camp/(user)")
            print(f"*(fish) is any fish name and (user) is any username")
            print(
                f"for fishes with 2 words or more, replace the space with an underscore!")
    elif arg1 in ['prob', 'p']:
        halt = True
        if len(sys.argv) in [2, 3]:
            print(f"prob usage: !fish prob/p fishes/(fish) camp/(user)")
            print(f"*(fish) is any fish name and (user) is any username")
            print(
                f"for fishes with 2 words or more, replace the space with an underscore!")
    elif arg1 in ['help', 'elp', 'hep']:
        halt = True
        print(f"logs usage: !fish logs/stats casts/fishes/(fish) camp/(user)")
        print(f"prob usage: !fish prob/p fishes/(fish) camp/(user)")
        print(f"*(fish) is any fish name and (user) is any username")
        print(f"for fishes with 2 words or more, replace the space with an underscore!")
    elif arg1 == 'weather':
        halt = True
        print_weather()
    elif arg1 in ['version', 'ver']:
        halt = True
        print(f"fishing ver. 6.00")
    elif arg1 == 'claim':
        halt = True
        check_daily()
    elif arg1 == 'filesize':
        halt = True
        check_log_size()
    elif arg1 == 'mirage':
        halt = True
        print(f"We have moved our field of operation to !mirage")

if not halt or False:
    if cooldown() or disable_sleep == 1:
        fishing()
    else:
        try:
            with open(f"{user}.pickle", "rb") as f:
                bankedPoints = pickle.load(f)
        except BaseException:
            bankedPoints = 0
        penalty = 25
        print(f"You were too hasty. -{penalty} campbucks. Awkward")
        bankedPoints -= int(penalty)

        with open(f"{user}.pickle", "wb") as f:
            pickle.dump(bankedPoints, f)
        t = datetime.utcnow()
        with open(f"{user}fishcd.pickle", "wb") as f:
            pickle.dump(t, f)
