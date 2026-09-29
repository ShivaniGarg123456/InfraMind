import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# Load .env from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_db():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not set in .env")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )


def create_database():

    conn = get_db()
    cursor = conn.cursor()

    # Complaints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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

    conn.commit()

    cursor.close()
    conn.close()


if __name__ == "__main__":

    create_database()

    print("Central PostgreSQL database connected successfully!")