import os
import sqlite3
from pathlib import Path
from typing import Iterator, Optional
from contextlib import contextmanager
from datetime import datetime

# Database path can be overridden via ENROLL_DB_PATH
_DEFAULT_DB_PATH = Path(__file__).resolve().parent / "enrollment.db"
_DB_PATH = Path(os.environ.get("ENROLL_DB_PATH", str(_DEFAULT_DB_PATH)))


def _enable_foreign_keys(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON;")


def _migrate_schema(connection: sqlite3.Connection) -> None:
    # Create tables if they don't exist
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TEXT NOT NULL,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        """
    )


def get_db_path() -> Path:
    return _DB_PATH


@contextmanager
def get_connection(readonly: bool = False) -> Iterator[sqlite3.Connection]:
    db_path = get_db_path()
    if readonly:
        uri = f"file:{db_path}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    _enable_foreign_keys(connection)
    try:
        yield connection
        if not readonly:
            connection.commit()
    finally:
        connection.close()


def ensure_initialized() -> None:
    with get_connection() as connection:
        _migrate_schema(connection)


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
