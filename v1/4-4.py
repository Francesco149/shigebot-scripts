import random
import pepe

SET = pepe.get_set()
bets, pulls = (random.sample(SET, len(SET)) for _ in range(2))
pairs = sum(b == p for b, p in zip(bets, pulls))

for bet, pull in zip(bets, pulls):
    print(f"!pepe {bet}")
    print(pull)

print(f"{pairs}/{len(SET)}")
