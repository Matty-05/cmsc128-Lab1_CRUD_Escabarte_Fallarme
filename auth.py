import sqlite3
import hashlib
import secrets

from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from validators import is_valid_email, is_valid_username, password_error, validate_required


bp = Blueprint("auth", __name__)

RESET_TOKEN_MINUTES = 15

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

@bp.after_app_request
def prevent_caching_logged_in_pages(response):
    if g.get("user"):
        response.headers["Cache-Control"] = "no-store"
    return response

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped_view

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if g.user:
            return redirect(url_for("tasks.index"))
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
    return redirect(url_for("tasks.index"))

@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# Password reset:

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def find_valid_reset(token):
    return get_db().execute(
        "SELECT * FROM password_resets WHERE token_hash = ? AND used = 0 AND expires_at > ?",
        (hash_token(token), datetime.now().isoformat()),
    ).fetchone()

@bp.route("/forgot-password", methods=["GET", "POST"])
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
        reset_link = url_for("auth.reset_password", token=token, _external=True)

    return render_template("forgot_password.html", submitted=True, reset_link=reset_link)

@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset = find_valid_reset(token)
    if reset is None:
        return render_template("reset_password.html", invalid=True, token=token)

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    errors = validate_required({"new_password": new_password, "confirm_password": confirm_password})
    if "new_password" not in errors:
        message = password_error(new_password)
        if message:
            errors["new_password"] = message
    if not errors and new_password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."
    if errors:
        return render_template("reset_password.html", token=token, errors=errors)

    db = get_db()
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), reset["user_id"]),
    )
    db.execute("UPDATE password_resets SET used = 1 WHERE user_id = ?", (reset["user_id"],))
    db.commit()

    session.clear()
    flash("Password reset. Log in with your new password.")
    return redirect(url_for("auth.login"))


# Registration:

@bp.route("/signup", methods=["GET"])
def register_form():
    if g.user:
        return redirect(url_for("tasks.index"))
    return render_template("signup.html")

@bp.route("/signup", methods=["POST"])
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
    return redirect(url_for("tasks.index"))


# Profile:

@bp.route("/profile", methods=["GET"])
@login_required
def profile_form():
    return render_template("profile.html")

@bp.route("/profile", methods=["POST"])
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
        return redirect(url_for("auth.profile_form"))

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
        return redirect(url_for("auth.profile_form"))

    abort(400)  # unknown or missing form action
