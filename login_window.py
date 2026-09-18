import tkinter as tk
from tkinter import ttk
import sqlite3
import hashlib
import secrets
import uuid
from pathlib import Path


# Task 1: Locate the existing database beside this Python file.
DB_PATH = Path(__file__).resolve().parent / "library.db"
print("Login database path:", DB_PATH)

# Task 2: Convert a password into a hash for safe storage.
def hash_password(password):
    salt = secrets.token_bytes(16)
    iterations = 600_000

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return f"pbkdf2_sha256${iterations}${salt.hex()}${hashed.hex()}"


# Task 3: Check the sign-in fields.
# Database authentication will be added in the next step.
def sign_in():
    username = username_entry.get().strip()
    password = password_entry.get()

    if not username or not password:
        message_label.config(
            text="Please enter your username and password."
        )
    else:
        message_label.config(
            text="Details entered. Database check comes next."
        )


# Task 4: Open the signup window.
def open_signup():
    signup_window = tk.Toplevel(window)
    signup_window.title("Create Library Account")
    signup_window.geometry("440x460")

    # Keep interaction in this window until it is closed.
    signup_window.grab_set()

    signup_frame = ttk.Frame(signup_window, padding=25)
    signup_frame.pack(fill="both", expand=True)

    ttk.Label(
        signup_frame,
        text="Create an Account",
        font=("Arial", 18, "bold")
    ).pack(pady=(0, 15))

    # Full name.
    ttk.Label(signup_frame, text="Full name").pack(anchor="w")
    name_entry = ttk.Entry(signup_frame)
    name_entry.pack(fill="x", pady=(0, 10))

    # Username.
    ttk.Label(signup_frame, text="Username").pack(anchor="w")
    new_username_entry = ttk.Entry(signup_frame)
    new_username_entry.pack(fill="x", pady=(0, 10))

    # Password.
    ttk.Label(signup_frame, text="Password").pack(anchor="w")
    new_password_entry = ttk.Entry(signup_frame, show="*")
    new_password_entry.pack(fill="x", pady=(0, 10))

    # Confirm password.
    ttk.Label(signup_frame, text="Confirm password").pack(anchor="w")
    confirm_password_entry = ttk.Entry(signup_frame, show="*")
    confirm_password_entry.pack(fill="x", pady=(0, 15))

    # Task 5: Validate and save a new user.
    def register():
        name = name_entry.get().strip()
        username = new_username_entry.get().strip()
        password = new_password_entry.get()
        confirmation = confirm_password_entry.get()

        # Stop if any required field is empty.
        if not name or not username or not password or not confirmation:
            signup_message.config(text="Please complete all fields.")
            return

        # Stop if the passwords do not match.
        if password != confirmation:
            signup_message.config(text="The passwords do not match.")
            return

        connection = None

        try:
            # Open the existing database.
            # Do not create a new database if the file is missing.
            connection = sqlite3.connect(
                DB_PATH.as_uri() + "?mode=rw",
                uri=True
            )

            connection.execute("PRAGMA foreign_keys = ON")

            # Enforce unique usernames in the database.
            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                ux_users_username ON users(username)
            """)

            # Check whether the username already exists.
            existing_user = connection.execute(
                "SELECT member_id FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing_user is not None:
                signup_message.config(
                    text="That username is already taken."
                )
                return

            # Generate a member ID and hash the password.
            member_id = "M" + uuid.uuid4().hex
            stored_password = hash_password(password)

            # Insert the account as an ordinary library user.
            connection.execute("""
                INSERT INTO users (
                    member_id,
                    name,
                    username,
                    password_hash,
                    role
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                member_id,
                name,
                username,
                stored_password,
                "user"
            ))

            # Save the new record.
            connection.commit()

            signup_message.config(
                text="Account created and saved successfully."
            )

            # Clear the password fields after successful registration.
            new_password_entry.delete(0, tk.END)
            confirm_password_entry.delete(0, tk.END)

        except sqlite3.Error as error:
            if connection is not None:
                connection.rollback()

            signup_message.config(
                text="Account not saved. Check the terminal for details."
            )
            print("Database file:", DB_PATH)
            print("Database error:", error)

        finally:
            if connection is not None:
                connection.close()

    # Run register() when Create Account is clicked.
    ttk.Button(
        signup_frame,
        text="Create Account",
        command=register
    ).pack()

    signup_message = ttk.Label(
        signup_frame,
        text="",
        wraplength=360
    )
    signup_message.pack(pady=10)

    name_entry.focus_set()


# Task 6: Create the main login window.
window = tk.Tk()
window.title("Library Management System")
window.geometry("440x360")

frame = ttk.Frame(window, padding=25)
frame.pack(fill="both", expand=True)

heading = ttk.Label(
    frame,
    text="Library Sign In",
    font=("Arial", 18, "bold")
)
heading.pack(pady=(0, 15))

# Username field.
ttk.Label(frame, text="Username").pack(anchor="w")
username_entry = ttk.Entry(frame)
username_entry.pack(fill="x", pady=(0, 10))

# Password field.
ttk.Label(frame, text="Password").pack(anchor="w")
password_entry = ttk.Entry(frame, show="*")
password_entry.pack(fill="x", pady=(0, 15))

# Sign In button.
sign_in_button = ttk.Button(
    frame,
    text="Sign In",
    command=sign_in
)
sign_in_button.pack()

# Sign Up button.
signup_button = ttk.Button(
    frame,
    text="Sign Up",
    command=open_signup
)
signup_button.pack(pady=(10, 0))

# Feedback messages.
message_label = ttk.Label(
    frame,
    text="",
    wraplength=360
)
message_label.pack(pady=10)

username_entry.focus_set()

# Keep the window open and respond to clicks and typing.
window.mainloop()


#Code before Correction - Just for reference incase if needed be

