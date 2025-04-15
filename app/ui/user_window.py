import tkinter as tk

def open_user_window(username, user_id):
    new_win = tk.Toplevel()
    new_win.title(f"{username}'s Bank")
    new_win.geometry("400x300")
    label = tk.Label(new_win, text=f"Welcome {username} (User ID: {user_id})")
    label.pack(pady=20)