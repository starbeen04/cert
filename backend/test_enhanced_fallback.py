#!/usr/bin/env python3
"""
Enhanced PDF Processor Fallback 테스트
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.enhanced_pdf_processor import EnhancedPDFProcessor
from app.database_sqlite import get_db
from sqlalchemy.orm import Session

async def test_enhanced_processor():
    """Enhanced PDF Processor 테스트"""
    print("=== Enhanced PDF Processor 테스트 ===")
    
    # 테스트할 PDF 파일 찾기
    test_files = [
        "uploads/pdfs/20250819_230927_9d999864_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
        "uploads/pdfs/20250819_233440_bcacb893_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
        "uploads/pdfs/20250820_001326_21d9c23d_2. 2024년2회_정보처리산업기사필기 기출문제.pdf",
    ]
    
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            print(f"[발견] 테스트 파일: {file_path}")
            break
    
    if not test_file:
        print("[오류] 테스트할 PDF 파일을 찾을 수 없습니다.")
        return
    
    # 가상의 데이터베이스 세션 생성 (모든 필요한 테이블이 있다고 가정)
    processor = EnhancedPDFProcessor()
    
    print(f"\n[테스트] {test_file} 처리 시작...")
    
    try:
        # 가짜 데이터베이스 세션 생성 (실제로는 필요하지 않음)
        class MockDB:
            def query(self, *args):
                class MockQuery:
                    def filter(self, *args):
                        return self
                    def first(self):
                        # 가짜 AI 에이전트 반환
                        class MockAgent:
                            def __init__(self, name):
                                self.id = 1
                                self.agent_type = name
                                self.name = name
                                self.prompt_template = "Test prompt"
                                self.model = "claude-3-sonnet-20240229"
                                self.temperature = 0.3
                                self.max_tokens = 4000
                        
                        # 에이전트 타입에 따라 적절한 모의 에이전트 반환
                        return MockAgent("test_agent")
                return MockQuery()
            
            def add(self, obj):
                pass
                
            def commit(self):
                pass
                
            def close(self):
                pass
        
        mock_db = MockDB()
        
        # Enhanced PDF Processor 실행
        result = await processor.process_pdf_with_enhanced_pipeline(
            upload_id=999,  # 가짜 ID
            file_path=test_file,
            file_type="application/pdf",
            db=mock_db
        )
        
        print(f"\n=== 처리 결과 ===")
        if result.get("success"):
            print(f"[성공] 처리 완료")
            print(f"   - 총 문제 수: {result.get('total_questions', 0)}개")
            print(f"   - 처리 방법: {result.get('processing_method', 'unknown')}")
            print(f"   - Fallback 사용: {result.get('fallback_used', False)}")
            print(f"   - 비용: {result.get('cost', 0)}")
            
            questions = result.get('questions', [])
            if questions:
                print(f"\n[처음 3개 문제 미리보기]")
                for i, q in enumerate(questions[:3]):
                    print(f"문제 {i+1}:")
                    print(f"  번호: {q.get('question_number', 'N/A')}")
                    print(f"  지문: {'있음' if q.get('passage') else '없음'}")
                    print(f"  문제: {str(q.get('question_text', ''))[:60]}...")
                    print(f"  선택지: {len(q.get('options', []))}개")
                    print()
        else:
            print(f"[실패] {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"[오류] 처리 중 예외 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_processor())