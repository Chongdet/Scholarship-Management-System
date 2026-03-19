import sqlite3
import os

def migrate():
    db_path = 'scholarship.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Columns to add
    updates = [
        ('student', 'activity_hours', 'INTEGER DEFAULT 0'),
        ('student', 'parttime_type', 'TEXT'),
        ('application', 'activity_hours', 'INTEGER DEFAULT 0'),
        ('application', 'parttime_type', 'TEXT')
    ]

    for table, col, col_type in updates:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"Added column {col} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col} already exists in {table}")
            else:
                print(f"Error adding column {col} to {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
