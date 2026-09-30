# CMSC 128 Lab 1 — To-Do List (CRUD)

A simple To-Do List web application implementing the four basic CRUD operations, built for CMSC 128 Laboratory Activity 1.

**Status:** Working

## Authors

- Ralph Ryan T. Escabarte (RalphREE)
- John Matthew N. Fallarme (Matty-05)

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML / CSS / JavaScript |
| Backend | Flask (Python) |
| Database | SQLite |

We chose HTML/CSS/JS + Flask + SQLite because it is the simplest option for
a small app like this, and we are both already comfortable with Python.
Flask is small enough that we write the routing and CRUD logic ourselves,
and SQLite is just a single file, so there is no separate database server
to set up.

## Project Structure

```
.
├── app.py                  # Flask application — routes and CRUD logic
├── requirements.txt        # Python dependencies
├── .gitignore
├── database/
│   └── schema.sql          # SQLite table definitions
├── templates/              # Jinja2 HTML templates
│   ├── _tasks_panel.html   # Task list + filter/sort controls, shared by both pages
│   ├── index.html          # Task list + add-task form
│   └── edit.html           # Edit-task form
└── static/
    ├── css/style.css
    └── js/main.js
```

## Setup

### Requirements

- Python 3.10 or newer
- Git

### Installation

Clone the repository and move into it:

```bash
git clone https://github.com/Matty-05/cmsc128-Lab1_CRUD_Escabarte_Fallarme
cd cmsc128-Lab1_CRUD_Escabarte_Fallarme
```

Create and activate a virtual environment:

```bash
# Windows (Command Prompt / PowerShell)
python -m venv venv
venv\Scripts\activate

# Windows (Git Bash)
python -m venv venv
source venv/Scripts/activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now be prefixed with `(venv)`.

Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the app

```bash
python app.py
```

Then open http://127.0.0.1:5000 in a browser.

The SQLite database file (`database/todo.db`) is created automatically on first run and is **not** tracked by Git — each developer gets their own local copy.

### Notes for collaborators

- Re-run the activate command in every new terminal session.
- `venv/` and `database/todo.db` are gitignored on purpose — don't commit them.
- If you install a new package, add it to `requirements.txt` and commit that file.

## Features

- [x] To-do list interface
- [x] Add task (title, due date and time, priority, tag)
- [x] Edit task
- [x] Delete task with confirmation dialog
- [x] Mark task as done
- [x] Data persistence across restarts
- [x] Undo option when deleting
- [x] Filter and sort

## Data Operations

| Method | Route            | Function         | Description                    |
| ------ | ---------------- | ---------------- | ------------------------------ |
| GET    | `/`              | `index`          | List all tasks                 |
| POST   | `/add`           | `add_task`       | Create a new task              |
| GET    | `/edit/<id>`     | `edit_task_form` | Fetch one task for editing     |
| POST   | `/edit/<id>`     | `edit_task`      | Update an existing task        |
| POST   | `/toggle/<id>`   | `toggle_task`    | Mark a task done or not done   |
| POST   | `/delete/<id>`   | `delete_task`    | Delete a task                  |

A missing `<id>` returns **404**. Every write redirects back to the list,
carrying the current query string so the active filter and sort survive the
action.

### Filter and Sort Parameters

Filtering and sorting are query parameters read by `get_filtered_tasks()`.
They work on both `/` and `/edit/<id>`, since both pages render the same task
list.

| Parameter         | Accepted values                                      | Default      |
| ----------------- | ---------------------------------------------------- | ------------ |
| `filter_tag`      | `School`, `Personal`, `Others` (omit for all)         | all tags     |
| `filter_priority` | `High`, `Medium`, `Low` (omit for all)                | all          |
| `sort_by`         | `created_at`, `due_date`, `title`, `tag`, `priority`  | `created_at` |
| `sort_order`      | `asc`, `desc`                                         | `desc`       |

Both sort parameters are validated against an allowlist before being used —
`sort_by` must be a key of `SORT_COLUMNS` and `sort_order` must be `asc` or
`desc`, otherwise the default is used. This matters because the column and
direction are interpolated into the SQL string rather than passed as bound
parameters. Filter values *are* passed as bound parameters (`?` placeholders).

Priority sorts by rank rather than alphabetically (High > Medium > Low), so
`sort_by=priority&sort_order=desc` puts High-priority tasks first. Titles sort
case-insensitively via `COLLATE NOCASE`.

**Examples**

```
/?filter_tag=School                          School tasks only
/?sort_by=due_date&sort_order=asc            soonest deadline first
/?sort_by=priority&sort_order=desc           High priority first
/?filter_priority=High&sort_by=due_date&sort_order=asc
                                             urgent tasks, soonest first
