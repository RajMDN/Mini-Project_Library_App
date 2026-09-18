                    Library Management System
                          Project Abstract
The aim of this project is to develop a simple Library Management System using Python. Maintaining library records manually can make it difficult to keep track of books, who has borrowed them, and whether they are available. This application will help users manage these details in one place.

The system will allow users to add books, view the book list, search for books by title or author, and update book details. It will also support issuing and returning books. Each book will have a unique ID, a title, an author, and an availability status. When a book is issued, the borrower’s details will be recorded and the book’s status will be updated. Once the book is returned, it will be marked as available again.

Python will be used to write the program, Tkinter will be used to create the graphical user interface, and SQLite will be used to store the records. The interface will have simple buttons and input fields so users can complete tasks without typing commands. Saved records will be available the next time the application is opened.

The database will contain three related tables: Books, Users, and Borrowing Records. These tables will store book details, user information, and records of borrowing and returns. Linking these tables will help the system identify who has borrowed each book and track its availability.
The program will include basic checks to prevent mistakes, such as leaving required fields empty, entering a duplicate book ID, or issuing a book that is already borrowed. Error handling will also be included to display helpful messages when something goes wrong.

I plan to develop this project step by step, starting with the database design and its three related tables. I will then build the main functions in Python and connect them to a simple Tkinter interface. Each feature will be tested as I progress, including checking invalid inputs and updating book availability. This approach will help me understand how Python and SQLite work together 
while building a practical library application.

<img width="468" height="487" alt="image" src="https://github.com/user-attachments/assets/e42fe364-842d-409a-a7e8-e743a8956682" />
