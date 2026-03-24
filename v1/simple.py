import sys
import os

CMDS = {
    "area": "https://i.imgur.com/sxdISDi.jpeg",
    "camp": "people are always here because the camp never dies",
}

for command in CMDS.keys():
    if sys.argv[1].startswith(os.environ["PREFIX"] + command):
        print(CMDS[command])
        break
