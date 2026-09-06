-- Schema for the To-Do List CRUD app (CMSC 128 Lab 1)
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('Low', 'Med', 'High')),
    tag TEXT NOT NULL CHECK (tag IN ('School', 'Personal', 'Others')),
    is_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);