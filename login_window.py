import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import secrets
import uuid
from pathlib import Path
from datetime import date, timedelta



# Task 1: Locate the existing database beside this Python file.
DB_PATH = Path(__file__).resolve().parent / "library.db"
print("Login database path:", DB_PATH)

# Set only after successful sign-in; cleared on sign-out.
current_member_id = None

# Task 2: Create and check password hashes.
def hash_password(password):
    # Each account gets its own random salt.
    salt = secrets.token_bytes(16)
    iterations = 600_000
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hashed.hex()}"


def verify_password(entered_password, stored_password):
    # Older sample members may not have login credentials.
    if not isinstance(stored_password, str) or not stored_password:
        return False

    try:
        method, iterations, salt, saved_hash = stored_password.split("$")
        if method != "pbkdf2_sha256":
            return False

        iterations = int(iterations)
        # Reject damaged settings instead of running an excessive calculation.
        if not 1 <= iterations <= 2_000_000:
            return False

        entered_hash = hashlib.pbkdf2_hmac(
            "sha256",
            entered_password.encode("utf-8"),
            bytes.fromhex(salt),
            iterations
        )
        return secrets.compare_digest(
            entered_hash, bytes.fromhex(saved_hash)
        )
    except (ValueError, TypeError, OverflowError):
        return False


# Task 3: Check the credentials saved in the Users table.
def sign_in():
    global current_member_id
    username = username_entry.get().strip()
    password = password_entry.get()

    if not username or not password:
        message_label.config(
            text="Please enter your username and password."
        )
        return

    connection = None
    try:
        # Open only the existing database beside this file.
        connection = sqlite3.connect(
            DB_PATH.as_uri() + "?mode=rw", uri=True
        )
        connection.execute("PRAGMA foreign_keys = ON")

        # The question mark safely supplies the entered username.
        account = connection.execute("""
            SELECT member_id, name, password_hash, role
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

    except sqlite3.Error as error:
        message_label.config(
            text="Cannot check your account. See the terminal for details."
        )
        print("Database file:", DB_PATH)
        print("Database error:", error)
        return
    finally:
        if connection is not None:
            connection.close()

    if account is None:
        message_label.config(text="Incorrect username or password.")
        return

    member_id, name, stored_password, role = account
    if not verify_password(password, stored_password):
        message_label.config(text="Incorrect username or password.")
        return

    if role not in ("user", "librarian"):
        message_label.config(text="Your account has an unrecognised role.")
        return

    password_entry.delete(0, tk.END)
    message_label.config(text="")
    current_member_id = member_id
    open_welcome(member_id, name, role)


# NULL returned_date means this loan is still active.
def get_catalogue():

    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        return connection.execute("""
            SELECT b.book_id, b.title, b.author, COALESCE(b.category, ''),
                   CASE WHEN EXISTS (
                       SELECT 1 FROM loans AS l
                       WHERE l.book_id = b.book_id
                         AND l.returned_date IS NULL
                   ) THEN 'Borrowed' ELSE 'Available' END
            FROM books AS b
    
            ORDER BY b.title COLLATE NOCASE ASC, b.book_id;
        """).fetchall()
    finally:
        connection.close()


def borrow_book(book_id):
    # Use the authenticated session, never a member ID typed into a form.
    if current_member_id is None:
        raise PermissionError("Please sign in as a library user.")
    if not book_id:
        raise ValueError("Please select a book first.")

    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        # Only one writer can check availability and create a loan at a time.
        connection.execute("BEGIN IMMEDIATE")
        account = connection.execute(
            "SELECT role FROM users WHERE member_id = ?",
            (current_member_id,)
        ).fetchone()
        if account is None or account[0] != "user":
            raise PermissionError("Only library user accounts can borrow books.")

        book = connection.execute(
            "SELECT title FROM books WHERE book_id = ?", (book_id,)
        ).fetchone()
        if book is None:
            raise ValueError("This book no longer exists. Refresh the catalogue.")

        active_loan = connection.execute("""
            SELECT loan_id FROM loans
            WHERE book_id = ? AND returned_date IS NULL
        """, (book_id,)).fetchone()
        if active_loan is not None:
            raise ValueError("This copy is already borrowed. Select another copy.")

        # This also protects the rule when other code writes to the table.
        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_loans_active_book
            ON loans(book_id) WHERE returned_date IS NULL
        """)
        cursor = connection.execute("""
            INSERT INTO loans
                (book_id, member_id, borrowed_date, returned_date)
            VALUES (?, ?, ?, NULL)
        """, (book_id, current_member_id, date.today().isoformat()))
        loan_id = cursor.lastrowid
        connection.commit()
        return loan_id
    except (sqlite3.Error, ValueError, PermissionError):
        connection.rollback()
        raise
    finally:
        connection.close()