/edit/3?filter_tag=School                    edit task 3, list filtered
```

## Screenshots

To-Do list main page

![](images/To-Do_List_Page.png)

To-Do list when editing task

![](images/Edit_List.png)

To-Do list with the sort and filter option

![](images/Sort&Filter_Page.png)

Delete Confirmation

![](images/Delete_Confirmation.png)

Undo 

![](images/Undo.png)

## Session Handling

Logging in is handled with Flask's built-in `session`, which is stored in a **signed cookie** in the browser.

**How a login creates the session**

1. `POST /login` looks up the user by username (case-insensitive).
2. `check_password_hash()` compares the typed password with the stored hash. Passwords are never stored or compared in plain text.
3. If the username or password is wrong, the page shows one message, *"Incorrect username or password."*, so it does not reveal which usernames exist.
4. On success, `session.clear()` removes anything left from an earlier session, then `session["user_id"]` is set to the user's id.
5. The user is redirected to the Profile page.

**How the session stays valid**

- The cookie is signed with `SECRET_KEY`, which is loaded from `.env` (see `.env.example`). If anyone edits the cookie, the signature no longer matches and Flask ignores it.
- Because the session lives in the browser's cookie, not in the server's memory, the user **stays logged in after a refresh, back/forward navigation, and a server restart**. After a restart the server still has the same `SECRET_KEY`, so the old cookie is still valid.
- The app fails to start if `SECRET_KEY` is missing (`os.environ["SECRET_KEY"]`), so it never runs with a guessable default key.

**How pages use the session**

- `load_logged_in_user()` (`@app.before_request`) runs before every request and loads the logged-in user's row into `g.user`. The header uses it to show *"Hello, &lt;display name&gt;"*, the current page, and the Log out button.
- `@login_required` protects pages such as `/profile`. If there is no `user_id` in the session, it redirects to `/login`.
- A logged-in user who opens `/login` or `/signup` is redirected to Profile.

**How logout ends the session**

- `POST /logout` calls `session.clear()` and redirects to `/login`. It only accepts POST, so a link or a typed URL cannot log someone out by accident (a GET returns 405).
- `@app.after_request` adds `Cache-Control: no-store` to every page shown while logged in, so the browser does not keep a copy of private pages.
- Some browsers (Brave, Chrome) can still restore the previous page from memory when you press Back. A small script in `_header.html` reloads a page if it was restored this way (`pageshow` with `event.persisted`), so the server checks the session again and redirects to `/login`.

## Password Recovery

### How it works

1. **Request a link.** On the login page, click **Forgot password?** and enter a username or email (`POST /forgot-password`).
2. **Create a token.** If an account matches, the app creates a random token with `secrets.token_urlsafe(32)` and saves a row in the `password_resets` table with:
   - `user_id`: whose password it resets
   - `token_hash`: a SHA-256 hash of the token (the token itself is never stored)
   - `expires_at`: 15 minutes from now
   - `used`: 0 until the link is used
3. **Open the link.** `GET /reset-password/<token>` hashes the token from the URL and looks for a matching row that is not used and not expired. If none is found, the page says the link is invalid, used, or expired, and offers a button to request a new one.
4. **Set a new password.** `POST /reset-password/<token>` checks the token again, then validates the new password (required, at least 8 characters, both fields match).
5. **Save it.** The new password is hashed with `generate_password_hash()` and **replaces** the old hash in `users.password_hash`. All of that user's reset tokens are marked as used, and the session is cleared.
6. **Log in again.** The user is sent to `/login` with a success message. The **new password works and the old password is rejected**, because the old hash no longer exists.

The same message (*"If an account matches, a reset link has been created."*) is shown whether or not the account exists.

### Demo mode (no email)

This app does **not send email**. Instead, the reset link is **shown on the Forgot password page** in a box labelled *"Demo mode"*. A real application would email the link to the account's address instead.

**Security limitations of demo mode**

- **Anyone who knows a username or email can reset that account's password**, because the link is shown to whoever submits the form, not sent to the account owner's inbox. This is acceptable only for a local demo.
- **It reveals which accounts exist.** The confirmation message is the same for every request, but the link only appears when the account exists.
- The other protections still apply: the token is random and cannot be guessed, it works only once, it expires after 15 minutes, and only its hash is stored in the database.

To make this production-ready, the app would email the link (for example with Flask-Mail and SMTP credentials stored in `.env`) and never show it on the page.


