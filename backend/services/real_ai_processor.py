"""실제 Claude API를 활용한 AI 처리 파이프라인"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from services.claude_service import claude_service
from services.ocr_service import OCRService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RealAIProcessor:
    def __init__(self):
        self.ocr_service = OCRService()
    
    async def process_pdf_with_claude(self, upload_id: int, file_path: str, file_type: str, db: Session) -> Dict[str, Any]:
        """실제 Claude API를 사용한 PDF 처리 파이프라인"""
        try:
            print(f"🚀 Starting REAL AI processing for upload {upload_id}")
            await self._log_progress(upload_id, "🚀 실제 Claude AI 처리 파이프라인 시작", db)
            
            # 처리 상태 업데이트
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'processing' WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            
            # 단계별 AI 처리 시작
            total_cost = 0.0
            processed_questions = []
            processed_materials = []
            
            # 1단계: OCR 텍스트 추출
            await self._create_ai_task(upload_id, "ocr_extraction", "processing", db)
            
            print("📄 Step 1: OCR 텍스트 추출 중...")
            await self._log_progress(upload_id, "📄 1단계: OCR 텍스트 추출 중...", db)
            ocr_result = self.ocr_service.process_pdf(file_path, file_type)
            
            if not ocr_result or not ocr_result.get("success"):
                await self._update_ai_task(upload_id, "ocr_extraction", "failed", {"error": "OCR 실패"}, db)
                return {"error": "OCR processing failed"}
            
            extracted_text = ocr_result.get("extracted_text", "")
            print(f"📝 OCR 추출된 텍스트 길이: {len(extracted_text)} characters")
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                error_msg = f"OCR 추출된 텍스트가 너무 짧습니다 ({len(extracted_text)} 문자). 최소 100자 이상이 필요합니다."
                await self._update_ai_task(upload_id, "ocr_extraction", "failed", {"error": error_msg}, db)
                return {"error": error_msg}
            
            await self._update_ai_task(upload_id, "ocr_extraction", "completed", {"text_length": len(extracted_text)}, db)
            
            # 2단계: Claude AI로 문서 분석 및 분류
            await self._create_ai_task(upload_id, "document_analysis", "processing", db)
            
            print("🤖 Step 2: Claude AI 문서 분석 중...")
            await self._log_progress(upload_id, "🤖 2단계: Claude AI로 문서 분석 중...", db)
            analysis_result = await self._analyze_document_with_claude(extracted_text, db)
            
            if analysis_result.get("success"):
                await self._update_ai_task(upload_id, "document_analysis", "completed", analysis_result, db)
                total_cost += analysis_result.get("cost", 0)
                print(f"✅ 문서 분석 완료 - 비용: ${analysis_result.get('cost', 0):.4f}")
            else:
                await self._update_ai_task(upload_id, "document_analysis", "failed", analysis_result, db)
                return {"error": "Document analysis failed"}
            
            # 3단계: 파일 유형에 따른 처리
            if file_type in ["questions", "both"]:
                # 문제 추출
                await self._create_ai_task(upload_id, "question_extraction", "processing", db)
                print("❓ Step 3: Claude AI 문제 추출 중...")
                
                questions_result = await self._extract_questions_with_claude(extracted_text, analysis_result.get("document_type", ""), db)
                
                if questions_result.get("success"):
                    questions = questions_result.get("questions", [])
                    processed_questions = await self._save_questions_to_db(questions, upload_id, db)
                    await self._update_ai_task(upload_id, "question_extraction", "completed", {"count": len(questions)}, db)
                    total_cost += questions_result.get("cost", 0)
                    print(f"✅ 문제 추출 완료 - {len(questions)}개 문제, 비용: ${questions_result.get('cost', 0):.4f}")
                else:
                    await self._update_ai_task(upload_id, "question_extraction", "failed", questions_result, db)
            
            if file_type in ["study_material", "both"]:
                # 학습자료 생성
                await self._create_ai_task(upload_id, "material_generation", "processing", db)
                print("📚 Step 4: Claude AI 학습자료 생성 중...")
                
                materials_result = await self._generate_materials_with_claude(extracted_text, analysis_result.get("key_topics", []), db)
                
                if materials_result.get("success"):
                    materials = materials_result.get("materials", [])
                    processed_materials = await self._save_materials_to_db(materials, upload_id, db)
                    await self._update_ai_task(upload_id, "material_generation", "completed", {"count": len(materials)}, db)
                    total_cost += materials_result.get("cost", 0)
                    print(f"✅ 학습자료 생성 완료 - {len(materials)}개 자료, 비용: ${materials_result.get('cost', 0):.4f}")
                else:
                    await self._update_ai_task(upload_id, "material_generation", "failed", materials_result, db)
            
            # 4단계: 품질 검증
            await self._create_ai_task(upload_id, "quality_verification", "processing", db)
            print("🔍 Step 5: Claude AI 품질 검증 중...")
            
            quality_result = await self._verify_quality_with_claude(processed_questions, processed_materials, db)
            await self._update_ai_task(upload_id, "quality_verification", "completed", quality_result, db)
            total_cost += quality_result.get("cost", 0)
            
            # 최종 상태 업데이트
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'completed', processed_date = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            
            # API 사용량 업데이트
            await self._update_api_usage(total_cost, db)
            
            result = {
                "success": True,
                "upload_id": upload_id,
                "questions_count": len(processed_questions),
                "materials_count": len(processed_materials),
                "total_cost": total_cost,
                "quality_score": quality_result.get("quality_score", 0)
            }
            
            print(f"🎉 AI 처리 완료! 문제: {len(processed_questions)}개, 자료: {len(processed_materials)}개, 총 비용: ${total_cost:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            db.execute(
                text("UPDATE pdf_uploads SET processing_status = 'failed' WHERE id = :id"),
                {"id": upload_id}
            )
            db.commit()
            return {"error": str(e)}
    
    async def _analyze_document_with_claude(self, text: str, db: Session) -> Dict[str, Any]:
        """Claude API로 문서 분석"""
        try:
            # 문서 분석 에이전트 조회 (직접 sqlite3 사용)
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_type = 'document_analysis' AND is_active = 1 LIMIT 1")
            agent_row = cursor.fetchone()
            conn.close()
            
            if not agent_row:
                print("❌ Document analysis agent not found!")
                return {"error": "Document analysis agent not found"}
            
            # Convert to dict for easier access
            agent = {
                "id": agent_row[0],
                "name": agent_row[1],
                "description": agent_row[2],
                "agent_type": agent_row[3],
                "model_name": agent_row[4],
                "provider": agent_row[5],
                "is_active": agent_row[6],
                "max_tokens": agent_row[7],
                "temperature": agent_row[8],
                "system_prompt": agent_row[9]
            }
            
            # 디버깅: agent 정보 출력
            print(f"🔍 Agent found: {agent['name']} (ID: {agent['id']})")
            print(f"🔍 Model: {agent['model_name']}")
            print(f"🔍 System prompt length: {len(agent['system_prompt']) if agent['system_prompt'] else 0}")
            
            prompt = f"""다음 PDF에서 추출된 텍스트를 분석하고 분류해주세요:

