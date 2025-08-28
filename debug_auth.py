#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    # Check table structure
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    print("\nTesting user lookup:")
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE username = ?", ("test_instructor",))
    user = cursor.fetchone()
    if user:
        print(f"Found user: {user}")
    else:
        print("User not found")
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')