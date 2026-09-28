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
            email TEXT UNIQUE,
            email_verified INTEGER DEFAULT 0,
            otp TEXT,
            otp_expiry TEXT,
            role TEXT NOT NULL,
            student_id INTEGER,
            department TEXT
        )
    """)


    # Add new columns to existing database if they don't exist
    existing_columns = [
        row[1]
        for row in cursor.execute("PRAGMA table_info(users)").fetchall()
    ]

    if "email" not in existing_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN email TEXT"
        )

    if "email_verified" not in existing_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0"
        )

    if "otp" not in existing_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN otp TEXT"
        )

    if "otp_expiry" not in existing_columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN otp_expiry TEXT"
        )


    conn.commit()
    conn.close()


if __name__ == "__main__":

    create_database()

    print("Database created successfully!")