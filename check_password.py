#!/usr/bin/env python3
import sqlite3
import hashlib

def simple_hash(password: str) -> str:
    """Same hash function as in auth.py"""
    return hashlib.sha256(password.encode()).hexdigest()

try:
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    # Check all users and their password hashes
    cursor.execute('SELECT username, hashed_password FROM users;')
    users = cursor.fetchall()
    
    print('Users and password verification:')
    for username, stored_hash in users:
        if username == 'test_instructor':
            test_password = 'instructor123'
            computed_hash = simple_hash(test_password)
            print(f'  {username}:')
            print(f'    Stored hash:   {stored_hash}')
            print(f'    Computed hash: {computed_hash}')
            print(f'    Match: {stored_hash == computed_hash}')
        elif username == 'admin':
            test_password = 'admin123'
            computed_hash = simple_hash(test_password)
            print(f'  {username}:')
            print(f'    Stored hash:   {stored_hash}')
            print(f'    Computed hash: {computed_hash}')
            print(f'    Match: {stored_hash == computed_hash}')
        else:
            print(f'  {username}: (hash present)')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')