# Finish the signed-in user's active loan while keeping its history.
def return_book(book_id, expected_loan_id=None):
    if current_member_id is None:
        raise PermissionError("Please sign in as a library user.")
    if not book_id:
        raise ValueError("Please select a book first.")

    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        account = connection.execute(
            "SELECT role FROM users WHERE member_id = ?",
            (current_member_id,)
        ).fetchone()
        if account is None or account[0] != "user":
            raise PermissionError("Only library user accounts can return their books.")

        active_loan = connection.execute("""
            SELECT loan_id, member_id FROM loans
            WHERE book_id = ? AND returned_date IS NULL
        """, (book_id,)).fetchone()
        if active_loan is None:
            raise ValueError("This copy has no active loan to return.")
        loan_id, borrower_id = active_loan
        if expected_loan_id is not None and loan_id != expected_loan_id:
            raise ValueError("This loan has changed. Refresh the list and try again.")
        if borrower_id != current_member_id:
            raise PermissionError("You can only return a book borrowed by your account.")

        # Update this loan, rather than deleting it or changing the Books table.
        cursor = connection.execute("""
            UPDATE loans SET returned_date = ?
            WHERE loan_id = ? AND member_id = ? AND returned_date IS NULL
        """, (date.today().isoformat(), loan_id, current_member_id))
        if cursor.rowcount != 1:
            raise ValueError("The loan has changed. Refresh and try again.")
        connection.commit()
        return loan_id
    except (sqlite3.Error, ValueError, PermissionError):
        connection.rollback()
        raise
    finally:
        connection.close()


# Due dates are calculated from the saved borrowing date: no new column needed.
def loan_due_details(borrowed_date, today=None):
    if today is None:
        today = date.today()
    try:
        due = date.fromisoformat(borrowed_date) + timedelta(days=7)
    except (ValueError, TypeError, OverflowError):
        return "", "Check borrowing date"
    if today > due:
        status = "Overdue"
    elif today == due:
        status = "Due today"
    else:
        status = "On loan"
    return due.isoformat(), status


def get_active_loans(all_users=False):
    if current_member_id is None:
        raise PermissionError("Please sign in first.")
    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        account = connection.execute(
            "SELECT role FROM users WHERE member_id = ?", (current_member_id,)
        ).fetchone()
        if account is None or account[0] not in ("user", "librarian"):
            raise PermissionError("Your account cannot view loans.")
        if all_users and account[0] != "librarian":
            raise PermissionError("Only the librarian can view everyone's loans.")

        sql = """
            SELECT l.loan_id, b.book_id, b.title, u.name, u.username,
                   l.borrowed_date
            FROM loans AS l
            JOIN books AS b ON b.book_id = l.book_id
            JOIN users AS u ON u.member_id = l.member_id
            WHERE l.returned_date IS NULL
        """
        parameters = ()
        if not all_users:
            sql += " AND l.member_id = ?"
            parameters = (current_member_id,)
        sql += " ORDER BY l.borrowed_date, l.loan_id"
        records = connection.execute(sql, parameters).fetchall()
        return [tuple(row) + loan_due_details(row[5]) for row in records]
    finally:
        connection.close()


