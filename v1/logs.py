import sys
import os
from log_utils import open_db, log_message, update_markov


def main():
    conn = open_db()

    # Handle Incremental per-message processing
    username = os.environ.get('NICK')
    message = " ".join(sys.argv[1:])

    if username and message:
        if log_message(conn, username, message):
            # message was not duplicate
            update_markov(conn, username, message)

    conn.close()


if __name__ == "__main__":
    main()
