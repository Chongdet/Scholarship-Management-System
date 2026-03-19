import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "scholarship.db")

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- 🛠️ Starting Migration... ---")

    # Add parttime_description to student table
    try:
        cursor.execute("ALTER TABLE student ADD COLUMN parttime_description TEXT")
        print("✅ Added 'parttime_description' to 'student' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ 'parttime_description' already exists in 'student' table.")
        else:
            print(f"❌ Error adding to 'student': {e}")

    # Add parttime_description to application table
    try:
        cursor.execute("ALTER TABLE application ADD COLUMN parttime_description TEXT")
        print("✅ Added 'parttime_description' to 'application' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ 'parttime_description' already exists in 'application' table.")
        else:
            print(f"❌ Error adding to 'application': {e}")

    conn.commit()
    conn.close()
    print("--- 🎉 Migration Complete! ---")

if __name__ == "__main__":
    migrate()
