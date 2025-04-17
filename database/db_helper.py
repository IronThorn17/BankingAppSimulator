import sqlite3
import bcrypt
from database.database import get_connection
from app.event_bus import EventBus

# ------------------------ Admin Functions ------------------------

def get_all_users() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "username": row[1]} for row in users]


def delete_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Delete accounts (transactions remain, due to FK)
    cursor.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    from app.event_bus import EventBus
    EventBus.notify("user_deleted", user_id)

    conn.commit()
    conn.close()


def delete_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM accounts")
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()


# ------------------------ User Functions ------------------------

def create_user(username: str, password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> int | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[1]):
        return row[0]  # Return user ID
    return None


# ------------------------ Account Functions ------------------------

def create_account(user_id: int, account_type: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (user_id, account_type, balance) VALUES (?, ?, ?)", (user_id, account_type, 0.0))
    conn.commit()
    account_id = cursor.lastrowid
    conn.close()
    return account_id


def get_accounts(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, account_type, balance FROM accounts WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {"account_id": row[0], "type": row[1], "balance": row[2]}
        for row in rows
    ]


def get_account_balance(account_id: int) -> float | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ------------------------ Transaction Functions ------------------------

def deposit(account_id: int, amount: float, note: str = "Deposit") -> bool:
    if amount <= 0:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
        cursor.execute("""
            INSERT INTO transactions (account_id, type, amount, note)
            VALUES (?, 'deposit', ?, ?)
        """, (account_id, amount, note))

        # Find user ID and notify event
        cursor.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        if row:
            EventBus.notify("account_updated", row[0])

        conn.commit()
        return True
    finally:
        conn.close()


def transfer_funds(from_account: int, to_account: int, amount: float, note: str = "Transfer") -> bool:
    if amount <= 0 or from_account == to_account:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    # Check sufficient funds
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (from_account,))
    from_balance = cursor.fetchone()
    if not from_balance or from_balance[0] < amount:
        conn.close()
        return False

    try:
        # Withdraw from source
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, from_account))
        cursor.execute("""
            INSERT INTO transactions (account_id, type, amount, note, related_account_id)
            VALUES (?, 'transfer_out', ?, ?, ?)
        """, (from_account, amount, note, to_account))

        # Deposit into destination
        cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, to_account))
        cursor.execute("""
            INSERT INTO transactions (account_id, type, amount, note, related_account_id)
            VALUES (?, 'transfer_in', ?, ?, ?)
        """, (to_account, amount, note, from_account))

        # Notify both users
        cursor.execute("SELECT user_id FROM accounts WHERE id = ?", (from_account,))
        from_user = cursor.fetchone()
        cursor.execute("SELECT user_id FROM accounts WHERE id = ?", (to_account,))
        to_user = cursor.fetchone()

        if from_user:
            EventBus.notify("account_updated", from_user[0])
        if to_user and to_user != from_user:
            EventBus.notify("account_updated", to_user[0])

        conn.commit()
        return True
    except Exception as e:
        print("[ERROR]", e)
        conn.rollback()
        return False
    finally:
        conn.close()


def get_transaction_history(account_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT type, amount, timestamp, note, related_account_id
        FROM transactions
        WHERE account_id = ?
        ORDER BY timestamp DESC
    """, (account_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "type": row[0],
            "amount": row[1],
            "timestamp": row[2],
            "note": row[3],
            "related_account_id": row[4]
        }
        for row in rows
    ]

def get_account_balance(account_id: int) -> float | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def record_withdrawal(account_id: int, amount: float, note: str = "Withdrawal") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))
        cursor.execute("""
            INSERT INTO transactions (account_id, type, amount, note)
            VALUES (?, 'transfer_out', ?, ?)
        """, (account_id, amount, note))

        # Find user ID and notify
        cursor.execute("SELECT user_id FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        if row:
            EventBus.notify("account_updated", row[0])

        conn.commit()
        return True
    except Exception as e:
        print("[ERROR] withdrawal:", e)
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user_accounts_by_username(username: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.account_type, a.balance
        FROM accounts a
        JOIN users u ON a.user_id = u.id
        WHERE u.username = ?
        ORDER BY a.id ASC
    """, (username,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {"account_id": row[0], "type": row[1], "balance": row[2]}
        for row in rows
    ]