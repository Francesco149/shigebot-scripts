import log_utils
import sys
import random
import os


def main():
    msg = " ".join(sys.argv[1:])
    p = log_utils.parse_twitch_cmd(msg, "logs")
    if not p:
        return

    conn = log_utils.open_db()
    cursor = conn.cursor()

    base_where = " WHERE 1=1"
    params = []

    # Target User
    if p['user']:
        base_where += " AND LOWER(username) = ?"
        params.append(p['user'])

    # Exclusions (Default + User added - User removed)
    if p['exclude_users']:
        placeholders = ', '.join(['?'] * len(p['exclude_users']))
        base_where += f" AND LOWER(username) NOT IN ({placeholders})"
        params.extend(p['exclude_users'])

    # Command filtering
    if not p['show_commands']:
        base_where += f" AND message NOT LIKE '{os.environ['PREFIX']}%'"

    # Search Queries
    if p['query']:
        if p['mode'] == 'contains':
            base_where += " AND message LIKE ?"
            params.append(f"%{p['query']}%")
        elif p['mode'] == 'starts':
            base_where += " AND message LIKE ?"
            params.append(f"{p['query']}%")
        elif p['mode'] == 'regex':
            base_where += " AND message REGEXP ?"
            params.append(p['query'])

    # Random Multi-Offset Execution
    cursor.execute(f"SELECT COUNT(*) FROM chat_logs{base_where}", params)
    total_rows = cursor.fetchone()[0]

    if total_rows == 0:
        print("No logs found.")
        return

    # Pull N random indices
    limit = min(p['limit'], total_rows)
    offsets = random.sample(range(total_rows), limit)
    results = []

    for offset in offsets:
        cursor.execute(
            f"SELECT timestamp, username, message FROM chat_logs{base_where} LIMIT 1 OFFSET {offset}", params)
        res = cursor.fetchone()
        if res:
            results.append(res)

    # Output newline separated
    for r in sorted(results, key=lambda x: x[0]):
        print(f"{log_utils.format_ts(r[0])} {r[1]}: {r[2]}")

    conn.close()


if __name__ == "__main__":
    main()
