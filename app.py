import os

from datetime import datetime

from dotenv import load_dotenv
from flask import Flask

import auth
import lists
import tasks
from db import DATABASE, SCHEMA, close_db, get_db


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.teardown_appcontext(close_db)

app.register_blueprint(auth.bp)
app.register_blueprint(tasks.bp)
app.register_blueprint(lists.bp)

def init_db():
    with app.app_context():
        db = get_db()
        with open(SCHEMA, "r") as f:
            db.executescript(f.read())
        db.commit()

@app.template_filter("format_due")
def format_due(value):
    try:
        due = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    time = due.strftime("%I:%M %p").lstrip("0")
    return f"{due:%b} {due.day}, {due.year}, {time}"

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
