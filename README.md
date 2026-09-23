                    Library Management System
                          Project Abstract
                          # Library Management System

**Student:** Rajesh Bhatt  
**Course:** BS-68 ‚Äî AI Driven Python Programming

## Project Abstract

The aim of this project is to develop a simple Library Management System using Python. Maintaining library records manually can make it difficult to keep track of books, who has borrowed them, and whether they are available. This application brings these details together in one place.

The application supports account registration and sign-in, with separate roles for the librarian and library users. The librarian can add books and view current loans with borrower details. Library users can view the catalogue, borrow available books, check their own loans and return books. Each physical copy has its own unique Book ID, so multiple copies of the same title can be managed separately.

Python is used for the program logic, Tkinter provides the graphical interface, and SQLite stores the records. Buttons and input fields allow users to complete tasks without typing commands. Saved records remain available when the application is opened again.

The database contains three related tables: books, users and loans. These store book details, user information, and borrowing and return records. Linking the tables allows the system to identify who borrowed each copy. A book is shown as borrowed while it has a loan without a return date. Returning it makes it available again while preserving the borrowing history.

The borrowing period is seven days. Users can view their borrowed books, due dates and whether a loan is on time, due today or overdue. The librarian can view current loans across users. Passwords are stored as salted password hashes rather than plain text.

The project has been developed step by step, starting with the database design, followed by registration, sign-in, role-based screens, book management, borrowing and returns. Input checks and error handling help prevent mistakes such as missing required details, duplicate usernames and borrowing a copy already on loan. This approach has helped me understand Python functions, database relationships, validation and GUI development. Searching for books and editing or deleting book records remain planned improvements from the original proposal.

## Implemented Features

- Sign up and sign in with a username and password.
- Separate Librarian and Library User roles.
- Librarian access to add books with automatically generated Book IDs.
- Multiple copies of a title, each with its own Book ID.
- A catalogue showing title, author, category and availability.
- Borrowing available copies and returning the signed-in user's own books.
- My Borrowed Books with borrowed date, due date and loan status.
- Current Loans for the librarian, including borrower details.
- Seven-day borrowing period and retained loan history.
- SQLite storage and password hashing.

## Project Files

| File | Purpose |
| --- | --- |
| `login_window.py` | Starts the application and its graphical screens. |
| `Library_app.py` | Creates or prepares the database tables. |
| `library.db` | Stores the supplied books, users and loan records. |
| `README.md` | Project description and running instructions. |

Keep these files together in the extracted project folder. The Python scripts locate `library.db` beside themselves. Running a copy from another folder can open a different database or produce a missing-database error.

## Requirements

- Python 3 with Tkinter support.
- A desktop environment to display the windows.
- SQLite support is provided by Python's built-in `sqlite3` module.

No third-party Python packages are required by the application. VS Code and DB Browser for SQLite are optional tools; neither is required to use the application.

To check Tkinter, run `python3 -m tkinter` on macOS, or `python -m tkinter` on Windows. A small test window should open. If it does not, use a Python installation with Tcl/Tk support before starting the project.

## How to Run

1. Extract the ZIP into a writable folder on your computer.
2. Keep the supplied Python files and `library.db` together.
3. Open a terminal in that folder, or open the folder in VS Code and select Terminal ‚Üí New Terminal.
4. Run the application:

   **macOS:**

   ```bash
   python3 login_window.py
   ```

   **Windows:**

   ```bash
   python login_window.py
   ```

5. Check the printed `Login database path` points to the database inside the extracted folder.
6. Sign in using a tested demonstration account supplied with the project.

The supplied database is intended to contain the existing tables and demonstration records. It does not need to be recreated to run the application. `Library_app.py` is the setup script; a newly created database will not contain the original demonstration accounts or full catalogue.

## Demonstration Accounts ‚Äî Complete Before Submission

Fill in this table with tested project-only accounts from the supplied database. These placeholders are not working credentials. Do not use passwords that you use for personal accounts. If the repository is public, provide demonstration credentials privately to the teacher instead of publishing them here.

| Role | Username | Project-only password |
| --- | --- | --- |
| Librarian | RB007 | TO BE ADDED |
| Library User | Paddy | TO BE ADDED |

New accounts created through Sign Up receive the Library User role. Sign Up does not grant librarian access.

## How to Use

### Librarian

1. Sign in with the librarian account.
2. Select View Books to see the catalogue.
3. Select Add Book and enter the title, author and category. The application generates a Book ID.
4. Select Current Loans to view borrowers, books and due dates.
5. Use Sign Out when finished.

### Library User

1. Sign in with a library-user account, or create one through Sign Up.
2. Select View Books, select an available copy and choose Borrow Book.
3. Open My Borrowed Books to check the due date and status.
4. Select your borrowed book and choose Return Book.
5. Refresh an already-open catalogue to see the updated availability.

A book borrowed on 20 September is due on 27 September. It is marked Due today on 27 September and Overdue from 28 September if it has not been returned.

## Database Design

| Table | Main fields | Purpose |
| --- | --- | --- |
| `books` | `book_id`, `title`, `author`, `category` | One record per physical copy. |
| `users` | `member_id`, `name`, `username`, `password_hash`, `role` | Member details and login information. |
| `loans` | `loan_id`, `book_id`, `member_id`, `borrowed_date`, `returned_date` | Borrowing and return history. |

`loans.book_id` refers to `books.book_id`, and `loans.member_id` refers to `users.member_id`. An empty return date identifies an active loan. The due date is calculated from the borrowing date plus seven days.

## Checks Before Submission

- Test the project after extracting the ZIP into a separate folder.
- Confirm both demonstration accounts can sign in and display the correct roles.
- Confirm the expected book catalogue is present.
- Borrow an available copy and confirm a second user cannot borrow that same copy.
- Return it using the borrowing user's account and confirm it becomes available again.
- Check the due dates in My Borrowed Books and the librarian's Current Loans.
- Check required-field validation, duplicate usernames and an incorrect password.
- If alphabetical ordering has been added, confirm the catalogue displays titles from A to Z.


## Planned Improvements

- Search by title or author.
- An account password-reset facility.

## Learning Outcome

Building this project in small steps helped me follow how data moves from a Tkinter input field into a Python function and then into SQLite.

 It also helped me understand how related tables work together and why validation, password protection and testing are necessary for a useful application.

Guidance, help and motivation from the Teacher, Mrs.Aiby Sara Biju was phenomenal to be able to complete the mini project on time.

I took help from ChatGPT especially around the login.py code, also to understand  some of the errors and trouble shooting. 



<img width="468" height="487" alt="image" src="https://github.com/user-attachments/assets/e42fe364-842d-409a-a7e8-e743a8956682" />
