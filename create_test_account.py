#!/usr/bin/env python3
"""
CertFast 테스트 계정 생성 스크립트
"""
import sqlite3
import hashlib
from datetime import datetime

def create_database_tables():
    """데이터베이스 테이블 생성"""
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    # Users 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'student',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Certificates 테이블 생성  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            difficulty_level TEXT,
            issuer TEXT,
            exam_duration_minutes INTEGER,
            passing_score INTEGER,
            total_questions INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # API Keys 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            api_key TEXT NOT NULL,
            monthly_limit REAL DEFAULT 0,
            current_monthly_usage REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 테이블 생성 완료")

def create_test_accounts():
    """테스트 계정 생성"""
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # 관리자 계정
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', 'admin@certfast.com', admin_password, '관리자', 'admin', 1, now, now))
    
    # 학습자 계정
    student_password = hashlib.sha256("student123".encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('test_student', 'student@certfast.com', student_password, '테스트 학습자', 'student', 1, now, now))
    
    # 강사 계정
    instructor_password = hashlib.sha256("instructor123".encode()).hexdigest()
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (username, email, hashed_password, full_name, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('test_instructor', 'instructor@certfast.com', instructor_password, '테스트 강사', 'instructor', 1, now, now))
    
    conn.commit()
    conn.close()
    print("✅ 테스트 계정 생성 완료")

def create_sample_certificates():
    """샘플 자격증 데이터 생성"""
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    certificates = [
        {
            'title': 'AWS Solutions Architect Associate',
            'description': 'AWS 클라우드에서 확장 가능하고 안전한 애플리케이션을 설계하고 배포하는 능력을 검증하는 자격증',
            'category': 'Cloud',
            'difficulty_level': 'intermediate',
            'issuer': 'Amazon Web Services',
            'exam_duration_minutes': 130,
            'passing_score': 72,
            'total_questions': 65
        },
        {
            'title': 'Google Cloud Professional Cloud Architect',
            'description': 'Google Cloud Platform을 사용하여 클라우드 솔루션을 설계하고 관리하는 전문가 자격증',
            'category': 'Cloud',
            'difficulty_level': 'advanced',
            'issuer': 'Google Cloud',
            'exam_duration_minutes': 120,
            'passing_score': 70,
            'total_questions': 50
        },
        {
            'title': 'Microsoft Azure Fundamentals',
            'description': 'Microsoft Azure의 기본 개념과 서비스에 대한 기초 지식을 검증하는 자격증',
            'category': 'Cloud',
            'difficulty_level': 'Beginner',
            'issuer': 'Microsoft',
            'exam_duration_minutes': 85,
            'passing_score': 70,
            'total_questions': 40
        },
        {
            'title': 'CISSP (Certified Information Systems Security Professional)',
            'description': '정보 시스템 보안 전문가를 위한 국제적으로 인정받는 고급 보안 자격증',
            'category': 'Security',
            'difficulty_level': 'Expert',
            'issuer': '(ISC)²',
            'exam_duration_minutes': 180,
            'passing_score': 70,
            'total_questions': 125
        },
        {
            'title': 'CompTIA Security+',
            'description': 'IT 보안 분야의 기초 지식과 실무 능력을 검증하는 벤더 중립적 자격증',
            'category': 'Security',
            'difficulty_level': 'intermediate',
            'issuer': 'CompTIA',
            'exam_duration_minutes': 90,
            'passing_score': 75,
            'total_questions': 90
        }
    ]
    
    for cert in certificates:
        cursor.execute('''
            INSERT OR REPLACE INTO certificates 
            (title, description, category, difficulty_level, issuer, 
             exam_duration_minutes, passing_score, total_questions, 
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cert['title'], cert['description'], cert['category'], 
            cert['difficulty_level'], cert['issuer'],
            cert['exam_duration_minutes'], cert['passing_score'], cert['total_questions'],
            1, now, now
        ))
    
    conn.commit()
    conn.close()
    print("✅ 샘플 자격증 데이터 생성 완료")

def create_sample_api_keys():
    """샘플 API 키 데이터 생성"""
    conn = sqlite3.connect('cert_fast_test.db')
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    api_keys = [
        {
            'key_name': 'Claude API Key',
            'provider': 'Anthropic',
            'api_key': 'sk-ant-api03-test-key-for-demo-purposes-only',
            'monthly_limit': 1000.0,
            'current_monthly_usage': 150.0
        },
        {
            'key_name': 'OpenAI API Key',
            'provider': 'OpenAI',
            'api_key': 'sk-test-key-for-demo-purposes-only',
            'monthly_limit': 500.0,
            'current_monthly_usage': 80.0
        }
    ]
    
    for api_key in api_keys:
        cursor.execute('''
            INSERT OR REPLACE INTO api_keys 
            (key_name, provider, api_key, monthly_limit, current_monthly_usage, 
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            api_key['key_name'], api_key['provider'], api_key['api_key'],
            api_key['monthly_limit'], api_key['current_monthly_usage'],
            1, now, now
        ))
    
    conn.commit()
    conn.close()
    print("✅ 샘플 API 키 데이터 생성 완료")

def main():
    """메인 함수"""
    print("🚀 CertFast 테스트 데이터 생성을 시작합니다...")
    
    # 1. 데이터베이스 테이블 생성
    create_database_tables()
    
    # 2. 테스트 계정 생성
    create_test_accounts()
    
    # 3. 샘플 자격증 데이터 생성
    create_sample_certificates()
    
    # 4. 샘플 API 키 데이터 생성
    create_sample_api_keys()
    
    print("\n🎉 테스트 데이터 생성이 완료되었습니다!")
    print("\n📋 생성된 테스트 계정:")
    print("   관리자 계정:")
    print("   - 사용자명: admin")
    print("   - 비밀번호: admin123")
    print("   - 이메일: admin@certfast.com")
    print("")
    print("   학습자 계정:")
    print("   - 사용자명: test_student")
    print("   - 비밀번호: student123")
    print("   - 이메일: student@certfast.com")
    print("")
    print("   강사 계정:")
    print("   - 사용자명: test_instructor")
    print("   - 비밀번호: instructor123")
    print("   - 이메일: instructor@certfast.com")
    print("\n💡 이제 프론트엔드에서 이 계정으로 로그인할 수 있습니다!")

if __name__ == "__main__":
    main()