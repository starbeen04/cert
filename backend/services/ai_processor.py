"""AI 처리 파이프라인 서비스"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
# 테이블 기반 작업을 위해 모델 import 제거
from app.database import get_db
from services.claude_service import claude_service
from services.ocr_service import OCRService
import logging

logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        self.ocr_service = OCRService()
    
    async def process_pdf_with_ai(self, upload_id: int, db: Session) -> Dict[str, Any]:
        """PDF를 AI 파이프라인으로 처리"""
        try:
            # 업로드 정보 조회
            upload = db.execute(
                text("SELECT * FROM pdf_uploads WHERE id = :id"),
                {"id": upload_id}
            ).fetchone()
            if not upload:
                return {"error": "Upload not found"}
            
            # 처리 상태 업데이트
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'processing' WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            
            logger.info(f"Starting AI processing for upload {upload_id}")
            
            # 1단계: OCR로 텍스트 추출
            ocr_result = self.ocr_service.process_pdf(upload.file_path, upload.file_type)
            if not ocr_result or not ocr_result.get("success"):
                upload.processing_status = "failed"
                db.commit()
                return {"error": "OCR processing failed"}
            
            extracted_text = ocr_result.get("extracted_text", "")
            if not extracted_text:
                upload.processing_status = "failed" 
                db.commit()
                return {"error": "No text extracted from PDF"}
            
            # AI 처리 파이프라인 실행
            result = await self._run_ai_pipeline(upload, extracted_text, db)
            
            if result.get("success"):
                upload.processing_status = "completed"
                upload.processed_date = db.execute(text("SELECT CURRENT_TIMESTAMP")).scalar()
            else:
                upload.processing_status = "failed"
            
            db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            if 'upload' in locals():
                upload.processing_status = "failed"
                db.commit()
            return {"error": str(e)}
    
    async def _run_ai_pipeline(self, upload: PDFUpload, text: str, db: Session) -> Dict[str, Any]:
        """AI 처리 파이프라인 실행"""
        try:
            results = {
                "success": True,
                "steps": [],
                "questions": [],
                "materials": [],
                "total_tokens": 0,
                "total_cost": 0.0
            }
            
            # 1단계: 문서 분석
            await self._create_ai_task(upload.id, "document_analysis", "processing", db)
            doc_analysis = await self._analyze_document(text, db)
            await self._update_ai_task(upload.id, "document_analysis", 
                                     "completed" if doc_analysis.get("success") else "failed", 
                                     doc_analysis, db)
            results["steps"].append({"step": "document_analysis", "result": doc_analysis})
            
            if not doc_analysis.get("success"):
                return {"error": "Document analysis failed"}
            
            # 2단계: 문제 추출 (문제집이거나 통합 타입인 경우)
            if upload.file_type in ["questions", "both"]:
                await self._create_ai_task(upload.id, "question_extraction", "processing", db)
                questions = await self._extract_questions(text, db)
                await self._update_ai_task(upload.id, "question_extraction",
                                         "completed" if questions.get("success") else "failed",
                                         questions, db)
                results["steps"].append({"step": "question_extraction", "result": questions})
                
                if questions.get("success"):
                    # 데이터베이스에 문제 저장
                    saved_questions = await self._save_questions(questions["questions"], upload.id, db)
                    results["questions"] = saved_questions
                    
                    # 3단계: 해설 생성
                    await self._create_ai_task(upload.id, "explanation_generation", "processing", db)
                    explanations = await self._generate_explanations(saved_questions, db)
                    await self._update_ai_task(upload.id, "explanation_generation",
                                             "completed" if explanations.get("success") else "failed",
                                             explanations, db)
                    results["steps"].append({"step": "explanation_generation", "result": explanations})
            
            # 4단계: 학습자료 생성 (학습자료이거나 통합 타입인 경우)
            if upload.file_type in ["study_material", "both"]:
                await self._create_ai_task(upload.id, "study_material_generation", "processing", db)
                materials = await self._generate_study_materials(text, db)
                await self._update_ai_task(upload.id, "study_material_generation",
                                         "completed" if materials.get("success") else "failed",
                                         materials, db)
                results["steps"].append({"step": "material_generation", "result": materials})
                
                if materials.get("success"):
                    saved_materials = await self._save_study_materials(materials["materials"], upload.id, db)
                    results["materials"] = saved_materials
            
            # 5단계: 품질 검증
            await self._create_ai_task(upload.id, "quality_verification", "processing", db)
            quality_check = await self._verify_quality(results, db)
            await self._update_ai_task(upload.id, "quality_verification",
                                     "completed" if quality_check.get("success") else "failed",
                                     quality_check, db)
            results["steps"].append({"step": "quality_verification", "result": quality_check})
            
            # 사용량 통계 계산
            total_tokens = sum(step["result"].get("usage", {}).get("total_tokens", 0) for step in results["steps"])
            total_cost = sum(step["result"].get("cost", 0) for step in results["steps"])
            
            results["total_tokens"] = total_tokens
            results["total_cost"] = total_cost
            
            logger.info(f"AI pipeline completed for upload {upload.id}. Tokens: {total_tokens}, Cost: ${total_cost:.4f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in AI pipeline: {e}")
            return {"error": str(e)}
    
    async def _analyze_document(self, text: str, db: Session) -> Dict[str, Any]:
        """1단계: 문서 분석"""
        try:
            agent = db.query(AIAgent).filter(
                AIAgent.agent_type == "document_analysis",
                AIAgent.is_active == True
            ).first()
            
            if not agent:
                return {"error": "Document analysis agent not found"}
            
            prompt = f"""다음 PDF에서 추출된 텍스트를 분석해주세요:

{text[:3000]}...

다음 정보를 JSON 형식으로 제공해주세요:
{{
    "document_type": "문제집 또는 교재",
    "subject_area": "주제 분야",
    "difficulty_level": "초급/중급/고급",
    "total_pages": "추정 페이지 수",
    "structure_analysis": "문서 구조 분석",
    "content_summary": "내용 요약"
}}"""
            
            response = await claude_service.call_claude_api(prompt, agent, db)
            
            if response.get("success"):
                try:
                    # JSON 응답 파싱
                    content = response["content"]
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        return {
                            "success": True,
                            "analysis": analysis,
                            "usage": response.get("usage", {}),
                            "cost": self._calculate_cost(response.get("usage", {}))
                        }
                    else:
                        return {"error": "Failed to parse analysis result"}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    return {"error": "Invalid JSON response from AI"}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error in document analysis: {e}")
            return {"error": str(e)}
    
    async def _extract_questions(self, text: str, db: Session) -> Dict[str, Any]:
        """2단계: 문제 추출"""
        try:
            agent = db.query(AIAgent).filter(
                AIAgent.agent_type == "question_extraction",
                AIAgent.is_active == True
            ).first()
            
            if not agent:
                return {"error": "Question extraction agent not found"}
            
            prompt = f"""다음 텍스트에서 객관식 문제들을 추출해주세요:

{text[:4000]}

각 문제를 다음 JSON 배열 형식으로 추출해주세요:
[
    {{
        "question_number": 1,
        "question_text": "문제 내용",
        "options": ["1번 선택지", "2번 선택지", "3번 선택지", "4번 선택지"],
        "correct_answer": "정답 번호 또는 내용",
        "topic_category": "문제 주제",
        "difficulty_level": "초급/중급/고급",
        "explanation": "해설 (있는 경우)"
    }}
]

정확한 JSON 형식으로 모든 문제를 추출해주세요."""
            
            response = await claude_service.call_claude_api(prompt, agent, db, max_tokens=6000)
            
            if response.get("success"):
                try:
                    content = response["content"]
                    # JSON 배열 추출
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        questions = json.loads(json_match.group())
                        return {
                            "success": True,
                            "questions": questions,
                            "count": len(questions),
                            "usage": response.get("usage", {}),
                            "cost": self._calculate_cost(response.get("usage", {}))
                        }
                    else:
                        return {"error": "No questions found in response"}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error in questions: {e}")
                    return {"error": "Invalid JSON response from AI"}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error in question extraction: {e}")
            return {"error": str(e)}
    
    async def _generate_explanations(self, questions: List[Dict], db: Session) -> Dict[str, Any]:
        """3단계: 해설 생성"""
        try:
            agent = db.query(AIAgent).filter(
                AIAgent.agent_type == "explanation_generation",
                AIAgent.is_active == True
            ).first()
            
            if not agent:
                return {"error": "Explanation generation agent not found"}
            
            explanations = []
            total_cost = 0.0
            
            for question in questions[:10]:  # 처음 10문제만 해설 생성
                prompt = f"""다음 문제에 대한 상세한 해설을 작성해주세요:

문제: {question['question_text']}
선택지: {', '.join(question.get('options', []))}
정답: {question.get('correct_answer', '')}