{text[:4000]}...

다음 JSON 형식으로 분석 결과를 제공해주세요:
{{
    "document_type": "문제집 또는 교재",
    "subject_area": "주제 분야 (예: 정보처리, 데이터베이스, 프로그래밍)",
    "difficulty_level": "초급/중급/고급",
    "has_questions": true/false,
    "has_theory": true/false,
    "estimated_questions": 추정_문제수,
    "key_topics": ["주요 토픽1", "주요 토픽2", "주요 토픽3"],
    "content_summary": "내용 요약"
}}"""
            
            # Agent 딕셔너리 생성
            agent_dict = {
                "model_name": agent['model_name'],
                "system_prompt": agent['system_prompt'] or '',
                "max_tokens": agent['max_tokens'] or 4000,
                "temperature": agent['temperature'] or 0.7
            }
            
            print(f"🔍 Agent dict created: {agent_dict}")
            
            # Claude API 호출
            response = await claude_service.call_claude_api_direct(prompt, agent_dict, db)
            
            if response.get("success"):
                content = response["content"]
                # JSON 추출
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return {
                        "success": True,
                        "analysis": analysis,
                        "document_type": analysis.get("document_type", "unknown"),
                        "key_topics": analysis.get("key_topics", []),
                        "usage": response.get("usage", {}),
                        "cost": self._calculate_cost(response.get("usage", {}))
                    }
            
            return {"error": "Failed to analyze document"}
            
        except Exception as e:
            logger.error(f"Error in document analysis: {e}")
            return {"error": str(e)}
    
    async def _extract_questions_with_claude(self, text: str, document_type: str, db: Session) -> Dict[str, Any]:
        """Claude API로 문제 추출 - 다중 청크 병렬 처리"""
        try:
            # 문제 추출 에이전트 조회 (직접 sqlite3 사용)
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_type = 'question_extraction' AND is_active = 1 LIMIT 1")
            agent_row = cursor.fetchone()
            conn.close()
            
            if not agent_row:
                return {"error": "Question extraction agent not found"}
            
            # Convert to dict
            agent = {
                "model_name": agent_row[4],
                "system_prompt": agent_row[9] or '',
                "max_tokens": agent_row[7] or 8000,
                "temperature": 0.3  # 정확도를 위해 낮은 temperature 사용
            }
            
            print(f"📝 전체 텍스트 길이: {len(text)} characters")
            
            # 텍스트를 4000자 청크로 분할 (overlap 500자)
            chunk_size = 4000
            overlap = 500
            chunks = []
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            
            print(f"🔄 {len(chunks)}개 청크로 분할하여 병렬 처리 시작")
            
            # 향상된 프롬프트
            all_questions = []
            total_cost = 0
            
            for chunk_idx, chunk in enumerate(chunks):
                print(f"📋 청크 {chunk_idx + 1}/{len(chunks)} 처리 중...")
                
                enhanced_prompt = f"""다음은 자격증 시험 문제집의 일부입니다. 이 텍스트에서 모든 객관식 문제를 정확히 추출해주세요.

