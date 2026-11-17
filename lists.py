from flask import Blueprint, abort, flash, g, redirect, request, session, url_for

from auth import login_required
from db import get_db


bp = Blueprint("lists", __name__)

def redirect_to_index():
    return redirect(url_for("tasks.index", **request.args))

# The list saved in the session, but only if I am still a member. None means Personal.
def get_active_list():
    list_id = session.get("list_id")
    if list_id is None:
        return None
    return get_db().execute(
        """SELECT lists.* FROM lists
           JOIN list_members ON list_members.list_id = lists.id
           WHERE lists.id = ? AND list_members.user_id = ?""",
        (list_id, g.user["id"]),
    ).fetchone()

# Every list I own or was added to, with the owner's name for the switcher buttons.
def get_my_lists():
    return get_db().execute(
        """SELECT lists.*, users.display_name AS owner_name FROM lists
           JOIN list_members ON list_members.list_id = lists.id
           JOIN users ON users.id = lists.owner_id
           WHERE list_members.user_id = ?
           ORDER BY lists.id""",
        (g.user["id"],),
    ).fetchall()

# Everything _list_bar.html needs. Used by the To-Do List and Edit pages.
def get_list_bar_data():
    active_list = get_active_list()
    members = []
    if active_list is not None:
        members = get_db().execute(
            """SELECT users.display_name FROM list_members
               JOIN users ON users.id = list_members.user_id
               WHERE list_members.list_id = ?
               ORDER BY users.display_name""",
            (active_list["id"],),
        ).fetchall()
    return {"lists": get_my_lists(), "active_list": active_list, "members": members}

@bp.route("/lists", methods=["POST"])
@login_required
def create_list():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Enter a list name.", "error")
        return redirect_to_index()

    db = get_db()
    cursor = db.execute(
        "INSERT INTO lists (owner_id, name) VALUES (?, ?)",
        (g.user["id"], name),
    )
    db.execute(
        "INSERT INTO list_members (list_id, user_id) VALUES (?, ?)",
        (cursor.lastrowid, g.user["id"]),
    )
    db.commit()
    # Open the new list right away so the user sees what they just made.
    session["list_id"] = cursor.lastrowid
    return redirect_to_index()


@bp.route("/lists/switch", methods=["POST"])
@login_required
def switch_list():
    # An empty value means Personal. Any other id must be a list I am a member of.
    list_id = request.form.get("list_id", type=int)
    if list_id is not None:
        membership = get_db().execute(
            "SELECT 1 FROM list_members WHERE list_id = ? AND user_id = ?",
            (list_id, g.user["id"]),
        ).fetchone()
        if membership is None:
            abort(404)
    session["list_id"] = list_id
    return redirect_to_index()


@bp.route("/lists/<int:list_id>/members", methods=["POST"])
@login_required
def add_list_member(list_id):
    identifier = request.form.get("identifier", "").strip()
    db = get_db()
    owned_list = db.execute(
        "SELECT 1 FROM lists WHERE id = ? AND owner_id = ?",
        (list_id, g.user["id"]),
    ).fetchone()
    if owned_list is None:
        abort(404)

    user = db.execute(
        "SELECT id, display_name FROM users WHERE username = ? COLLATE NOCASE OR email = ?",
        (identifier, identifier.lower()),
    ).fetchone()
    if user is None:
        flash("No account matches that username or email.", "error")
        return redirect_to_index()

    cursor = db.execute(
        "INSERT OR IGNORE INTO list_members (list_id, user_id) VALUES (?, ?)",
        (list_id, user["id"]),
    )
    db.commit()
    if cursor.rowcount == 0:
        flash(f"{user['display_name']} is already in this list.", "error")
    else:
        flash(f"Added {user['display_name']} to this list.", "success")
    return redirect_to_index()
