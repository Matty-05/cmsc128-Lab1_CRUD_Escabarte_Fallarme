import os
import sqlite3
import hashlib
import secrets

from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from validators import is_valid_email, is_valid_username, password_error


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "todo.db"
SCHEMA = BASE_DIR / "database" / "schema.sql"
SORT_COLUMNS = {
    "created_at": "created_at",
    "due_date": "due_date",
    "title": "title COLLATE NOCASE",
    "tag": "tag",
    "priority": "CASE priority WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 END",
}
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    connection = g.pop("db", None)

    if connection is not None:
        connection.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open(SCHEMA, "r") as f:
            db.executescript(f.read())
        db.commit()

@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if g.user:
            return redirect(url_for("profile_form"))
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("login.html", error="Enter your username and password.", username=username)

    user = get_db().execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Incorrect username or password.", username=username)

    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("profile_form"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    identifier = request.form.get("identifier", "").strip()
    if not identifier:
        return render_template("forgot_password.html", error="Enter your username or email.")

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE OR email = ?",
        (identifier, identifier.lower()),
    ).fetchone()

    reset_link = None
    if user is not None:
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(minutes=RESET_TOKEN_MINUTES)).isoformat()
        db.execute(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user["id"], hash_token(token), expires_at),
        )
        db.commit()
        reset_link = url_for("reset_password", token=token, _external=True)

    return render_template("forgot_password.html", submitted=True, reset_link=reset_link)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    return "Reset page coming soon"

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view

RESET_TOKEN_MINUTES = 15

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

def redirect_to_index():
    return redirect(url_for("index", **request.args))

@app.template_filter("format_due")
def format_due(value):
    try:
        due = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    time = due.strftime("%I:%M %p").lstrip("0")
    return f"{due:%b} {due.day}, {due.year}, {time}"

def get_filtered_tasks():
    db = get_db()
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    filter_tag = request.args.get("filter_tag", "")
    filter_priority = request.args.get("filter_priority", "")

    condition_strings = []
    parameter_values = []

    if filter_tag: 
        condition_strings.append("tag = ?")
        parameter_values.append(filter_tag)

    if filter_priority:
        condition_strings.append("priority = ?")
        parameter_values.append(filter_priority)

    where_clause = "WHERE " + " AND ".join(condition_strings) if condition_strings else ""
    
    if (sort_order != "desc" and sort_order != "asc"):
        sort_order = "desc"

    if sort_by not in SORT_COLUMNS:
        sort_by = "created_at"
    order_expression = SORT_COLUMNS[sort_by]

    return db.execute(f"SELECT * FROM tasks {where_clause} ORDER BY {order_expression} {sort_order}", parameter_values).fetchall()

@app.route("/")
def index():
    return render_template("index.html", tasks=get_filtered_tasks())

@app.route("/add", methods=["POST"])
def add_task():
    db = get_db()
    title = request.form["title"].strip()
    if not title:
        return redirect_to_index()

    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]

    db.execute("INSERT INTO tasks (title, due_date, priority, tag) VALUES (?, ?, ?, ?)", (title, due_date, priority, tag))
    db.commit()
    return redirect_to_index()

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET is_done = NOT is_done WHERE id = ?", (task_id,))
    db.commit()
    return redirect_to_index()

@app.route("/edit/<int:task_id>", methods=["GET"])
def edit_task_form(task_id):
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        abort(404)
    return render_template("edit.html", task=task, tasks=get_filtered_tasks())

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    db = get_db()
    title = request.form["title"].strip()
    if not title:
        return redirect(url_for("edit_task_form", task_id=task_id, **request.args))

    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]

    db.execute("UPDATE tasks SET title = ?, due_date = ?, priority = ?, tag = ? WHERE id = ?", (title, due_date, priority, tag, task_id))
    db.commit()
    return redirect_to_index()

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect_to_index()


# Registration:

@app.route("/signup", methods=["GET"])
def register_form():
    if g.user:
        return redirect(url_for("profile_form"))
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def register():
    db = get_db()
    display_name = request.form.get("display_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # errors is a dict of field name -> message; the templates read errors.<field>
    errors = validate_required({
        "display_name": display_name,
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": confirm_password,
    })

    if "username" not in errors and not is_valid_username(username):
        errors["username"] = "Use 3-30 characters: letters, numbers, underscores only."

    if "email" not in errors and not is_valid_email(email):
        errors["email"] = "Please enter a valid email address."

    if "password" not in errors:
        message = password_error(password)
        if message:
            errors["password"] = message

    if "password" not in errors and "confirm_password" not in errors and password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    if "username" not in errors:
        taken = db.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if taken:
            errors["username"] = "That username is already taken."

    if "email" not in errors:
        taken = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if taken:
            errors["email"] = "That email is already registered."

    if errors:
        return render_template("signup.html", errors=errors, form=request.form)

    try:
        cursor = db.execute(
            "INSERT INTO users (username, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
            (username, email, display_name, generate_password_hash(password))
        )
        db.commit()
    except sqlite3.IntegrityError:
        # Backstop for a race where two registrations land at the same instant.
        return render_template(
            "signup.html",
            errors={"username": "That username or email is already taken."},
            form=request.form
        )

    session.clear()
    session["user_id"] = cursor.lastrowid
    flash("Your account was created. Welcome!")
    return redirect(url_for("profile_form"))


# Profile:

@app.route("/profile", methods=["GET"])
@login_required
def profile_form():
    return render_template("profile.html")

@app.route("/profile", methods=["POST"])
@login_required
def update_profile():
    db = get_db()
    action = request.form.get("action")

    if action == "details":
        display_name = request.form.get("display_name", "").strip()
        username = request.form.get("username", "").strip()

        errors = validate_required({
            "display_name": display_name,
            "username": username,
        })

        if "username" not in errors and not is_valid_username(username):
            errors["username"] = "Use 3-30 characters: letters, numbers, underscores only."

        if "username" not in errors:
            # Ignore the user's own row so keeping the same username is allowed.
            taken = db.execute(
                "SELECT id FROM users WHERE username = ? COLLATE NOCASE AND id != ?",
                (username, g.user["id"])
            ).fetchone()
            if taken:
                errors["username"] = "That username is already taken."

        if errors:
            return render_template("profile.html", errors=errors, form=request.form)

        db.execute(
            "UPDATE users SET display_name = ?, username = ? WHERE id = ?",
            (display_name, username, g.user["id"])
        )
        db.commit()
        flash("Account details updated.")
        return redirect(url_for("profile_form"))

    if action == "password":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_required({
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": confirm_password,
        })

        if "current_password" not in errors and not check_password_hash(g.user["password_hash"], current_password):
            errors["current_password"] = "Current password is incorrect."

        if "new_password" not in errors:
            message = password_error(new_password)
            if message:
                errors["new_password"] = message

        if "new_password" not in errors and "confirm_password" not in errors and new_password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            return render_template("profile.html", errors=errors, form=request.form)

        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), g.user["id"])
        )
        db.commit()
        flash("Password updated.")
        return redirect(url_for("profile_form"))

    abort(400)  # unknown or missing form action

if __name__ == "__main__":
    init_db()
    app.run(debug=True)