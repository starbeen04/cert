#!/usr/bin/env python3
"""
CertFast 테스트 계정 비밀번호 해싱 수정 스크립트 (bcrypt 사용)
"""
import sqlite3
from passlib.context import CryptContext
from datetime import datetime

def fix_test_accounts():
    """테스트 계정의 비밀번호를 bcrypt로 다시 해싱"""
    # bcrypt 컨텍스트 생성
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # 관리자 계정 비밀번호 업데이트
    admin_password_hash = pwd_context.hash("admin123")
    cursor.execute('''
        UPDATE users SET hashed_password = ?, updated_at = ?
        WHERE username = 'admin'
    ''', (admin_password_hash, now))
    
    # 학습자 계정 비밀번호 업데이트  
    student_password_hash = pwd_context.hash("student123")
    cursor.execute('''
        UPDATE users SET hashed_password = ?, updated_at = ?
        WHERE username = 'test_student'
    ''', (student_password_hash, now))
    
    conn.commit()
    
    # 업데이트된 계정 확인
    cursor.execute('SELECT username, email, role FROM users')
    accounts = cursor.fetchall()
    
    conn.close()
    
    print("✅ 테스트 계정 비밀번호가 bcrypt로 업데이트되었습니다!")
    print("\n📋 업데이트된 계정:")
    for account in accounts:
        username, email, role = account
        password = "admin123" if username == "admin" else "student123"
        print(f"   - {username} ({role}): {email} / 비밀번호: {password}")

def main():
    print("🔧 테스트 계정 비밀번호 해싱 수정 중...")
    fix_test_accounts()
    print("\n💡 이제 올바른 비밀번호로 로그인할 수 있습니다!")

if __name__ == "__main__":
    main()