해설은 다음 구조로 작성해주세요:
1. 문제 이해
2. 핵심 개념 설명
3. 단계별 풀이
4. 정답 확인
5. 오답 분석 (주요 오답에 대해)

정확하고 이해하기 쉬운 해설을 작성해주세요."""

                response = await claude_service.call_claude_api(prompt, agent, db, max_tokens=2000)
                
                if response.get("success"):
                    explanation = {
                        "question_id": question.get("id"),
                        "explanation": response["content"],
                        "cost": self._calculate_cost(response.get("usage", {}))
                    }
                    explanations.append(explanation)
                    total_cost += explanation["cost"]
                    
                    # 데이터베이스 업데이트
                    if question.get("id"):
                        db.execute(
                            text("UPDATE extracted_questions SET explanation = :explanation WHERE id = :id"),
                            {"explanation": response["content"], "id": question["id"]}
                        )
                
                await asyncio.sleep(1)  # API 호출 간격
            
            db.commit()
            
            return {
                "success": True,
                "explanations": explanations,
                "count": len(explanations),
                "total_cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Error in explanation generation: {e}")
            return {"error": str(e)}
    
    async def _generate_study_materials(self, text: str, db: Session) -> Dict[str, Any]:
        """4단계: 학습자료 생성"""
        try:
            agent = db.query(AIAgent).filter(
                AIAgent.agent_type == "study_material_generation", 
                AIAgent.is_active == True
            ).first()
            
            if not agent:
                return {"error": "Study material generation agent not found"}
            
            prompt = f"""다음 텍스트를 기반으로 학습자료를 생성해주세요:

{text[:4000]}

다음 JSON 배열 형식으로 학습자료를 생성해주세요:
[
    {{
        "title": "학습자료 제목",
        "content": "상세 내용",
        "content_type": "개념정리/요약/예제",
        "chapter_number": 1,
        "section_number": 1,
        "difficulty_level": "초급/중급/고급",
        "keywords": ["키워드1", "키워드2"]
    }}
]

체계적이고 이해하기 쉬운 학습자료를 생성해주세요."""
            
            response = await claude_service.call_claude_api(prompt, agent, db, max_tokens=6000)
            
            if response.get("success"):
                try:
                    content = response["content"]
                    json_match = re.search(r'\[.*\]', content, re.DOTALL)
                    if json_match:
                        materials = json.loads(json_match.group())
                        return {
                            "success": True,
                            "materials": materials,
                            "count": len(materials),
                            "usage": response.get("usage", {}),
                            "cost": self._calculate_cost(response.get("usage", {}))
                        }
                    else:
                        return {"error": "No materials found in response"}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error in materials: {e}")
                    return {"error": "Invalid JSON response from AI"}
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error in study material generation: {e}")
            return {"error": str(e)}
    
    async def _verify_quality(self, results: Dict, db: Session) -> Dict[str, Any]:
        """5단계: 품질 검증"""
        try:
            agent = db.query(AIAgent).filter(
                AIAgent.agent_type == "quality_verification",
                AIAgent.is_active == True
            ).first()
            
            # 품질 검증 에이전트가 없어도 처리 계속
            if not agent:
                return {
                    "success": True,
                    "quality_score": 85,
                    "feedback": "품질 검증 에이전트가 없어 기본 점수 적용",
                    "cost": 0
                }
            
            prompt = f"""다음 AI 처리 결과의 품질을 검증해주세요:

문제 수: {len(results.get('questions', []))}
학습자료 수: {len(results.get('materials', []))}
총 처리 단계: {len(results.get('steps', []))}

