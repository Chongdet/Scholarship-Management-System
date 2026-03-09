import sqlite3

conn = sqlite3.connect('scholarship.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:", tables)

# Check audit_log
if 'audit_log' in tables:
    cursor.execute("SELECT COUNT(*) FROM audit_log")
    count = cursor.fetchone()[0]
    print(f"\naudit_log table has {count} rows")
    
    if count > 0:
        cursor.execute("SELECT * FROM audit_log LIMIT 3")
        print("\nSample data:")
        for row in cursor.fetchall():
            print(row)
else:
    print("\naudit_log table does NOT exist!")

conn.close()
