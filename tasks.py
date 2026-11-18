from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from auth import login_required
from db import get_db
from lists import get_active_list, get_list_bar_data, redirect_to_index


bp = Blueprint("tasks", __name__)

SORT_COLUMNS = {
    "created_at": "created_at",
    "due_date": "due_date",
    "title": "title COLLATE NOCASE",
    "tag": "tag",
    "priority": "CASE priority WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 END",
}

def get_filtered_tasks(active_list):
    db = get_db()
    sort_by = request.args.get("sort_by", "created_at")
    sort_order = request.args.get("sort_order", "desc")

    filter_tag = request.args.get("filter_tag", "")
    filter_priority = request.args.get("filter_priority", "")

    # Personal shows only my tasks outside any list; a shared list shows all of its tasks.
    if active_list is None:
        condition_strings = ["user_id = ? AND list_id IS NULL"]
        parameter_values = [g.user["id"]]
    else:
        condition_strings = ["list_id = ?"]
        parameter_values = [active_list["id"]]

    if filter_tag:
        condition_strings.append("tag = ?")
        parameter_values.append(filter_tag)

    if filter_priority:
        condition_strings.append("priority = ?")
        parameter_values.append(filter_priority)

    where_clause = "WHERE " + " AND ".join(condition_strings)

    if (sort_order != "desc" and sort_order != "asc"):
        sort_order = "desc"

    if sort_by not in SORT_COLUMNS:
        sort_by = "created_at"
    order_expression = SORT_COLUMNS[sort_by]

    # added_by: who created the task, shown in shared lists.
    return db.execute(
        f"""SELECT *, (SELECT display_name FROM users WHERE users.id = tasks.user_id) AS added_by
            FROM tasks {where_clause} ORDER BY {order_expression} {sort_order}""",
        parameter_values,
    ).fetchall()

@bp.route("/")
@login_required
def index():
    # Look up the active list once and share it, instead of each helper querying it again.
    active_list = get_active_list()
    return render_template("index.html", tasks=get_filtered_tasks(active_list), **get_list_bar_data(active_list))

@bp.route("/add", methods=["POST"])
@login_required
def add_task():
    db = get_db()
    title = request.form["title"].strip()
    if not title:
        return redirect_to_index()

    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]
    list_id = request.form.get("list_id", type=int)

    if list_id is not None:
        membership = db.execute(
            "SELECT 1 FROM list_members WHERE list_id = ? AND user_id = ?",
            (list_id, g.user["id"]),
        ).fetchone()
        if membership is None:
            abort(403)

    db.execute(
        "INSERT INTO tasks (user_id, list_id, title, due_date, priority, tag) VALUES (?, ?, ?, ?, ?, ?)",
        (g.user["id"], list_id, title, due_date, priority, tag),
    )
    db.commit()
    return redirect_to_index()

@bp.route("/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    db = get_db()
    cursor = db.execute(
        """UPDATE tasks SET is_done = NOT is_done
           WHERE id = ? AND (user_id = ? OR list_id IN
               (SELECT list_id FROM list_members WHERE user_id = ?))""",
        (task_id, g.user["id"], g.user["id"]),
    )
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for("tasks.index", _anchor=f"task-{task_id}", **request.args))

@bp.route("/edit/<int:task_id>", methods=["GET"])
@login_required
def edit_task_form(task_id):
    db = get_db()
    task = db.execute(
        """SELECT * FROM tasks WHERE id = ? AND (user_id = ? OR list_id IN
               (SELECT list_id FROM list_members WHERE user_id = ?))""",
        (task_id, g.user["id"], g.user["id"]),
    ).fetchone()
    if task is None:
        abort(404)
    active_list = get_active_list()
    return render_template("edit.html", task=task, tasks=get_filtered_tasks(active_list), **get_list_bar_data(active_list))

@bp.route("/edit/<int:task_id>", methods=["POST"])
@login_required
def edit_task(task_id):
    db = get_db()
    title = request.form["title"].strip()
    if not title:
        return redirect(url_for("tasks.edit_task_form", task_id=task_id, _anchor=f"task-{task_id}", **request.args))

    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]

    cursor = db.execute(
        """UPDATE tasks SET title = ?, due_date = ?, priority = ?, tag = ?
           WHERE id = ? AND (user_id = ? OR list_id IN
               (SELECT list_id FROM list_members WHERE user_id = ?))""",
        (title, due_date, priority, tag, task_id, g.user["id"], g.user["id"]),
    )
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect(url_for("tasks.index", _anchor=f"task-{task_id}", **request.args))

@bp.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    db = get_db()
    cursor = db.execute(
        """DELETE FROM tasks WHERE id = ? AND (user_id = ? OR list_id IN
               (SELECT list_id FROM list_members WHERE user_id = ?))""",
        (task_id, g.user["id"], g.user["id"]),
    )
    if cursor.rowcount == 0:
        abort(404)
    db.commit()
    return redirect_to_index()
