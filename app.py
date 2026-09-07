import sqlite3 
from pathlib import Path
from flask import Flask, g, render_template, request, redirect, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "todo.db"
SCHEMA = BASE_DIR / "database" / "schema.sql"
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

@app.route("/")
def index():
    db = get_db()
    tasks = db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return "<br>".join([f"{row['id']} | {row['title']} | {row['priority']} | done={row['is_done']}" for row in tasks])

@app.route("/add", methods=["POST"])
def add_task():
    db = get_db()
    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]

    db.execute("INSERT INTO tasks (title, due_date, priority, tag) VALUES (?, ?, ?, ?)", (title, due_date, priority, tag))
    db.commit()
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET is_done = NOT is_done WHERE id = ?", (task_id,))
    db.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET"])
def edit_task_form(task_id):
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return f"{task['title']} - {task['priority']}"

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    db = get_db()
    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    tag = request.form["tag"]

    db.execute("UPDATE tasks SET title = ?, due_date = ?, priority = ?, tag = ? WHERE id = ?", (title, due_date, priority, tag, task_id))
    db.commit()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
