from tkinter import Tk
from database.database import initialize_database
from app.ui.login_screen import LoginScreen

if __name__ == "__main__":
    initialize_database()

    root = Tk()
    app = LoginScreen(root)
    root.mainloop()