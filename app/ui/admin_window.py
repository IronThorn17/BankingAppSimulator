import tkinter as tk
from tkinter import messagebox
from database.db_helper import delete_all_users

def open_admin_window():
    admin_win = tk.Toplevel()
    admin_win.title("Admin Tools")
    admin_win.geometry("300x150")

    label = tk.Label(admin_win, text="Admin Tools", font=("Arial", 14))
    label.pack(pady=10)

    clear_btn = tk.Button(admin_win, text="Delete All Users", command=clear_users)
    clear_btn.pack(pady=10)


def clear_users():
    if messagebox.askyesno("Confirm", "Are you sure you want to delete all users and accounts?"):
        delete_all_users()
        messagebox.showinfo("Done", "All users and accounts have been deleted.")