import sqlite3
import os

DATABASE_FILE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "jobs.db"))


def get_db():
    """Open a database connection and return rows by column name."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the tables if they do not already exist."""
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                applied_date TEXT NOT NULL,
                status TEXT NOT NULL,
                location TEXT,
                salary REAL,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS followups (
                followup_id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER NOT NULL,
                followup_date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (application_id)
                    REFERENCES applications(application_id)
                    ON DELETE CASCADE
            )
        """)
