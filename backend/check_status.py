#!/usr/bin/env python3
"""현재 구현 상태 확인 스크립트"""

from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text
import os

def check_ai_agents():
    """AI 에이전트 상태 확인"""
    try:
        db = next(get_db())
        agents = db.execute(text("SELECT * FROM ai_agents")).fetchall()
        print(f"=== AI Agents ({len(agents)}개) ===")
        for agent in agents:
            status = "Active" if agent.is_active else "Inactive"
            print(f"- {agent.name} ({agent.agent_type}): {status}")
        db.close()
        return len(agents)
    except Exception as e:
        print(f"AI Agents 확인 오류: {e}")
        return 0

def check_api_keys():
    """API 키 상태 확인"""
    try:
        db = next(get_db())
        keys = db.execute(text("SELECT * FROM api_keys")).fetchall()
        print(f"\n=== API Keys ({len(keys)}개) ===")
        for key in keys:
            status = "Active" if key.is_active else "Inactive"
            print(f"- {key.provider} ({key.key_name}): {status}")
        db.close()
        return len(keys)
    except Exception as e:
        print(f"API Keys 확인 오류: {e}")
        return 0

def check_uploaded_files():
    """업로드된 파일 상태 확인"""
    try:
        db = next(get_db())
        files = db.execute(text("SELECT * FROM pdf_uploads ORDER BY upload_date DESC LIMIT 5")).fetchall()
        print(f"\n=== Recent Uploads ({len(files)}개) ===")
        for file in files:
            print(f"- {file.original_name}: {file.processing_status}")
        db.close()
        return len(files)
    except Exception as e:
        print(f"Uploaded Files 확인 오류: {e}")
        return 0

def check_services():
    """서비스 파일들 확인"""
    services_dir = "services"
    print(f"\n=== Services Directory ===")
    if os.path.exists(services_dir):
        services = os.listdir(services_dir)
        key_services = ["claude_service.py", "ai_processor.py", "ocr_service.py"]
        for service in key_services:
            status = "✓ Exists" if service in services else "✗ Missing"
            print(f"- {service}: {status}")
    else:
        print("Services directory not found")

def check_questions_and_materials():
    """추출된 문제와 학습자료 확인"""
    try:
        db = next(get_db())
        
        questions = db.execute(text("SELECT COUNT(*) FROM extracted_questions")).scalar()
        materials = db.execute(text("SELECT COUNT(*) FROM study_materials")).scalar()
        
        print(f"\n=== Content ===")
        print(f"- 추출된 문제: {questions}개")
        print(f"- 학습자료: {materials}개")
        
        db.close()
        return questions, materials
    except Exception as e:
        print(f"Content 확인 오류: {e}")
        return 0, 0

if __name__ == "__main__":
    print("=== CertFast 구현 상태 확인 ===\n")
    
    agents_count = check_ai_agents()
    keys_count = check_api_keys()
    files_count = check_uploaded_files()
    check_services()
    questions_count, materials_count = check_questions_and_materials()
    
    print(f"\n=== 총 요약 ===")
    print(f"- AI 에이전트: {agents_count}개")
    print(f"- API 키: {keys_count}개") 
    print(f"- 업로드 파일: {files_count}개")
    print(f"- 추출 문제: {questions_count}개")
    print(f"- 학습자료: {materials_count}개")