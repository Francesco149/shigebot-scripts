from log_utils import log_message, update_markov, open_db
import sqlite3
import argparse


def process_retroactive_file(conn, filepath):
    """Feeds an old 'username: message' text file into the DB."""
    print(f"Ingesting {filepath}...")
    cursor = conn.cursor()
    # Turn off autocommit/journaling temporarily for max speed
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("BEGIN TRANSACTION")

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if ': ' not in line:
                continue
            username, message = line.split(': ', 1)
            username = username.strip()
            message = message.strip()

            if log_message(conn, username, message):
                update_markov(conn, username, message)

    conn.commit()  # Save everything at once at the very end
    cursor.execute("PRAGMA synchronous = NORMAL")
    print("Retroactive ingestion complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Twitch Chat Logger & Markov Generator")
    parser.add_argument('--retro', type=str,
                        help="Path to old logs file for initial ingestion")
    args = parser.parse_args()
    conn = open_db()
    process_retroactive_file(conn, args.retro)
    conn.close()


if __name__ == "__main__":
    main()
