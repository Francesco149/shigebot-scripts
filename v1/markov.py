import log_utils
import random
import sys


def select_weighted_word(choices):
    if not choices:
        return None
    words, weights = zip(*choices)
    return random.choices(words, weights=weights, k=1)[0]


def generate_one(conn, username, start_query, mode):
    cursor = conn.cursor()

    # FIX: If no user, but a query exists, find a user that HAS that word
    if not username and start_query:
        sql = "SELECT DISTINCT username FROM markov_chain WHERE word1 = '__START__' AND word2 = '__START__'"
        params = []
        if mode == 'starts':
            sql += " AND next_word LIKE ?"
            params.append(f"{start_query}%")
        elif mode == 'contains':
            sql += " AND next_word LIKE ?"
            params.append(f"%{start_query}%")
        elif mode == 'regex':
            sql += " AND next_word REGEXP ?"
            params.append(start_query)

        cursor.execute(sql, params)
        valid_users = [r[0] for r in cursor.fetchall()]
        if not valid_users:
            return f"No one has said a word matching '{start_query}'"
        username = random.choice(valid_users)
    elif not username:
        cursor.execute(
            "SELECT username FROM markov_chain ORDER BY RANDOM() LIMIT 1")
        res = cursor.fetchone()
        username = res[0] if res else None

    if not username:
        return "DB Empty"

    # Standard 2nd-order walk logic
    w1, w2 = "__START__", "__START__"
    sentence = []

    if start_query:
        sql = "SELECT next_word, frequency FROM markov_chain WHERE username = ? AND word1 = ? AND word2 = ?"
        params = [username, "__START__", "__START__"]
        if mode == 'starts':
            sql += " AND next_word LIKE ?"
            params.append(f"{start_query}%")
        elif mode == 'contains':
            sql += " AND next_word LIKE ?"
            params.append(f"%{start_query}%")
        elif mode == 'regex':
            sql += " AND next_word REGEXP ?"
            params.append(start_query)

        cursor.execute(sql, params)
        matches = cursor.fetchall()
        if matches:
            first_word = select_weighted_word(matches)
            sentence.append(first_word)
            w1, w2 = w2, first_word
        else:
            return f"{username}: No matches for '{start_query}'"

    for _ in range(30):
        cursor.execute(
            "SELECT next_word, frequency FROM markov_chain WHERE username = ? AND word1 = ? AND word2 = ?", (username, w1, w2))
        choices = cursor.fetchall()
        if not choices:
            break
        next_word = select_weighted_word(choices)
        if next_word == "__END__":
            break
        sentence.append(next_word)
        w1, w2 = w2, next_word

    return f"{username}: " + " ".join(sentence)


def main():
    msg = " ".join(sys.argv[1:])
    p = log_utils.parse_twitch_cmd(msg, "markov")
    if not p:
        return

    conn = log_utils.open_db()
    for _ in range(p['limit']):
        print(generate_one(conn, p['user'], p['query'], p['mode']))
    conn.close()


if __name__ == "__main__":
    main()
