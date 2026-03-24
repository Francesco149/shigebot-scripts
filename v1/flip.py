# originally made by https://twitch.tv/Painketsu
import random
flip = random.randint(0, 100)
if (flip < 50):
    print("Heads HOT")
elif (flip > 50):
    print("Tails THAT")
else:
    print("uh Landed on the side..")
