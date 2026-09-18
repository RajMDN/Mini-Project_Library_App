# Library Management Application - Rajesh Bhatt

import os
import sqlite3

# Task 1: Show the current working folder.
print("Current working folder:", os.getcwd())

# Task 2: Connect to the database.
connection = sqlite3.connect("library.db")
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

print("Library database connected successfully.")

try:
    # Task 3: Create the Books table.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id TEXT PRIMARY KEY NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT
        )
    """)

    # Task 4: Create the Users table.
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

    # Task 5: Create the Loans table.
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
    print("Books, Users and Loans tables are ready.")
except sqlite3.Error as error :
    print("Database error:",error)

 # Task 6: Check whether Users already has a username column.
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()

    username_exists = False

    for column in columns:
        if column[1] == "username":
            username_exists = True
            break

    # Add the column only if it is missing.
    if not username_exists:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN username TEXT
        """)
        print("Username column added.")
    else:
        print("Username column already exists.")

     # Task 7: Add the sample book only if B001 is missing.
    cursor.execute(
        "SELECT book_id FROM books WHERE book_id = ?",
        ("B001",)
    )

    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO books (book_id, title, author, category)
            VALUES (?, ?, ?, ?)
        """, (
            "B001",
            "Python Crash Course",
            "Eric Matthes",
            "Programming"
        ))
        print("Sample book added.")
    else:
        print("Book B001 already exists; no duplicate added.")

      # Task 8: Add the sample member only if M001 is missing.
    cursor.execute(
        "SELECT member_id FROM users WHERE member_id = ?",
        ("M001",)
    )

    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO users (member_id, name)
            VALUES (?, ?)
        """, ("M001", "Rajesh Bhatt"))
        print("Sample member added.")
    else:
        print("Member M001 already exists; no duplicate added.")

    # Save the inserted records.
    connection.commit()
# Task 9: Display the books.
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    print("\nBooks in the library:")

    for book in books:
        print(book)

    print("Number of books:", len(books))

    # Task 10: Display the Users table structure.
    cursor.execute("PRAGMA table_info(users)")

    print("\nUsers table columns:")

    for column in cursor.fetchall():
        print(column)

except sqlite3.Error as error:
    connection.rollback()
    print("Database error:", error)

finally:
    connection.close()
    print("\nDatabase connection closed.")