def show_loans(parent_window, all_users=False):
    # Check access before opening the screen or displaying any records.
    try:
        get_active_loans(all_users)
    except (PermissionError, sqlite3.Error) as error:
        messagebox.showerror("Unable to Load Loans", str(error), parent=parent_window)
        return

    loans_window = tk.Toplevel(parent_window)
    heading = "Current Loans" if all_users else "My Borrowed Books"
    loans_window.title(heading)
    loans_window.geometry("1100x460" if all_users else "850x460")
    content = ttk.Frame(loans_window, padding=20)
    content.pack(fill="both", expand=True)
    ttk.Label(content, text=heading, font=("Arial", 18, "bold")).pack(pady=(0, 10))
    ttk.Label(
        content, text="Borrowing period: 7 days. Dates are shown as YYYY-MM-DD."
    ).pack(pady=(0, 10))
    controls = ttk.Frame(content)
    controls.pack(side="bottom", fill="x", pady=(10, 0))
    summary = ttk.Label(controls, text="", wraplength=800)
    summary.pack(pady=5)
    table_frame = ttk.Frame(content)
    table_frame.pack(fill="both", expand=True)

    columns = ["book_id", "title"]
    headings = ["Book ID", "Title"]
    widths = [100, 240]
    if all_users:
        columns += ["borrower", "username"]
        headings += ["Borrower", "Username"]
        widths += [160, 120]
    columns += ["borrowed", "due", "status"]
    headings += ["Borrowed date", "Due date", "Status"]
    widths += [120, 120, 160]
    table = ttk.Treeview(
        table_frame, columns=columns, show="headings", selectmode="browse"
    )
    for column, label, width in zip(columns, headings, widths):
        table.heading(column, text=label)
        table.column(column, width=width, minwidth=70)
    table.tag_configure("Overdue", foreground="#a32020")
    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(side="left", fill="both", expand=True)
    displayed_loans = {}

    def refresh_loans():
        for item in table.get_children():
            table.delete(item)
        displayed_loans.clear()
        try:
            records = get_active_loans(all_users)
        except (PermissionError, sqlite3.Error) as error:
            summary.config(text="Loans could not be loaded.")
            messagebox.showerror("Unable to Load Loans", str(error), parent=loans_window)
            return

        for loan_id, book_id, title, name, username, borrowed, due, status in records:
            values = [book_id, title]
            if all_users:
                values += [name, username or ""]
            values += [borrowed, due, status]
            item_id = str(loan_id)
            displayed_loans[item_id] = book_id
            table.insert("", tk.END, iid=item_id, values=values, tags=(status,))
        if not records:
            summary.config(text="No current loans." if all_users else "You have no books to return.")
        else:
            due_today = sum(row[-1] == "Due today" for row in records)
            overdue = sum(row[-1] == "Overdue" for row in records)
            summary.config(
                text=f"Books on loan: {len(records)} | Due today: {due_today} | Overdue: {overdue}"
            )

    def return_selected_loan():
        selected = table.selection()
        if not selected:
            messagebox.showinfo("Select a Loan", "Select a book to return.", parent=loans_window)
            return
        item_id = selected[0]
        book_id = displayed_loans[item_id]
        try:
            # Match the displayed loan too, so a stale row cannot return a later loan.
            return_book(book_id, expected_loan_id=int(item_id))
        except (ValueError, PermissionError) as error:
            messagebox.showwarning("Unable to Return", str(error), parent=loans_window)
            refresh_loans()
            return
        except sqlite3.Error as error:
            messagebox.showerror(
                "Unable to Return",
                "Book not returned. Close any unsaved database edits in DB4S and try again.",
                parent=loans_window
            )
            print("Database error:", error)
            return
        refresh_loans()
        messagebox.showinfo("Book Returned", f"You returned {book_id}.", parent=loans_window)

    if not all_users:
        ttk.Button(
            controls, text="Return Book", command=return_selected_loan
        ).pack(side="left", padx=5)
    ttk.Button(controls, text="Refresh", command=refresh_loans).pack(side="left", padx=5)
    ttk.Button(controls, text="Close", command=loans_window.destroy).pack(side="right", padx=5)
    refresh_loans()


