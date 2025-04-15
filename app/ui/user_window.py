import tkinter as tk
from tkinter import messagebox
from database.db_helper import (
    get_accounts,
    get_transaction_history,
    create_account,
    deposit
)

class UserWindow:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id

        self.window = tk.Toplevel()
        self.window.title(f"{username}'s Dashboard")
        self.window.geometry("500x400")

        # Create navigation bar
        self.nav_frame = tk.Frame(self.window)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)

        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.nav_frame, text="View Accounts", command=self.show_accounts).pack(side=tk.LEFT)
        tk.Button(self.nav_frame, text="Deposit", command=self.show_deposit).pack(side=tk.LEFT)
        tk.Button(self.nav_frame, text="Transfer", command=self.show_transfer).pack(side=tk.LEFT)

        self.show_accounts()  # Show account list by default

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_accounts(self):
        self.clear_content()
        accounts = get_accounts(self.user_id)

        tk.Label(self.content_frame, text="Your Accounts:", font=("Arial", 14)).pack(pady=10)

        if not accounts:
            tk.Label(self.content_frame, text="No accounts found.").pack(pady=5)

        for acc in accounts:
            frame = tk.Frame(self.content_frame, pady=5)
            frame.pack(fill=tk.X, padx=20)

            label = tk.Label(frame, text=f"{acc['type'].capitalize()} - ${acc['balance']:.2f}", anchor="w", width=40)
            label.pack(side=tk.LEFT)

            btn = tk.Button(frame, text="View Transactions",
                            command=lambda acc_id=acc['account_id']: self.show_transaction_history(acc_id))
            btn.pack(side=tk.RIGHT)

        # Create new account section
        separator = tk.Frame(self.content_frame, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=10)

        tk.Button(self.content_frame, text="Create New Account", command=self.create_account_popup).pack(pady=10)

    def create_account_popup(self):
        popup = tk.Toplevel(self.window)
        popup.title("Create Account")
        popup.geometry("300x200")

        tk.Label(popup, text="Account Name (e.g., Checking)").pack(pady=5)
        name_var = tk.StringVar()
        tk.Entry(popup, textvariable=name_var).pack()

        tk.Label(popup, text="Initial Balance").pack(pady=5)
        balance_var = tk.StringVar()
        tk.Entry(popup, textvariable=balance_var).pack()

        def submit():
            name = name_var.get().strip()
            try:
                balance = float(balance_var.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Balance must be a valid number.")
                return

            if not name:
                messagebox.showerror("Invalid Input", "Account name cannot be empty.")
                return

            acc_id = create_account(self.user_id, name)
            if acc_id:
                deposit(acc_id, balance, note="Initial Balance")
                messagebox.showinfo("Success", f"Created '{name}' with ${balance:.2f}")
                popup.destroy()
                self.show_accounts()
            else:
                messagebox.showerror("Error", "Failed to create account.")

        tk.Button(popup, text="Create", command=submit).pack(pady=10)

    def show_transaction_history(self, account_id):
        transactions = get_transaction_history(account_id)
        history_win = tk.Toplevel(self.window)
        history_win.title("Transaction History")
        history_win.geometry("400x300")

        if not transactions:
            tk.Label(history_win, text="No transactions found.").pack(pady=20)
            return

        for tx in transactions:
            text = f"[{tx['timestamp']}] {tx['type']} ${tx['amount']:.2f}"
            if tx['note']:
                text += f" - {tx['note']}"
            if tx['related_account_id']:
                text += f" (to/from Acc #{tx['related_account_id']})"
            tk.Label(history_win, text=text, anchor="w", justify="left").pack(anchor="w", padx=10, pady=2)

    def show_deposit(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Deposit - (Coming Soon)", font=("Arial", 14)).pack(pady=50)

    def show_transfer(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Transfer - (Coming Soon)", font=("Arial", 14)).pack(pady=50)


def open_user_window(username, user_id):
    UserWindow(username, user_id)