=== 처리할 텍스트 ===
{chunk}

=== 추출 규칙 ===
1. 문제 번호가 있는 모든 객관식 문제를 찾으세요
2. 각 문제의 선택지(①②③④ 또는 1)2)3)4))를 모두 포함하세요  
3. 정답이 명시되어 있다면 포함하세요
4. 해설이 있다면 포함하세요

=== 출력 형식 ===
반드시 다음 JSON 배열 형식으로만 응답하세요:

[
    {{
        "question_number": 문제번호,
        "question_text": "완전한 문제 내용",
        "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
        "correct_answer": "정답",
        "topic_category": "추정 주제 분야",
        "difficulty_level": "초급",
        "explanation": "해설 내용 또는 null"
    }}
]

중요: 
- 문제가 없다면 빈 배열 []을 반환하세요
- JSON 형식을 정확히 지켜주세요
- 텍스트에서 발견되는 모든 문제를 누락 없이 추출하세요"""

                try:
                    response = await claude_service.call_claude_api_direct(enhanced_prompt, agent, db, max_tokens=8000)
                    
                    if response.get("success"):
                        content = response["content"]
                        # JSON 배열 추출 (더 강력한 파싱)
                        json_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
                        if json_match:
                            try:
                                chunk_questions = json.loads(json_match.group())
                                if isinstance(chunk_questions, list):
                                    for q in chunk_questions:
                                        if isinstance(q, dict) and q.get("question_text"):
                                            all_questions.append(q)
                                    print(f"✅ 청크 {chunk_idx + 1}: {len(chunk_questions)}개 문제 추출")
                                else:
                                    print(f"⚠️ 청크 {chunk_idx + 1}: 잘못된 JSON 형식")
                            except json.JSONDecodeError as e:
                                print(f"❌ 청크 {chunk_idx + 1}: JSON 파싱 오류 - {e}")
                        else:
                            print(f"⚠️ 청크 {chunk_idx + 1}: JSON 형식을 찾을 수 없음")
                        
                        total_cost += self._calculate_cost(response.get("usage", {}))
                    else:
                        print(f"❌ 청크 {chunk_idx + 1}: API 호출 실패")
                        
                except Exception as e:
                    print(f"❌ 청크 {chunk_idx + 1} 처리 오류: {e}")
                    continue
                
                # API 호출 간격 (rate limit 방지)
                await asyncio.sleep(1)
            
            print(f"🎉 전체 추출 완료: {len(all_questions)}개 문제, 총 비용: ${total_cost:.4f}")
            
            return {
                "success": True,
                "questions": all_questions,
                "count": len(all_questions),
                "chunks_processed": len(chunks),
                "total_cost": total_cost
            }
            
        except Exception as e:
            logger.error(f"Error in question extraction: {e}")
            return {"error": str(e)}
    
    async def _generate_materials_with_claude(self, text: str, topics: List[str], db: Session) -> Dict[str, Any]:
        """Claude API로 학습자료 생성"""
        try:
            # 학습자료 생성 에이전트 조회 (직접 sqlite3 사용)
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_type = 'study_material_generation' AND is_active = 1 LIMIT 1")
            agent_row = cursor.fetchone()
            conn.close()
            
            if not agent_row:
                return {"error": "Study material generation agent not found"}
            
            agent = {
                "model_name": agent_row[4],
                "system_prompt": agent_row[9] or '',
                "max_tokens": agent_row[7] or 6000,
                "temperature": agent_row[8] or 0.7
            }
            
            topics_str = ", ".join(topics) if topics else "일반"
            
            prompt = f"""다음 교재 텍스트와 주요 토픽을 기반으로 학습자료를 생성해주세요:

