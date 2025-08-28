# PDF 처리 백그라운드 서비스
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from sqlalchemy import text

from services.ocr_service import ocr_service
from app.database import engine

class PDFProcessor:
    def __init__(self):
        self.processing_queue = []
        self.is_processing = False
    
    async def add_to_queue(self, upload_id: int, file_path: str, file_type: str, certificate_id: int):
        """PDF 처리 큐에 추가"""
        job = {
            "upload_id": upload_id,
            "file_path": file_path,
            "file_type": file_type,
            "certificate_id": certificate_id,
            "added_at": datetime.now()
        }
        
        self.processing_queue.append(job)
        print(f"Added PDF processing job for upload_id: {upload_id}")
        
        # 처리 시작 (백그라운드)
        if not self.is_processing:
            asyncio.create_task(self.process_queue())
    
    async def process_queue(self):
        """큐에 있는 PDF들을 순차적으로 처리"""
        if self.is_processing:
            return
        
        self.is_processing = True
        
        try:
            while self.processing_queue:
                job = self.processing_queue.pop(0)
                await self.process_single_pdf(job)
        except Exception as e:
            print(f"Error processing PDF queue: {e}")
        finally:
            self.is_processing = False
    
    async def process_single_pdf(self, job: Dict[str, Any]):
        """개별 PDF 처리"""
        upload_id = job["upload_id"]
        file_path = job["file_path"]
        file_type = job["file_type"]
        certificate_id = job["certificate_id"]
        
        print(f"Processing PDF: {file_path}")
        
        with engine.connect() as conn:
            try:
                # 처리 상태를 'processing'으로 업데이트
                conn.execute(
                    text("UPDATE pdf_uploads SET processing_status = 'processing' WHERE id = :id"),
                    {"id": upload_id}
                )
                conn.commit()
                
                # OCR 처리 실행
                result = ocr_service.process_pdf(file_path, file_type)
                
                if result["success"]:
                    # 추출된 문제들을 데이터베이스에 저장
                    if result["extracted_questions"]:
                        await self.save_extracted_questions(conn, upload_id, certificate_id, result["extracted_questions"])
                    
                    # 추출된 학습자료들을 데이터베이스에 저장
                    if result["study_materials"]:
                        await self.save_study_materials(conn, upload_id, certificate_id, result["study_materials"])
                    
                    # 처리 완료 상태 업데이트
                    processing_result = {
                        "total_pages": result["total_pages"],
                        "extracted_questions": len(result["extracted_questions"]),
                        "study_materials": len(result["study_materials"]),
                        "processing_errors": result["processing_errors"],
                        "processed_at": result["processed_at"]
                    }
                    
                    conn.execute(
                        text("""
                            UPDATE pdf_uploads 
                            SET processing_status = 'completed', 
                                processed_date = CURRENT_TIMESTAMP,
                                processing_result = :result
                            WHERE id = :id
                        """),
                        {
                            "id": upload_id,
                            "result": str(processing_result)  # JSON 형태로 저장
                        }
                    )
                    conn.commit()
                    
                    print(f"PDF processing completed for upload_id: {upload_id}")
                    print(f"  - Questions extracted: {len(result['extracted_questions'])}")
                    print(f"  - Study materials: {len(result['study_materials'])}")
                
                else:
                    # 처리 실패
                    conn.execute(
                        text("""
                            UPDATE pdf_uploads 
                            SET processing_status = 'failed',
                                processing_result = :result
                            WHERE id = :id
                        """),
                        {
                            "id": upload_id,
                            "result": str(result["processing_errors"])
                        }
                    )
                    conn.commit()
                    print(f"PDF processing failed for upload_id: {upload_id}")
                
            except Exception as e:
                # 오류 발생시 실패 상태로 업데이트
                conn.execute(
                    text("""
                        UPDATE pdf_uploads 
                        SET processing_status = 'failed',
                            processing_result = :result
                        WHERE id = :id
                    """),
                    {
                        "id": upload_id,
                        "result": f"Processing error: {str(e)}"
                    }
                )
                conn.commit()
                print(f"Error processing PDF {upload_id}: {e}")
    
    async def save_extracted_questions(self, conn, upload_id: int, certificate_id: int, questions: list):
        """추출된 문제들을 데이터베이스에 저장"""
        for question in questions:
            try:
                conn.execute(
                    text("""
                        INSERT INTO extracted_questions 
                        (pdf_upload_id, certificate_id, question_number, question_text, options, 
                         question_type, has_image, difficulty_level, topic_category)
                        VALUES 
                        (:pdf_upload_id, :certificate_id, :question_number, :question_text, :options,
                         :question_type, :has_image, :difficulty_level, :topic_category)
                    """),
                    {
                        "pdf_upload_id": upload_id,
                        "certificate_id": certificate_id,
                        "question_number": question.get("question_number", 0),
                        "question_text": question.get("question_text", ""),
                        "options": str(question.get("options", [])),  # JSON 문자열로 저장
                        "question_type": "multiple_choice",
                        "has_image": question.get("has_image", False),
                        "difficulty_level": question.get("difficulty_level", 1),
                        "topic_category": question.get("topic_category", "기타")
                    }
                )
            except Exception as e:
                print(f"Error saving question: {e}")
    
    async def save_study_materials(self, conn, upload_id: int, certificate_id: int, materials: list):
        """추출된 학습자료들을 데이터베이스에 저장"""
        for material in materials:
            try:
                conn.execute(
                    text("""
                        INSERT INTO study_materials 
                        (pdf_upload_id, certificate_id, title, content, content_type, 
                         chapter_number, section_number)
                        VALUES 
                        (:pdf_upload_id, :certificate_id, :title, :content, :content_type,
                         :chapter_number, :section_number)
                    """),
                    {
                        "pdf_upload_id": upload_id,
                        "certificate_id": certificate_id,
                        "title": material.get("title", ""),
                        "content": material.get("content", ""),
                        "content_type": material.get("content_type", "theory"),
                        "chapter_number": material.get("chapter_number"),
                        "section_number": material.get("section_number", 1)
                    }
                )
            except Exception as e:
                print(f"Error saving study material: {e}")
    
    def get_processing_status(self, upload_id: int) -> Dict[str, Any]:
        """처리 상태 조회"""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT processing_status, processing_result FROM pdf_uploads WHERE id = :id"),
                {"id": upload_id}
            ).fetchone()
            
            if result:
                return {
                    "status": result.processing_status,
                    "result": result.processing_result
                }
            else:
                return {"status": "not_found", "result": None}

# 글로벌 PDF 프로세서 인스턴스
pdf_processor = PDFProcessor()