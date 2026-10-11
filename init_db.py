import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = os.environ.get("DATABASE_PATH", "study_blog.db")
SCHEMA_FILE = "schema.sql"

def get_db_connection(db_path=DB_NAME):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_NAME):
    print(f"Initializing database at: {db_path}...")
    
    conn = get_db_connection(db_path)
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # Create default admin if not exists
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@12345")

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (admin_username, admin_email))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        admin_hash = generate_password_hash(admin_password)
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, 'admin')
            """,
            (admin_username, admin_email, admin_hash)
        )
        conn.commit()
        print("Default admin created successfully:")
        print(f"  Username : {admin_username}")
        print(f"  Email    : {admin_email}")
        print(f"  Password : {admin_password}")
        print("  Role     : admin")
        print("\n[!] IMPORTANT: Change default password immediately in a production environment!")
    else:
        print("Admin user already exists. Skipping admin creation.")

    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
