
import sqlite3


def create_database():

    conn = sqlite3.connect("inframind.db")

    cursor = conn.cursor()


    # Complaints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            department TEXT,
            priority TEXT,
            status TEXT DEFAULT 'Pending',
            deadline TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)


    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            student_id INTEGER,
            department TEXT
        )
    """)


    conn.commit()
    conn.close()


if __name__ == "__main__":

    create_database()

    print("Database created successfully!")

