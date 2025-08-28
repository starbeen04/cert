#!/usr/bin/env python3
import sqlite3

try:
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT username, role, is_active FROM users;')
    users = cursor.fetchall()
    
    print('Users in database:')
    for username, role, is_active in users:
        print(f'  - {username}: {role} (active: {is_active})')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')