# CMSC 128 Lab 1 — To-Do List (CRUD)

A simple To-Do List web application implementing the four basic CRUD operations, built for CMSC 128 Laboratory Activity 1.

**Status:** project setup complete. Application code is not yet implemented.

## Authors

- Ralph Ryan T. Escabarte (RalphRE)
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
│   ├── base.html           # Shared page layout
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
git clone <repository-url>
cd <repository-name>
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

### To Be Implemented

- [ ] To-do list interface
- [ ] Add task (title, due date and time, priority, tag)
- [ ] Edit task
- [ ] Delete task with confirmation dialog
- [ ] Mark task as done
- [ ] Data persistence across restarts
- [ ] Undo option when deleting
- [ ] Filter and sort
- [ ] Built-in calendar view

## Data Operations

To Be Implemented

## Screenshots

To Be Implemented