def show_books(parent_window, role):
    books_window = tk.Toplevel(parent_window)
    books_window.title("Library Book Catalogue")
    books_window.geometry("1000x480")

    books_frame = ttk.Frame(books_window, padding=20)
    books_frame.pack(fill="both", expand=True)
    ttk.Label(
        books_frame, text="Book Catalogue", font=("Arial", 18, "bold")
    ).pack(pady=(0, 15))

    # Keep controls visible below the expanding table.
    controls = ttk.Frame(books_frame)
    controls.pack(side="bottom", fill="x", pady=(10, 0))
    status_label = ttk.Label(controls, text="", wraplength=900)
    status_label.pack(pady=5)
    table_frame = ttk.Frame(books_frame)
    table_frame.pack(fill="both", expand=True)
    columns = ("book_id", "title", "author", "category", "availability")
    book_table = ttk.Treeview(
        table_frame, columns=columns, show="headings", selectmode="browse"
    )
    for column, heading, width in (
        ("book_id", "Book ID", 120),
        ("title", "Title", 300),
        ("author", "Author", 200),
        ("category", "Category", 150),
        ("availability", "Availability", 120)
    ):
        book_table.heading(column, text=heading)
        book_table.column(column, width=width)

    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=book_table.yview
    )
    book_table.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    book_table.pack(side="left", fill="both", expand=True)

    def refresh_books():
        try:
            books = get_catalogue()
        except sqlite3.Error as error:
            # Remove stale rows if the current catalogue cannot be loaded.
            for item in book_table.get_children():
                book_table.delete(item)
            status_label.config(text="Catalogue could not be loaded.")
            messagebox.showerror(
                "Unable to Load Books",
                "Could not load the catalogue. Check the terminal for details.",
                parent=books_window
            )
            print("Database file:", DB_PATH)
            print("Database error:", error)
            return False

        for item in book_table.get_children():
            book_table.delete(item)
        for book in books:
            # Store the exact Book ID as the row identifier.
            book_table.insert("", tk.END, iid=book[0], values=book)
        status_label.config(
            text=f"Total books: {len(books)}" if books
            else "No books have been added yet."
        )
        return True

    def borrow_selected():
        selected = book_table.selection()
        if not selected:
            messagebox.showinfo(
                "Select a Book", "Click a book row first.", parent=books_window
            )
            return
        book_id = selected[0]
        try:
            loan_id = borrow_book(book_id)
        except (ValueError, PermissionError) as error:
            messagebox.showwarning("Unable to Borrow", str(error), parent=books_window)
            refresh_books()
            return
        except sqlite3.Error as error:
            text = "Book not borrowed. Check the terminal for details."
            if "locked" in str(error).lower():
                text = ("The database is busy. Save or revert edits in DB4S, "
                        "close its database, then try again.")
            messagebox.showerror("Unable to Borrow", text, parent=books_window)
            print("Database file:", DB_PATH)
            print("Database error:", error)
            return

        refresh_books()
        messagebox.showinfo(
            "Book Borrowed",
            f"You borrowed {book_id} successfully. Loan ID: {loan_id}",
            parent=books_window
        )

    def return_selected():
        selected = book_table.selection()
        if not selected:
            messagebox.showinfo(
                "Select a Book", "Click the book you want to return.",
                parent=books_window
            )
            return
        book_id = selected[0]
        try:
            return_book(book_id)
        except (ValueError, PermissionError) as error:
            messagebox.showwarning("Unable to Return", str(error), parent=books_window)
            refresh_books()
            return
        except sqlite3.Error as error:
            text = "Book not returned. Check the terminal for details."
            if "locked" in str(error).lower():
                text = ("The database is busy. Save or revert edits in DB4S, "
                        "close its database, then try again.")
            messagebox.showerror("Unable to Return", text, parent=books_window)
            print("Database file:", DB_PATH)
            print("Database error:", error)
            return

        refresh_books()
        messagebox.showinfo(
            "Book Returned", f"You returned {book_id} successfully.",
            parent=books_window
        )

    if role == "user":
        ttk.Button(
            controls, text="Borrow Book", command=borrow_selected
        ).pack(side="left", padx=5)
        ttk.Button(
            controls, text="Return Book", command=return_selected
        ).pack(side="left", padx=5)
    ttk.Button(
        controls, text="Refresh", command=refresh_books
    ).pack(side="left", padx=5)
    ttk.Button(
        controls, text="Close", command=books_window.destroy
    ).pack(side="right", padx=5)
    refresh_books()


# Save one physical copy. Permission is checked here, not only on the screen.
def save_book(title, author, category):
    if current_member_id is None:
        raise PermissionError("Please sign in as a librarian.")

    title = title.strip()
    author = author.strip()
    category = category.strip()
    if not title or not author or not category:
        raise ValueError("Please enter the title, author and category.")

    connection = sqlite3.connect(DB_PATH.as_uri() + "?mode=rw", uri=True)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        # Keep the permission check and insert in the same transaction.
        connection.execute("BEGIN IMMEDIATE")
        account = connection.execute(
            "SELECT role FROM users WHERE member_id = ?",
            (current_member_id,)
        ).fetchone()

        if account is None or account[0] != "librarian":
            raise PermissionError("Only a librarian can add books.")

        # Find the highest existing ID made of B followed only by digits.
        # Long UUID IDs containing letters are left unchanged and ignored.
        result = connection.execute("""
            SELECT COALESCE(
                MAX(CAST(SUBSTR(book_id, 2) AS INTEGER)), 0
            )
            FROM books
            WHERE book_id GLOB 'B[0-9]*'
              AND SUBSTR(book_id, 2) NOT GLOB '*[^0-9]*'
        """).fetchone()

        next_number = result[0] + 1

        # Pad small numbers with zeros: 2 -> B002, 10 -> B010.
        # Numbers beyond 999 grow naturally: 1000 -> B1000.
        book_id = f"B{next_number:03d}"

        connection.execute("""
            INSERT INTO books (book_id, title, author, category)
            VALUES (?, ?, ?, ?)
        """, (book_id, title, author, category))
        connection.commit()
        return book_id

    except (sqlite3.Error, PermissionError):
        connection.rollback()
        raise
    finally:
        connection.close()