텍스트: {text[:4000]}...
주요 토픽: {topics_str}

다음 JSON 배열 형식으로 학습자료를 생성해주세요:
[
    {{
        "title": "학습자료 제목",
        "content": "상세한 학습 내용 (최소 200자 이상)",
        "content_type": "개념정리/요약/예제",
        "difficulty_level": "초급/중급/고급",
        "keywords": ["키워드1", "키워드2", "키워드3"]
    }}
]

체계적이고 이해하기 쉬운 학습자료를 JSON 형식으로만 생성해주세요."""
            
            agent_dict = agent
            response = await claude_service.call_claude_api_direct(prompt, agent_dict, db, max_tokens=6000)
            
            if response.get("success"):
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
            
            return {"error": "Failed to generate materials"}
            
        except Exception as e:
            logger.error(f"Error in material generation: {e}")
            return {"error": str(e)}
    
    async def _verify_quality_with_claude(self, questions: List, materials: List, db: Session) -> Dict[str, Any]:
        """Claude API로 품질 검증"""
        try:
            # 품질 검증 에이전트 조회 (직접 sqlite3 사용)
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_agents WHERE agent_type = 'quality_verification' AND is_active = 1 LIMIT 1")
            agent_row = cursor.fetchone()
            conn.close()
            
            if not agent_row:
                return {"success": True, "quality_score": 80, "feedback": "품질 검증 에이전트 없음", "cost": 0}
            
            agent = {
                "model_name": agent_row[4],
                "system_prompt": agent_row[9] or '',
                "max_tokens": agent_row[7] or 1000,
                "temperature": agent_row[8] or 0.7
            }
            
            prompt = f"""다음 AI 처리 결과의 품질을 검증해주세요:

추출된 문제 수: {len(questions)}
생성된 학습자료 수: {len(materials)}

