import tkinter as tk
from tkinter import messagebox
from database.db_helper import (
    get_accounts,
    get_transaction_history,
    create_account,
    deposit,
    get_account_balance,
    record_withdrawal,
    get_user_accounts_by_username
)
from app.event_bus import EventBus


class UserWindow:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        EventBus.subscribe("account_updated", self.on_account_update)
        EventBus.subscribe("user_deleted", self.on_user_deleted)

        self.window = tk.Toplevel()
        self.window.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.window.title(f"{username}'s Dashboard")
        self.window.geometry("550x450")

        # Navigation bar
        self.nav_frame = tk.Frame(self.window)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)

        self.content_frame = tk.Frame(self.window)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.nav_frame, text="View Accounts", command=self.show_accounts).pack(side=tk.LEFT)
        tk.Button(self.nav_frame, text="Deposit/Withdraw", command=self.show_deposit).pack(side=tk.LEFT)
        tk.Button(self.nav_frame, text="Transfer", command=self.show_transfer).pack(side=tk.LEFT)
        tk.Button(self.nav_frame, text="Transactions", command=self.show_transactions_tab).pack(side=tk.LEFT)

        self.transaction_account_var = tk.StringVar()  # used by transaction tab
        self.transaction_account_map = {}

        self.show_accounts()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def cleanup(self):
        from app.event_bus import EventBus
        EventBus.unsubscribe("account_updated", self.on_account_update)
        self.window.destroy()

    def on_account_update(self, updated_user_id):
        if updated_user_id != self.user_id:
            return

        print(f"[DEBUG] Refresh triggered for {self.username}")

        # Refresh if transactions tab is active and has been initialized
        if hasattr(self, "transaction_list_frame") and self.current_view == "transactions":
            current_account = self.transaction_account_var.get()
            self.refresh_transaction_list(current_account)

        # Refresh account view if active
        if hasattr(self, "current_view") and self.current_view == "accounts":
            self.show_accounts()

        if self.current_view == "accounts":
            self.window.after(100, self.show_accounts)
        elif self.current_view == "transactions":
            self.window.after(100, self.show_transactions_tab)
        elif self.current_view == "deposit":
            self.window.after(100, self.show_deposit)
        elif self.current_view == "transfer":
            self.window.after(100, self.show_transfer)

    def on_user_deleted(self, deleted_user_id):
        if deleted_user_id == self.user_id:
            messagebox.showwarning("Logged Out", "Your account has been deleted by an admin.")
            self.cleanup()


    # -------------------- View Accounts --------------------
    def show_accounts(self):
        self.clear_content()
        self.current_view = "accounts"
        accounts = get_accounts(self.user_id)

        tk.Label(self.content_frame, text="Your Accounts:", font=("Arial", 14)).pack(pady=10)

        if not accounts:
            tk.Label(self.content_frame, text="No accounts found.").pack(pady=5)

        for acc in accounts:
            frame = tk.Frame(self.content_frame, pady=5)
            frame.pack(fill=tk.X, padx=20)

            label = tk.Label(frame, text=f"{acc['type'].capitalize()} - ${acc['balance']:.2f}", anchor="w", width=40)
            label.pack(side=tk.LEFT)

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

    # -------------------- Deposit / Withdraw --------------------
    def show_deposit(self):
        self.clear_content()
        self.current_view = "deposit"
        tk.Label(self.content_frame, text="Deposit / Withdraw Funds", font=("Arial", 14)).pack(pady=10)

        accounts = get_accounts(self.user_id)
        if not accounts:
            tk.Label(self.content_frame, text="You have no accounts to use.").pack(pady=10)
            return

        tk.Label(self.content_frame, text="Select Account").pack()
        selected_account = tk.StringVar()
        display_options = [f"{acc['type'].capitalize()} - ${acc['balance']:.2f} (#{acc['account_id']})" for acc in accounts]
        acc_map = {label: acc['account_id'] for label, acc in zip(display_options, accounts)}
        selected_account.set(display_options[0])

        tk.OptionMenu(self.content_frame, selected_account, *acc_map.keys()).pack(pady=5)

        tk.Label(self.content_frame, text="Amount").pack()
        amount_var = tk.StringVar()
        tk.Entry(self.content_frame, textvariable=amount_var).pack(pady=5)

        def do_deposit():
            acc_id = acc_map[selected_account.get()]
            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid deposit amount.")
                return

            if deposit(acc_id, amount, note="Manual Deposit"):
                messagebox.showinfo("Success", f"Deposited ${amount:.2f}")
                self.show_deposit()
            else:
                messagebox.showerror("Error", "Deposit failed.")

        def do_withdraw():
            acc_id = acc_map[selected_account.get()]
            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Enter a valid withdrawal amount.")
                return

            balance = get_account_balance(acc_id)
            if balance is None or balance < amount:
                messagebox.showerror("Error", "Insufficient funds.")
                return

            if record_withdrawal(acc_id, amount):
                messagebox.showinfo("Success", f"Withdrew ${amount:.2f}")
                self.show_deposit()
            else:
                messagebox.showerror("Error", "Withdrawal failed.")

        tk.Button(self.content_frame, text="Deposit", command=do_deposit).pack(pady=5)
        tk.Button(self.content_frame, text="Withdraw", command=do_withdraw).pack(pady=5)

    # -------------------- Transactions --------------------
    def show_transactions_tab(self):
        self.clear_content()
        self.current_view = "transactions"
        accounts = get_accounts(self.user_id)
        if not accounts:
            tk.Label(self.content_frame, text="No accounts to view.").pack(pady=20)
            return

        tk.Label(self.content_frame, text="Select Account to View Transactions", font=("Arial", 14)).pack(pady=10)

        self.transaction_account_map = {
            f"{acc['type'].capitalize()} - ${acc['balance']:.2f} (#{acc['account_id']})": acc['account_id']
            for acc in accounts
        }

        options = list(self.transaction_account_map.keys())
        self.transaction_account_var.set(options[0])

        dropdown = tk.OptionMenu(self.content_frame, self.transaction_account_var, *options, command=self.refresh_transaction_list)
        dropdown.pack(pady=5)

        self.transaction_list_frame = tk.Frame(self.content_frame)
        self.transaction_list_frame.pack(fill=tk.BOTH, expand=True)

        self.refresh_transaction_list(self.transaction_account_var.get())

    def refresh_transaction_list(self, selected_label):
        for widget in self.transaction_list_frame.winfo_children():
            widget.destroy()

        account_id = self.transaction_account_map.get(selected_label)
        transactions = get_transaction_history(account_id)

        if not transactions:
            tk.Label(self.transaction_list_frame, text="No transactions found.").pack(pady=10)
            return

        for tx in transactions:
            text = f"[{tx['timestamp']}] {tx['type']} ${tx['amount']:.2f}"
            if tx['note']:
                text += f" - {tx['note']}"
            if tx['related_account_id']:
                text += f" (to/from Acc #{tx['related_account_id']})"
            tk.Label(self.transaction_list_frame, text=text, anchor="w", justify="left").pack(anchor="w", padx=10, pady=2)

    # -------------------- Transfer Placeholder --------------------
    def show_transfer(self):
        from tkinter import ttk  # ensure ttk is imported
        self.clear_content()
        self.current_view = "transfer"

        tk.Label(self.content_frame, text="Transfer Funds", font=("Arial", 14)).pack(pady=5)

        notebook = ttk.Notebook(self.content_frame)
        internal_frame = tk.Frame(notebook)
        external_frame = tk.Frame(notebook)

        notebook.add(internal_frame, text="To My Accounts")
        notebook.add(external_frame, text="To Another User")
        notebook.pack(fill=tk.BOTH, expand=True)

        self.build_internal_transfer_ui(internal_frame)
        self.build_external_transfer_ui(external_frame)

    def build_internal_transfer_ui(self, parent):
        accounts = get_accounts(self.user_id)
        if len(accounts) < 2:
            tk.Label(parent, text="You need at least two accounts to transfer funds.").pack(pady=10)
            return

        display_options = [f"{acc['type'].capitalize()} - ${acc['balance']:.2f} (#{acc['account_id']})" for acc in accounts]
        acc_map = {label: acc['account_id'] for label, acc in zip(display_options, accounts)}

        from_var = tk.StringVar(value=display_options[0])
        to_var = tk.StringVar(value=next(opt for opt in display_options if opt != from_var.get()))

        def update_to_options(*_):
            to_menu = to_dropdown["menu"]
            to_menu.delete(0, "end")
            for option in display_options:
                if option != from_var.get():
                    to_menu.add_command(label=option, command=lambda val=option: to_var.set(val))

        tk.Label(parent, text="From Account").pack()
        tk.OptionMenu(parent, from_var, *display_options, command=lambda _: update_to_options()).pack()

        tk.Label(parent, text="To Account").pack()
        to_dropdown = tk.OptionMenu(parent, to_var, *[opt for opt in display_options if opt != from_var.get()])
        to_dropdown.pack()

        tk.Label(parent, text="Amount").pack()
        amount_var = tk.StringVar()
        tk.Entry(parent, textvariable=amount_var).pack(pady=5)

        def do_transfer():
            from_id = acc_map[from_var.get()]
            to_id = acc_map[to_var.get()]
            if from_id == to_id:
                messagebox.showerror("Error", "Cannot transfer to the same account.")
                return

            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.")
                return

            balance = get_account_balance(from_id)
            if balance is None or balance < amount:
                messagebox.showerror("Error", "Insufficient funds.")
                return

            from_type = from_var.get().split(" - ")[0]
            to_type = to_var.get().split(" - ")[0]
            note_out = f"Transfer to {self.username} - {to_type}"
            note_in = f"Transfer from {self.username} - {from_type}"

            if record_withdrawal(from_id, amount, note=note_out) and deposit(to_id, amount, note=note_in):
                messagebox.showinfo("Success", f"Transferred ${amount:.2f}")
                self.show_transfer()

        tk.Button(parent, text="Transfer Funds", command=do_transfer).pack(pady=10)

    def build_external_transfer_ui(self, parent):
        tk.Label(parent, text="Recipient Username").pack()
        recipient_var = tk.StringVar()
        tk.Entry(parent, textvariable=recipient_var).pack()

        tk.Label(parent, text="Your Sending Account").pack()
        user_accounts = get_accounts(self.user_id)
        if not user_accounts:
            tk.Label(parent, text="You have no accounts to send from.").pack()
            return

        from_options = [f"{acc['type'].capitalize()} - ${acc['balance']:.2f} (#{acc['account_id']})" for acc in user_accounts]
        acc_map = {label: acc['account_id'] for label, acc in zip(from_options, user_accounts)}
        from_var = tk.StringVar(value=from_options[0])
        tk.OptionMenu(parent, from_var, *from_options).pack()

        tk.Label(parent, text="Amount").pack()
        amount_var = tk.StringVar()
        tk.Entry(parent, textvariable=amount_var).pack(pady=5)

        def do_external_transfer():
            recipient = recipient_var.get().strip()
            if not recipient or recipient == self.username:
                messagebox.showerror("Error", "Enter a valid recipient username.")
                return

            from database.db_helper import get_user_accounts_by_username
            target_accounts = get_user_accounts_by_username(recipient)
            if not target_accounts:
                messagebox.showerror("Error", "Recipient not found or has no accounts.")
                return

            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.")
                return

            from_id = acc_map[from_var.get()]
            to_id = target_accounts[0]["account_id"]
            to_type = target_accounts[0]["type"]

            balance = get_account_balance(from_id)
            if balance is None or balance < amount:
                messagebox.showerror("Error", "Insufficient funds.")
                return

            note_out = f"Transfer to {recipient} - {to_type}"
            note_in = f"Transfer from {self.username} - {from_var.get().split(' - ')[0]}"

            if record_withdrawal(from_id, amount, note=note_out) and deposit(to_id, amount, note=note_in):
                messagebox.showinfo("Success", f"Transferred ${amount:.2f} to {recipient}")
                self.show_transfer()

        tk.Button(parent, text="Send Transfer", command=do_external_transfer).pack(pady=10)


def open_user_window(username, user_id):
    UserWindow(username, user_id)
