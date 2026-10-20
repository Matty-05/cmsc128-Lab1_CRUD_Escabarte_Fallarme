import argparse
import sqlite3

from app import DATABASE, init_db


DEMO_TASKS = (
    ("Review lecture notes", "2026-10-22T18:00", "Medium", "School"),
    ("Finish lab exercise", "2026-10-24T20:00", "High", "School"),
    ("Buy groceries", "2026-10-25T10:00", "Low", "Personal"),
    ("Plan next week", "2026-10-26T19:00", "Medium", "Others"),
)


def seed_user_tasks(db, username):
    user = db.execute(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    if user is None:
        raise ValueError(f"No user found with username: {username}")

    db.executemany(
        """INSERT INTO tasks (user_id, title, due_date, priority, tag)
           VALUES (?, ?, ?, ?, ?)""",
        ((user[0], *task) for task in DEMO_TASKS),
    )


def main():
    parser = argparse.ArgumentParser(description="Seed tasks for two demo accounts.")
    parser.add_argument("usernames", nargs=2, metavar="USERNAME")
    args = parser.parse_args()

    init_db()
    with sqlite3.connect(DATABASE) as db:
        for username in args.usernames:
            seed_user_tasks(db, username)

    print("Seeded four tasks for each demo account.")


if __name__ == "__main__":
    main()