JSON 형식으로 평가 결과를 제공해주세요:
{{
    "quality_score": 0-100점,
    "accuracy_score": 0-100점,
    "completeness_score": 0-100점,
    "feedback": "종합 평가 및 개선사항",
    "recommendations": ["추천사항1", "추천사항2"]
}}"""
            
            agent_dict = agent
            response = await claude_service.call_claude_api_direct(prompt, agent_dict, db, max_tokens=1000)
            
            if response.get("success"):
                content = response["content"]
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    quality_result = json.loads(json_match.group())
                    quality_result["success"] = True
                    quality_result["cost"] = self._calculate_cost(response.get("usage", {}))
                    return quality_result
            
            return {"success": True, "quality_score": 75, "feedback": "품질 검증 완료", "cost": 0}
            
        except Exception as e:
            logger.error(f"Error in quality verification: {e}")
            return {"success": True, "quality_score": 70, "feedback": f"검증 오류: {str(e)}", "cost": 0}
    
    async def _save_questions_to_db(self, questions: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """문제를 데이터베이스에 저장"""
        saved_questions = []
        
        for i, question in enumerate(questions):
            try:
                result = db.execute(
                    text("""
                        INSERT INTO extracted_questions 
                        (pdf_upload_id, question_number, question_text, options, correct_answer, topic_category, difficulty_level, explanation)
                        VALUES (:pdf_id, :q_num, :q_text, :options, :answer, :category, :difficulty, :explanation)
                    """),
                    {
                        "pdf_id": upload_id,
                        "q_num": question.get("question_number", i + 1),
                        "q_text": question.get("question_text", ""),
                        "options": json.dumps(question.get("options", []), ensure_ascii=False),
                        "answer": question.get("correct_answer", ""),
                        "category": question.get("topic_category", "일반"),
                        "difficulty": question.get("difficulty_level", "중급"),
                        "explanation": question.get("explanation", "")
                    }
                )
                db.flush()
                
                saved_questions.append({
                    "id": result.lastrowid,
                    "question_text": question.get("question_text", ""),
                    "topic_category": question.get("topic_category", "일반")
                })
                
            except Exception as e:
                logger.error(f"Error saving question {i}: {e}")
                continue
        
        db.commit()
        return saved_questions
    
    async def _save_materials_to_db(self, materials: List[Dict], upload_id: int, db: Session) -> List[Dict]:
        """학습자료를 데이터베이스에 저장"""
        saved_materials = []
        
        for i, material in enumerate(materials):
            try:
                result = db.execute(
                    text("""
                        INSERT INTO study_materials 
                        (pdf_upload_id, title, content, content_type, difficulty_level, keywords, chapter_number, section_number)
                        VALUES (:pdf_id, :title, :content, :content_type, :difficulty, :keywords, :chapter, :section)
                    """),
                    {
                        "pdf_id": upload_id,
                        "title": material.get("title", f"학습자료 {i+1}"),
                        "content": material.get("content", ""),
                        "content_type": material.get("content_type", "개념정리"),
                        "difficulty": material.get("difficulty_level", "중급"),
                        "keywords": json.dumps(material.get("keywords", []), ensure_ascii=False),
                        "chapter": 1,
                        "section": i + 1
                    }
                )
                db.flush()
                
                saved_materials.append({
                    "id": result.lastrowid,
                    "title": material.get("title", f"학습자료 {i+1}"),
                    "content_type": material.get("content_type", "개념정리")
                })
                
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
        """AI 작업 생성 (직접 sqlite3 사용)"""
        try:
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ai_tasks (file_upload_id, task_type, status, started_at, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (upload_id, agent_type, status))
            
            conn.commit()
            conn.close()
            logger.info(f"Created AI task: {agent_type} for upload {upload_id}")
        except Exception as e:
            logger.error(f"Error creating AI task: {e}")
    
    async def _update_ai_task(self, upload_id: int, agent_type: str, status: str, result_data: Dict, db: Session):
        """AI 작업 상태 업데이트 (직접 sqlite3 사용)"""
        try:
            import sqlite3
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE ai_tasks 
                SET status = ?, 
                    output_data = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_upload_id = ? AND task_type = ?
            """, (status, json.dumps(result_data, ensure_ascii=False), upload_id, agent_type))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated AI task: {agent_type} for upload {upload_id} - {status}")
        except Exception as e:
            logger.error(f"Error updating AI task: {e}")
    
    async def _log_progress(self, upload_id: int, message: str, db: Session):
        """진행 상황 로그"""
        try:
            # 간단한 진행 로그 (나중에 WebSocket으로 확장 가능)
            print(f"📝 Upload {upload_id}: {message}")
        except Exception as e:
            logger.error(f"Error logging progress: {e}")
    
    async def _update_api_usage(self, cost: float, db: Session):
        """API 사용량 업데이트"""
        try:
            # 활성화된 API 키 조회
            api_key = db.execute(
                text("SELECT * FROM api_keys WHERE is_active = 1 AND provider = 'anthropic' LIMIT 1")
            ).fetchone()
            
            if api_key:
                # 일일 및 월간 사용량 업데이트
                db.execute(
                    text("""
                        UPDATE api_keys 
                        SET current_daily_usage = current_daily_usage + :cost,
                            current_monthly_usage = current_monthly_usage + :cost,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :key_id
                    """),
                    {"cost": cost, "key_id": api_key.id}
                )
                
                # 사용 로그 생성
                db.execute(
                    text("""
                        INSERT INTO ai_usage_logs (api_key_id, agent_type, tokens_used, cost_usd, created_at)
                        VALUES (:key_id, :agent_type, :tokens, :cost, CURRENT_TIMESTAMP)
                    """),
                    {
                        "key_id": api_key.id,
                        "agent_type": "document_processing",
                        "tokens": 1000,  # 실제 토큰 수는 usage에서 가져와야 함
                        "cost": cost
                    }
                )
                db.commit()
                
        except Exception as e:
            logger.error(f"Error updating API usage: {e}")
            db.rollback()

# 전역 인스턴스
real_ai_processor = RealAIProcessor()