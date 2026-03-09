"""เพิ่มคอลัมน์ total_score และ is_scored ในตาราง application (ใช้ครั้งเดียว)"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "scholarship.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(application)")
    cols = [row[1] for row in cur.fetchall()]
    if "total_score" not in cols:
        cur.execute("ALTER TABLE application ADD COLUMN total_score REAL")
        print("Added total_score")
    if "is_scored" not in cols:
        cur.execute("ALTER TABLE application ADD COLUMN is_scored INTEGER DEFAULT 0")
        print("Added is_scored")
    if "notes" not in cols:
        cur.execute("ALTER TABLE application ADD COLUMN notes TEXT")
        print("Added notes")
    conn.commit()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    migrate()
