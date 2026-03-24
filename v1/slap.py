import os
import sys

nick = os.environ['NICK']
target = sys.argv[1] if len(sys.argv) > 1 else "themselves"
print(f"{nick} slaps {target} around a big with a large trout")
