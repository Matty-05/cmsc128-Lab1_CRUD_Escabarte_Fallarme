import argparse
import sqlite3
from datetime import datetime, timedelta

from app import DATABASE, init_db


# One set per demo account, so each account's list looks different in the demo.
# Each task: (title, days from today, hour, priority, tag)
DEMO_TASK_SETS = (
    (
        ("Review lecture notes", 1, 18, "Medium", "School"),
        ("Finish lab exercise", 3, 20, "High", "School"),
        ("Buy groceries", 4, 10, "Low", "Personal"),
        ("Plan next week", 5, 19, "Medium", "Others"),
    ),
    (
        ("Submit math problem set", 2, 23, "High", "School"),
        ("Read chapter 5", 3, 21, "Medium", "School"),
        ("Call home", 1, 19, "Low", "Personal"),
        ("Fix bike tire", 6, 9, "Low", "Others"),
    ),
    (
        ("Prepare quiz reviewer", 2, 17, "High", "School"),
        ("Return library books", 4, 15, "Medium", "Others"),
        ("Pay phone bill", 3, 12, "High", "Personal"),
        ("Clean room", 5, 10, "Low", "Personal"),
    ),
    (
        ("Draft research outline", 3, 22, "High", "School"),
        ("Practice presentation", 2, 20, "Medium", "School"),
        ("Go for a run", 1, 6, "Low", "Personal"),
        ("Renew student ID", 7, 13, "Medium", "Others"),
    ),
)


SHARED_LIST_NAME = "Demo Group List"
SHARED_TASK = ("Finish group project slides", 4, 21, "High", "School")


def due_date(days, hour):
    """Dates are relative to today, so the demo tasks are never already overdue."""
    due = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days)
    return due.strftime("%Y-%m-%dT%H:%M")


def seed_user_tasks(db, username, tasks):
    user = db.execute(
        "SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    if user is None:
        raise ValueError(f"No user found with username: {username}")

    added = 0
    for title, days, hour, priority, tag in tasks:
        # Skip a task this user already has, so running the seeder twice adds nothing.
        exists = db.execute(
            "SELECT 1 FROM tasks WHERE user_id = ? AND title = ? AND list_id IS NULL",
            (user[0], title),
        ).fetchone()
        if exists:
            continue
        db.execute(
            """INSERT INTO tasks (user_id, title, due_date, priority, tag)
               VALUES (?, ?, ?, ?, ?)""",
            (user[0], title, due_date(days, hour), priority, tag),
        )
        added += 1
    return added


def seed_shared_list(db, usernames):
    """One shared list owned by the first user, with every given user as a member."""
    user_ids = [
        db.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (name,)).fetchone()[0]
        for name in usernames
    ]
    owner_id = user_ids[0]

    shared_list = db.execute(
        "SELECT id FROM lists WHERE owner_id = ? AND name = ?", (owner_id, SHARED_LIST_NAME)
    ).fetchone()
    if shared_list is None:
        list_id = db.execute(
            "INSERT INTO lists (owner_id, name) VALUES (?, ?)", (owner_id, SHARED_LIST_NAME)
        ).lastrowid
    else:
        list_id = shared_list[0]

    # The owner is a member too, the same as when a list is created in the app.
    db.executemany(
        "INSERT OR IGNORE INTO list_members (list_id, user_id) VALUES (?, ?)",
        ((list_id, user_id) for user_id in user_ids),
    )

    title, days, hour, priority, tag = SHARED_TASK
    exists = db.execute(
        "SELECT 1 FROM tasks WHERE list_id = ? AND title = ?", (list_id, title)
    ).fetchone()
    if not exists:
        db.execute(
            """INSERT INTO tasks (user_id, list_id, title, due_date, priority, tag)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (owner_id, list_id, title, due_date(days, hour), priority, tag),
        )


def main():
    parser = argparse.ArgumentParser(description="Seed personal tasks for demo accounts.")
    parser.add_argument("usernames", nargs="+", metavar="USERNAME")
    args = parser.parse_args()

    init_db()
    with sqlite3.connect(DATABASE) as db:
        for index, username in enumerate(args.usernames):
            tasks = DEMO_TASK_SETS[index % len(DEMO_TASK_SETS)]
            added = seed_user_tasks(db, username, tasks)
            print(f"{username}: added {added} task(s)")

        seed_shared_list(db, args.usernames)
        print(f"{SHARED_LIST_NAME}: shared by {', '.join(args.usernames)}")


if __name__ == "__main__":
    main()
