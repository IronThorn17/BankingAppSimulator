import tkinter as tk
from tkinter import messagebox
from database.db_helper import create_user, authenticate_user
from app.ui.user_window import open_user_window
from app.ui.admin_window import open_admin_window  # ✅ NEW

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Banking App - Login")
        self.root.geometry("300x320")

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Label(root, text="Username").pack(pady=5)
        tk.Entry(root, textvariable=self.username_var).pack()

        tk.Label(root, text="Password").pack(pady=5)
        tk.Entry(root, show="*", textvariable=self.password_var).pack()

        tk.Button(root, text="Login", command=self.login).pack(pady=5)
        tk.Button(root, text="Create Account", command=self.create_account).pack()

        # Admin Login Section
        tk.Label(root, text="--- Admin Login ---").pack(pady=10)
        self.admin_pass_var = tk.StringVar()
        tk.Entry(root, show="*", textvariable=self.admin_pass_var).pack()
        tk.Button(root, text="Admin Login", command=self.admin_login).pack(pady=5)

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        user_id = authenticate_user(username, password)
        if user_id:
            messagebox.showinfo("Login Success", f"Welcome, {username}!")
            open_user_window(username, user_id)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def create_account(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty.")
            return

        if create_user(username, password):
            messagebox.showinfo("Success", "Account created. You may now log in.")
        else:
            messagebox.showerror("Error", "Username already exists.")

    def admin_login(self):
        entered_password = self.admin_pass_var.get()
        if entered_password == "admin123":  # ✅ Hardcoded for now
            open_admin_window()
        else:
            messagebox.showerror("Access Denied", "Incorrect admin password.")