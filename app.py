import sqlite3 
from datetime import datetime
from pathlib import Path
from flask import Flask, g, render_template, request, redirect, url_for

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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