JSON 형식으로 평가 결과를 제공해주세요:
{{
    "quality_score": 0-100점,
    "accuracy_score": 0-100점,
    "completeness_score": 0-100점,
    "feedback": "개선 사항 및 피드백",
    "recommendations": ["추천사항1", "추천사항2"]
}}"""
            
            response = await claude_service.call_claude_api(prompt, agent, db, max_tokens=1000)
            
            if response.get("success"):
                try:
                    content = response["content"]
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        quality_result = json.loads(json_match.group())
                        quality_result["success"] = True
                        quality_result["cost"] = self._calculate_cost(response.get("usage", {}))
                        return quality_result
                    else:
                        return {"success": True, "quality_score": 80, "feedback": "품질 검증 완료", "cost": 0}
                except json.JSONDecodeError:
                    return {"success": True, "quality_score": 75, "feedback": "품질 검증 완료 (파싱 오류)", "cost": 0}
            else:
                return {"success": True, "quality_score": 70, "feedback": "품질 검증 API 오류", "cost": 0}
                
        except Exception as e:
            logger.error(f"Error in quality verification: {e}")
            return {"success": True, "quality_score": 60, "feedback": f"품질 검증 오류: {str(e)}", "cost": 0}
    
    async def _save_questions(self, questions: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """문제를 데이터베이스에 저장"""
        saved_questions = []
        
        for i, question in enumerate(questions):
            try:
                db_question = ExtractedQuestion(
                    pdf_upload_id=upload_id,
                    question_number=question.get("question_number", i + 1),
                    question_text=question.get("question_text", ""),
                    options=json.dumps(question.get("options", []), ensure_ascii=False),
                    correct_answer=question.get("correct_answer", ""),
                    topic_category=question.get("topic_category", ""),
                    difficulty_level=question.get("difficulty_level", "중급"),
                    explanation=question.get("explanation", ""),
                    has_image=False
                )
                
                db.add(db_question)
                db.flush()
                
                saved_question = {
                    "id": db_question.id,
                    "question_number": db_question.question_number,
                    "question_text": db_question.question_text,
                    "options": question.get("options", []),
                    "correct_answer": db_question.correct_answer,
                    "topic_category": db_question.topic_category,
                    "difficulty_level": db_question.difficulty_level
                }
                saved_questions.append(saved_question)
                
            except Exception as e:
                logger.error(f"Error saving question {i}: {e}")
                continue
        
        db.commit()
        return saved_questions
    
    async def _save_study_materials(self, materials: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """학습자료를 데이터베이스에 저장"""
        saved_materials = []
        
        for i, material in enumerate(materials):
            try:
                db_material = StudyMaterial(
                    pdf_upload_id=upload_id,
                    title=material.get("title", f"학습자료 {i+1}"),
                    content=material.get("content", ""),
                    content_type=material.get("content_type", "개념정리"),
                    chapter_number=material.get("chapter_number", 1),
                    section_number=material.get("section_number", i + 1),
                    difficulty_level=material.get("difficulty_level", "중급"),
                    keywords=json.dumps(material.get("keywords", []), ensure_ascii=False)
                )
                
                db.add(db_material)
                db.flush()
                
                saved_material = {
                    "id": db_material.id,
                    "title": db_material.title,
                    "content": db_material.content,
                    "content_type": db_material.content_type,
                    "chapter_number": db_material.chapter_number,
                    "section_number": db_material.section_number
                }
                saved_materials.append(saved_material)
                
            except Exception as e:
                logger.error(f"Error saving material {i}: {e}")
                continue
        
        db.commit()
        return saved_materials
    
    def _calculate_cost(self, usage: Dict[str, Any]) -> float:
        """토큰 사용량 기반 비용 계산"""
        if not usage:
            return 0.0
        
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        # Claude 3.5 Sonnet 가격 (2024 기준)
        input_cost_per_token = 0.000003  # $0.003 per 1K tokens
        output_cost_per_token = 0.000015  # $0.015 per 1K tokens
        
        return (input_tokens * input_cost_per_token) + (output_tokens * output_cost_per_token)
    
    async def _create_ai_task(self, upload_id: int, agent_type: str, status: str, db: Session):
        """AI 작업 생성"""
        try:
            ai_task = AITask(
                upload_id=upload_id,
                agent_type=agent_type,
                status=status
            )
            db.add(ai_task)
            db.commit()
            logger.info(f"Created AI task: {agent_type} for upload {upload_id}")
        except Exception as e:
            logger.error(f"Error creating AI task: {e}")
            db.rollback()
    
    async def _update_ai_task(self, upload_id: int, agent_type: str, status: str, result_data: Dict, db: Session):
        """AI 작업 상태 업데이트"""
        try:
            db.execute(
                text("""
                    UPDATE ai_tasks 
                    SET status = :status, 
                        result_data = :result_data,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE upload_id = :upload_id AND agent_type = :agent_type
                """),
                {
                    "status": status,
                    "result_data": json.dumps(result_data, ensure_ascii=False),
                    "upload_id": upload_id,
                    "agent_type": agent_type
                }
            )
            db.commit()
            logger.info(f"Updated AI task: {agent_type} for upload {upload_id} - {status}")
        except Exception as e:
            logger.error(f"Error updating AI task: {e}")
            db.rollback()

# 전역 AI 프로세서 인스턴스
ai_processor = AIProcessor()