# The librarian enters book details here.
def open_add_book(parent_window):
    add_window = tk.Toplevel(parent_window)
    add_window.title("Add Book")
    add_window.geometry("480x440")
    add_window.transient(parent_window)
    add_window.grab_set()

    add_frame = ttk.Frame(add_window, padding=25)
    add_frame.pack(fill="both", expand=True)
    ttk.Label(
        add_frame, text="Add a Book Copy", font=("Arial", 18, "bold")
    ).pack(pady=(0, 15))

    ttk.Label(add_frame, text="Title").pack(anchor="w")
    title_entry = ttk.Entry(add_frame)
    title_entry.pack(fill="x", pady=(0, 10))

    ttk.Label(add_frame, text="Author").pack(anchor="w")
    author_entry = ttk.Entry(add_frame)
    author_entry.pack(fill="x", pady=(0, 10))

    ttk.Label(add_frame, text="Category").pack(anchor="w")
    category_entry = ttk.Entry(add_frame)
    category_entry.pack(fill="x", pady=(0, 10))

    ttk.Label(
        add_frame,
        text="All fields are required. A Book ID is generated when you save.",
        wraplength=420
    ).pack(pady=5)

    def submit_book():
        try:
            book_id = save_book(
                title_entry.get(), author_entry.get(), category_entry.get()
            )
        except (ValueError, PermissionError) as error:
            book_message.config(text=str(error))
            return
        except sqlite3.Error as error:
            book_message.config(
                text="Book not saved. Check the terminal for details."
            )
            print("Database file:", DB_PATH)
            print("Database error:", error)
            return

        book_message.config(
            text=f"Book added successfully. Book ID: {book_id}"
        )
        # Clear the fields so another click cannot accidentally save this copy.
        title_entry.delete(0, tk.END)
        author_entry.delete(0, tk.END)
        category_entry.delete(0, tk.END)
        title_entry.focus_set()

    ttk.Button(
        add_frame, text="Save Book", command=submit_book
    ).pack(pady=10)
    book_message = ttk.Label(add_frame, text="", wraplength=420)
    book_message.pack(pady=5)
    ttk.Button(
        add_frame, text="Close", command=add_window.destroy
    ).pack(pady=5)
    title_entry.focus_set()


# Show the role only after successful authentication.
def open_welcome(member_id, name, role):
    welcome_window = tk.Toplevel(window)
    welcome_window.title("Library Management System")
    welcome_window.geometry("480x520")
    welcome_frame = ttk.Frame(welcome_window, padding=25)
    welcome_frame.pack(fill="both", expand=True)

    if role == "librarian":
        heading_text = "Librarian"
    else:
        heading_text = "Library User"

    ttk.Label(
        welcome_frame, text=heading_text, font=("Arial", 18, "bold")
    ).pack(pady=(0, 15))
    ttk.Label(
        welcome_frame, text=f"Welcome, {name}!", wraplength=420
    ).pack(pady=5)
    ttk.Label(
        welcome_frame, text=f"Member ID: {member_id}", wraplength=420
    ).pack(pady=5)
    ttk.Label(
        welcome_frame,
        text="You have signed in successfully.\n"
             "Click View Books to browse the catalogue.",
        wraplength=420
    ).pack(pady=15)

    # Both roles can browse the book catalogue.
    ttk.Button(
        welcome_frame,
        text="View Books",
        command=lambda: show_books(welcome_window, role)
    ).pack(pady=10)

    if role == "user":
        ttk.Button(
            welcome_frame, text="My Borrowed Books",
            command=lambda: show_loans(welcome_window)
        ).pack(pady=10)
    elif role == "librarian":
        ttk.Button(
            welcome_frame, text="Current Loans",
            command=lambda: show_loans(welcome_window, all_users=True)
        ).pack(pady=10)

    # Only librarians see this button. save_book also checks the saved role.
    if role == "librarian":
        ttk.Button(
            welcome_frame,
            text="Add Book",
            command=lambda: open_add_book(welcome_window)
        ).pack(pady=10)

    def sign_out():
        global current_member_id
        current_member_id = None
        welcome_window.destroy()
        window.deiconify()
        username_entry.focus_set()

    ttk.Button(
        welcome_frame, text="Sign Out", command=sign_out
    ).pack(pady=10)
    welcome_window.protocol("WM_DELETE_WINDOW", sign_out)
    window.withdraw()


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
