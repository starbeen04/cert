#!/usr/bin/env python3
"""
직접 백엔드 인증 함수들을 테스트해보기
"""
import sqlite3
import hashlib
from types import SimpleNamespace

def simple_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return simple_hash(plain_password) == hashed_password

def get_user_by_username(username: str):
    import sqlite3
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    print(f"Raw result for {username}: {result}")
    
    if result:
        # Table structure: id, username, email, hashed_password, full_name, role, is_active, created_at, updated_at
        user_data = SimpleNamespace()
        user_data.id = result[0]
        user_data.username = result[1] 
        user_data.email = result[2]
        user_data.hashed_password = result[3]
        user_data.full_name = result[4]
        user_data.role = result[5]
        user_data.is_active = result[6]
        user_data.created_at = result[7] if len(result) > 7 else None
        user_data.updated_at = result[8] if len(result) > 8 else None
        return user_data
    return None

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        print(f"User {username} not found")
        return False
    
    print(f"User found: {user.username}, role: {user.role}")
    print(f"Stored password hash: {user.hashed_password}")
    print(f"Computed hash: {simple_hash(password)}")
    
    if not verify_password(password, user.hashed_password):
        print("Password verification failed")
        return False
    print("Password verification successful")
    return user

# Test authentication
print("Testing authentication:")
print("=" * 50)

print("\n1. Testing admin login:")
admin_result = authenticate_user('admin', 'admin123')
print(f"Result: {admin_result}")

print("\n2. Testing instructor login:")
instructor_result = authenticate_user('test_instructor', 'instructor123')
print(f"Result: {instructor_result}")

print("\n3. Testing student login:")
student_result = authenticate_user('test_student', 'student123')
print(f"Result: {student_result}")