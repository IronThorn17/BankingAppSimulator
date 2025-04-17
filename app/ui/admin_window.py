import tkinter as tk
from tkinter import messagebox, ttk
from database.db_helper import (
    delete_all_users,
    get_all_users,
    get_accounts,
    get_transaction_history,
    delete_user_by_id
)


def open_admin_window():
    AdminWindow()


class AdminWindow:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Admin Panel")
        self.window.geometry("600x500")

        self.nav = ttk.Notebook(self.window)
        self.users_tab = tk.Frame(self.nav)
        self.clear_tab = tk.Frame(self.nav)

        self.nav.add(self.users_tab, text="User Management")
        self.nav.add(self.clear_tab, text="Clear Database")

        self.nav.pack(fill=tk.BOTH, expand=True)

        self.build_users_tab()
        self.build_clear_tab()

    # --------------------- User Management Tab ---------------------

    def build_users_tab(self):
        tk.Label(self.users_tab, text="Users", font=("Arial", 14)).pack(pady=10)
        self.user_list_frame = tk.Frame(self.users_tab)
        self.user_list_frame.pack(fill=tk.BOTH, expand=True)

        self.refresh_user_list()

    def refresh_user_list(self):
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        users = get_all_users()
        if not users:
            tk.Label(self.user_list_frame, text="No users found.").pack(pady=10)
            return

        for user in users:
            frame = tk.Frame(self.user_list_frame, pady=3)
            frame.pack(fill=tk.X, padx=20)

            label = tk.Label(frame, text=f"{user['username']} (ID: {user['id']})", anchor="w")
            label.pack(side=tk.LEFT)

            view_button = tk.Button(frame, text="View Accounts",
                                    command=lambda uid=user['id'], uname=user['username']: self.view_user_accounts(uid, uname))
            view_button.pack(side=tk.RIGHT)

    def view_user_accounts(self, user_id, username):
        popup = tk.Toplevel(self.window)
        popup.title(f"{username}'s Accounts")
        popup.geometry("400x400")

        tk.Label(popup, text=f"Accounts for {username}", font=("Arial", 12)).pack(pady=10)

        accounts = get_accounts(user_id)
        if not accounts:
            tk.Label(popup, text="No accounts found.").pack(pady=5)
        else:
            for acc in accounts:
                frame = tk.Frame(popup)
                frame.pack(fill=tk.X, padx=20, pady=3)

                label = tk.Label(frame, text=f"{acc['type'].capitalize()} - ${acc['balance']:.2f}")
                label.pack(side=tk.LEFT)

                view_tx = tk.Button(frame, text="Transactions", command=lambda aid=acc['account_id']: self.view_account_transactions(aid))
                view_tx.pack(side=tk.RIGHT)

        del_button = tk.Button(popup, text=f"Delete {username}", fg="red",
                               command=lambda: self.confirm_delete_user(user_id, username, popup))
        del_button.pack(pady=20)

    def view_account_transactions(self, account_id):
        tx_popup = tk.Toplevel(self.window)
        tx_popup.title("Transaction History")
        tx_popup.geometry("400x300")

        transactions = get_transaction_history(account_id)

        if not transactions:
            tk.Label(tx_popup, text="No transactions found.").pack(pady=10)
            return

        for tx in transactions:
            text = f"[{tx['timestamp']}] {tx['type']} ${tx['amount']:.2f}"
            if tx['note']:
                text += f" - {tx['note']}"
            if tx['related_account_id']:
                text += f" (to/from Acc #{tx['related_account_id']})"
            tk.Label(tx_popup, text=text, anchor="w", justify="left").pack(anchor="w", padx=10, pady=2)

    def confirm_delete_user(self, user_id, username, popup):
        if messagebox.askyesno("Confirm", f"Delete user '{username}'?\nTransactions will be preserved."):
            delete_user_by_id(user_id)
            messagebox.showinfo("Success", f"User '{username}' deleted.")
            popup.destroy()
            self.refresh_user_list()

    # --------------------- Clear Database Tab ---------------------

    def build_clear_tab(self):
        tk.Label(self.clear_tab, text="Clear Database", font=("Arial", 14), fg="red").pack(pady=20)
        tk.Button(self.clear_tab, text="Delete ALL Users and Accounts", fg="white", bg="red",
                  command=self.confirm_clear_database).pack(pady=20)

    def confirm_clear_database(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the entire database?"):
            delete_all_users()
            self.refresh_user_list()
            messagebox.showinfo("Done", "Database cleared.")
