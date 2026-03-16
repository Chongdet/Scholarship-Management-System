"""เพิ่มคอลัมน์ที่ขาดหายไปในตาราง scholarship (ใช้ครั้งเดียว)"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "scholarship.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(scholarship)")
    cols = [row[1] for row in cur.fetchall()]
    print(f"Existing columns: {cols}")

    # Columns to add: (column_name, definition)
    to_add = [
        ("number_of_scholarships", "INTEGER"),
        ("scholarship_type",       "TEXT"),
        ("provider",               "TEXT"),
        ("interview_file_url",     "TEXT"),
        ("announce_file_url",      "TEXT"),
        ("image",                  "TEXT"),
        ("qualifications",         "TEXT"),
        ("conditions",             "TEXT"),
        ("scholarship_nature",     "TEXT"),
        ("required_documents",     "TEXT"),
    ]

    for col_name, col_def in to_add:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE scholarship ADD COLUMN {col_name} {col_def}")
            print(f"Added: {col_name}")
        else:
            print(f"Already exists: {col_name}")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
