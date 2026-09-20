# Library Management Application - Rajesh Bhatt
# Run this setup script before starting login_window.py.
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "library.db"


def initialise_database():
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()

        # 1. Create the three tables when they do not already exist.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                member_id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                username TEXT,
                password_hash TEXT,
                role TEXT NOT NULL DEFAULT 'user'
                    CHECK (role IN ('user', 'librarian'))
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY,
                book_id TEXT NOT NULL,
                member_id TEXT NOT NULL,
                borrowed_date TEXT NOT NULL,
                returned_date TEXT,
                FOREIGN KEY (book_id) REFERENCES books(book_id),
                FOREIGN KEY (member_id) REFERENCES users(member_id)
            )
        """)

        # 2. Upgrade older tables without deleting records.
        columns = {column[1] for column in cursor.execute("PRAGMA table_info(users)")}
        if "username" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
        if "password_hash" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        if "role" not in columns:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
                CHECK (role IN ('user', 'librarian'))
            """)
        book_columns = {column[1] for column in cursor.execute("PRAGMA table_info(books)")}
        if "category" not in book_columns:
            cursor.execute("ALTER TABLE books ADD COLUMN category TEXT")

        # 3. One username per account, and one active loan per physical copy.
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username)
        """)
        duplicates = cursor.execute("""
            SELECT book_id FROM loans
            WHERE returned_date IS NULL
            GROUP BY book_id HAVING COUNT(*) > 1
        """).fetchall()
        if duplicates:
            ids = ", ".join(row[0] for row in duplicates)
            raise ValueError(
                "More than one active loan exists for: " + ids
                + ". Review those loans before running setup again."
            )
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_loans_active_book
            ON loans(book_id) WHERE returned_date IS NULL
        """)

        # 4. Preserve the original sample records; add only if missing.
        if cursor.execute(
            "SELECT 1 FROM books WHERE book_id = ?", ("B001",)
        ).fetchone() is None:
            cursor.execute("""
                INSERT INTO books(book_id, title, author, category)
                VALUES (?, ?, ?, ?)
            """, ("B001", "Python Crash Course", "Eric Matthes", "Programming"))

        if cursor.execute(
            "SELECT 1 FROM users WHERE member_id = ?", ("M001",)
        ).fetchone() is None:
            cursor.execute(
                "INSERT INTO users(member_id, name) VALUES (?, ?)",
                ("M001", "Rajesh Bhatt")
            )

        connection.commit()
        print("Books, Users and Loans tables are ready.")
        print("Active-loan protection is ready.")
        print("Number of books:", cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0])
        print("Users table columns:")
        for column in cursor.execute("PRAGMA table_info(users)"):
            print(column)
        print("Note: sample member M001 has no login credentials. Use Sign Up for login accounts.")
    except (sqlite3.Error, ValueError):
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    print("Database file:", DB_PATH)
    try:
        initialise_database()
    except (sqlite3.Error, ValueError) as error:
        print("Setup failed:", error)
        raise SystemExit(1)
    print("Database connection closed.")
