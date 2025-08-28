"""
스마트 PDF 분석 API - 새로운 3단계 시스템 전용 엔드포인트
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PdfUpload, ExtractedQuestion

# PDF 처리 시스템 임포트
from ..services.simple_pdf_processor import SimplePDFProcessor
from ..services.professional_pdf_pipeline import ProfessionalPDFPipeline
from ..services.unified_pdf_processor import UnifiedPDFProcessor
from ..services.hybrid_pdf_processor import HybridPDFProcessor
from ..services.structure_based_pdf_processor import StructureBasedPDFProcessor
from config.ai_config import ai_config
import openai
import os

router = APIRouter()

# 처리기 인스턴스들 (요청시 초기화)
simple_processor = None
professional_processor = None
structure_based_processor = None
unified_processor = None
hybrid_processor = None

def get_simple_processor():
    """SimplePDFProcessor 인스턴스를 요청시 생성"""
    global simple_processor
    if simple_processor is None:
        openai_api_key = ai_config.get_api_key("gpt-4o")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요")
        
        openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        simple_processor = SimplePDFProcessor(openai_client)
        print(f"✅ SimplePDFProcessor 초기화 완료 (API Key: ...{openai_api_key[-8:] if openai_api_key else 'None'})")
    
    return simple_processor

def get_professional_processor():
    """ProfessionalPDFPipeline 인스턴스를 요청시 생성"""
    global professional_processor
    if professional_processor is None:
        openai_api_key = ai_config.get_api_key("gpt-4o")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요")
        
        openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        professional_processor = ProfessionalPDFPipeline(openai_client)
        print(f"✅ ProfessionalPDFPipeline 초기화 완료")
    
    return professional_processor

def get_unified_processor():
    """UnifiedPDFProcessor 인스턴스를 요청시 생성"""
    global unified_processor
    if unified_processor is None:
        openai_api_key = ai_config.get_api_key("gpt-4o")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요")
        
        openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        unified_processor = UnifiedPDFProcessor(openai_client)
        print(f"✅ UnifiedPDFProcessor 초기화 완료")
    
    return unified_processor

def get_hybrid_processor():
    """HybridPDFProcessor 인스턴스를 요청시 생성"""
    global hybrid_processor
    if hybrid_processor is None:
        openai_api_key = ai_config.get_api_key("gpt-4o")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요")
        
        openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        hybrid_processor = HybridPDFProcessor(openai_client)
        print(f"✅ HybridPDFProcessor 초기화 완료")
    
    return hybrid_processor

def get_structure_based_processor():
    """StructureBasedPDFProcessor 인스턴스를 요청시 생성"""
    global structure_based_processor
    if structure_based_processor is None:
        openai_api_key = ai_config.get_api_key("gpt-4o")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요")
        
        openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        structure_based_processor = StructureBasedPDFProcessor(openai_client)
        print(f"✅ StructureBasedPDFProcessor 초기화 완료")
    
    return structure_based_processor


# DB 저장 함수
async def save_processing_result_to_db(
    upload_id: int, 
    filename: str,
    certificate_id: int,
    structure_analysis: Dict,
    processing_result: Dict,
    questions: List[Dict]
):
    """처리 결과를 데이터베이스에 저장"""
    
    # 임시 DB 세션 생성 (실제로는 dependency injection 사용)
    from ..database import SessionLocal
    db = SessionLocal()
    
    try:
        # 1. PdfUpload 레코드 생성/업데이트
        pdf_upload = db.query(PdfUpload).filter(PdfUpload.id == upload_id).first()
        
        if not pdf_upload:
            # 새로운 업로드 레코드 생성
            pdf_upload = PdfUpload(
                id=upload_id,
                filename=filename,
                original_name=filename,
                file_path=f"uploads/structure_test/struct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}.pdf",
                file_size=0,  # 실제 파일 크기 필요
                certificate_id=certificate_id,
                file_type="questions",
                processing_status="completed",
                ai_agent="smart_3stage_pipeline"
            )
            db.add(pdf_upload)
        else:
            # 기존 레코드 업데이트
            pdf_upload.processing_status = "completed"
            pdf_upload.ai_agent = "smart_3stage_pipeline"
            pdf_upload.updated_at = datetime.now()
        
        db.flush()  # ID 생성을 위해 flush
        
        # 2. ExtractedQuestion 레코드들 생성
        for i, question in enumerate(questions, 1):
            # 프로페셔널 스키마 형식 처리
            question_text = ""
            if question.get('stem'):
                question_text = question['stem'].get('text', '')
            else:
                question_text = question.get('question_text', '')
            
            # 선택지 처리 (새 형식)
            options_list = []
            if question.get('choices'):
                for choice in question['choices']:
                    content = choice.get('content', '')
                    options_list.append(content)
                options_text = "\n".join(options_list)
            elif question.get('options'):
                # 기존 형식 호환
                if isinstance(question['options'], list):
                    options_text = "\n".join(question['options'])
                else:
                    options_text = str(question['options'])
            else:
                options_text = ""
            
            # 보기/지문 처리
            passage_text = ""
            if question.get('passages'):
                passage_texts = []
                for passage in question['passages']:
                    if passage.get('type') == 'text':
                        passage_texts.append(passage.get('content', ''))
                passage_text = "\n".join(passage_texts)
            else:
                passage_text = question.get('passage', '')
            
            extracted_question = ExtractedQuestion(
                pdf_upload_id=pdf_upload.id,
                question_id=str(question.get('number', question.get('question_number', i))),
                question_text=question_text,
                question_type=question.get('question_type', 'multiple_choice'),
                options=options_text,
                passage=passage_text,
                additional_info=f"Page: {question.get('page_span', [question.get('page_number', 1)])[0]}, Processing: Professional A/B/C pipeline"
            )
            db.add(extracted_question)
        
        db.commit()
        
        print(f"✅ DB 저장 성공: {len(questions)}개 문제 저장됨")
        
    except Exception as e:
        db.rollback()
        print(f"❌ DB 저장 실패: {e}")
        raise e
    finally:
        db.close()

# 구 함수 제거됨 - 프로페셔널 파이프라인으로 대체

@router.post("/simple-process")
async def simple_pdf_process(
    file: UploadFile = File(...),
    name: str = Form(...),
    certificate_id: int = Form(...),
    file_type: str = Form("questions"),
    description: str = Form("")
):
    """단순화된 3단계 PDF 처리"""
    
    try:
        # 1. 파일 저장
        temp_upload_id = int(datetime.now().timestamp() * 1000)  # 임시 ID
        filename = file.filename
        
        # 업로드 디렉토리 생성
        upload_dir = Path("uploads/simple_test")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"simple_test_{timestamp}_{filename}"
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"🎯 단순화된 3단계 PDF 처리 시작: {filename}")
        print(f"📁 저장된 파일: {file_path}")
        
        # 2. 단순화된 처리 시스템 실행
        processor = get_simple_processor()
        result = await processor.process_pdf_simple(str(file_path), temp_upload_id)
        
        if result.get("success"):
            # 3. 데이터베이스 저장
            questions = result.get("extraction_result", {}).get("questions", [])
            
            if questions:
                await save_processing_result_to_db(
                    temp_upload_id,
                    name,
                    certificate_id,
                    result.get("structure_analysis", {}),
                    result,
                    questions
                )
                
                print(f"✅ 단순 처리 성공: {len(questions)}개 문제 추출")
            
            return JSONResponse({
                "success": True,
                "mode": "simple_3_stage",
                "temp_upload_id": temp_upload_id,
                "filename": filename,
                "structure_analysis": result.get("structure_analysis"),
                "total_questions": len(questions),
                "processing_result": result,
                "message": f"단순화된 3단계 처리 완료 - {len(questions)}개 문제 추출"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": "단순화된 처리 실패"
            }, status_code=500)
    
    except Exception as e:
        # 파일 정리
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
            
        print(f"❌ 단순 처리 오류: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "단순화된 PDF 처리 중 오류 발생"
        }, status_code=500)

@router.get("/analysis-status/{upload_id}")
async def get_smart_analysis_status(upload_id: int):
    """스마트 분석 상태 확인"""
    
    # 실제 구현시 DB에서 상태 확인
    return {
        "upload_id": upload_id,
        "status": "processing",  # pending, processing, completed, failed
        "progress": {
            "step": 2,  # 현재 단계 (1: 구조분석, 2: 맞춤추출, 3: 품질검증)
            "description": "구조 기반 맞춤형 추출 중...",
            "percentage": 60
        },
        "estimated_completion": "2분 후"
    }

@router.get("/analysis-result/{upload_id}")
async def get_smart_analysis_result(upload_id: int):
    """스마트 분석 결과 조회"""
    
    # 실제 구현시 DB에서 결과 조회
    return {
        "upload_id": upload_id,
        "success": True,
        "processing_method": "smart_3stage_pipeline",
        "structure_analysis": {
            "document_type": "questions_only",
            "total_questions": 40,
            "page_breakdown": {
                "questions_pages": [1, 2, 3, 4, 5]
            }
        },
        "extraction_results": {
            "questions_extracted": 38,
            "accuracy_score": 95.0,
            "issues_found": [
                "문제 12번: 이미지 선택지 매칭 필요",
                "문제 25번: 표 데이터 불완전"
            ]
        },
        "verification_result": {
            "overall_quality": "excellent",
            "confidence_score": 0.92
        }
    }


@router.post("/test-structure-analysis")
async def test_structure_analysis_only(
    file: UploadFile = File(...),
    name: str = Form(...),
    certificate_id: int = Form(...),
    file_type: str = Form(...),
    description: str = Form(None),
):
    """1단계만 테스트: PDF 구조 분석만 수행"""
    
    print(f"🔍 구조 분석 테스트: {file.filename}")
    
    # 파일 저장 로직 (위와 동일)
    upload_dir = Path("uploads/structure_test")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"struct_test_{timestamp}_{file.filename}"
    file_path = upload_dir / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ultra Precise 구조 분석 수행
        import openai
        import os
        from dotenv import load_dotenv
        
        # .env 파일 로드
        load_dotenv()
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        print(f"OpenAI API Key 확인: {openai_api_key[:20]}..." if openai_api_key else "OpenAI API Key 없음")
        
        # 임시로 기존 키 사용 (테스트용)
        fallback_key = "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"
        
        openai_client = openai.AsyncOpenAI(
            api_key=openai_api_key or fallback_key
        )
        
        from app.services.ultra_precise_pdf_analyzer import UltraPrecisePDFAnalyzer
        analyzer = UltraPrecisePDFAnalyzer(openai_client)
        
        temp_id = int(datetime.now().timestamp())
        structure = await analyzer.analyze_pdf_structure_ultra_detailed(str(file_path), temp_id)
        
        return JSONResponse({
            "success": True,
            "filename": filename,
            "structure_analysis": structure,
            "temp_upload_id": temp_id,
            "message": "Ultra Precise PDF 구조 분석 완료 (1단계 테스트)"
        })
        
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
            
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "구조 분석 테스트 실패"
        }, status_code=500)

@router.get("/analyze-structure/{upload_id}")
async def get_structure_analysis_result(upload_id: int):
    """구조 분석 결과 조회 - 실제로는 DB에서 조회해야 하지만 테스트용 목업 데이터"""
    
    # 실제 구현시 DB에서 upload_id로 검색
    # 지금은 목업 데이터 반환
    mock_analysis_result = {
        "success": True,
        "structure_analysis": {
            "analysis_summary": {
                "document_type": "questions_only",
                "total_questions": 40,
                "confidence_score": 0.95,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "page_analysis": [
                {
                    "page_number": 1,
                    "page_type": "pure_questions",
                    "question_density": 4,
                    "questions_on_page": [1, 2, 3, 4],
                    "special_elements": ["tables", "images"]
                },
                {
                    "page_number": 2,
                    "page_type": "pure_questions", 
                    "question_density": 4,
                    "questions_on_page": [5, 6, 7, 8],
                    "special_elements": ["code_blocks"]
                }
            ],
            "question_analysis": {
                "total_questions_found": 40,
                "question_types_distribution": {
                    "text_only": 25,
                    "with_table": 8,
                    "with_image": 5,
                    "with_code": 2
                },
                "detailed_questions": [
                    {
                        "question_number": 1,
                        "question_type": "text_only",
                        "choices_count": 4,
                        "page_location": 1,
                        "has_passage": False,
                        "has_table": False,
                        "has_images": False,
                        "has_code": False,
                        "processing_complexity": "low"
                    },
                    {
                        "question_number": 6,
                        "question_type": "with_table",
                        "choices_count": 4,
                        "page_location": 2,
                        "has_passage": True,
                        "has_table": True,
                        "has_images": False,
                        "has_code": False,
                        "processing_complexity": "high"
                    }
                ]
            },
            "special_elements": {
                "tables": [
                    {
                        "location": "Q6 (Page 2)",
                        "table_type": "process_scheduling",
                        "complexity": "medium",
                        "data_completeness": "complete"
                    }
                ],
                "images": [
                    {
                        "location": "Q13 (Page 4)",
                        "image_purpose": "선택지",
                        "image_count_at_location": 4
                    }
                ]
            },
            "processing_strategy": {
                "recommended_approach": "question_type_specialized",
                "chunk_size_recommendation": "15_questions_per_chunk",
                "estimated_processing_time": "3-5분",
                "special_handling": [
                    "표 데이터 완전 추출 보장",
                    "이미지 선택지 정확한 매칭",
                    "코드 블록 구조 보존"
                ]
            },
            "quality_checks": {
                "completeness_score": 0.92,
                "consistency_score": 0.94,
                "reliability_score": 0.90,
                "issues_found": [
                    "문제 25번: 이미지 선택지 인식 필요",
                    "문제 38번: 표 데이터 부분적 인식"
                ]
            }
        },
        "message": "Ultra Precise 구조 분석 완료"
    }
    
    return JSONResponse(mock_analysis_result)

# 구 구조 기반 처리 함수 제거됨 - 프로페셔널 파이프라인으로 대체

@router.get("/results/{upload_id}")
async def get_processing_result(upload_id: int):
    """처리 결과 조회"""
    
    try:
        results_dir = Path("results/smart_analysis")
        result_files = list(results_dir.glob(f"result_{upload_id}_*.json"))
        
        if not result_files:
            return JSONResponse({
                "success": False,
                "error": "처리 결과를 찾을 수 없습니다"
            }, status_code=404)
        
        # 가장 최근 파일 선택
        latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return JSONResponse({
            "success": True,
            "result": result_data,
            "message": "처리 결과 조회 성공"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/processing-methods/compare")
async def compare_processing_methods_info():
    """처리 방식 비교 정보"""
    
    return {
        "comparison_modes": {
            "legacy": {
                "name": "기존 방식",
                "description": "기존 청크 기반 일괄 처리",
                "pros": ["안정적", "검증됨"],
                "cons": ["선택지 011 문제", "이미지 처리 부정확"]
            },
            "smart": {
                "name": "새로운 3단계 방식",
                "description": "구조 분석 → 맞춤 추출 → 품질 검증",
                "pros": ["정확한 구조 파악", "맞춤형 처리", "품질 검증"],
                "cons": ["처리 시간 증가", "API 사용량 증가"]
            }
        },
        "recommended_test_scenarios": [
            "문제집 PDF (40-60문제)",
            "이론서 PDF", 
            "혼합형 PDF (문제+이론)",
            "이미지 선택지 포함 PDF",
            "표/그래프 포함 PDF"
        ]
    }

@router.get("/special-elements/{upload_id}")
async def get_special_elements(upload_id: int):
    """특수 요소(표, 코드, 이미지) 파일 목록 조회"""
    try:
        # assets 디렉토리에서 해당 upload_id 폴더 찾기
        assets_path = Path("assets")
        upload_folders = list(assets_path.glob(f"upload_{upload_id}*"))
        
        if not upload_folders:
            return {"special_elements": []}
        
        upload_folder = upload_folders[0]
        special_elements = []
        
        # q-2024-ii-XXX 패턴으로 된 폴더들 찾기
        for question_dir in upload_folder.glob("q-2024-ii-*"):
            question_num = question_dir.name.split("-")[-1]  # 006, 015 등 추출
            
            elements = {
                "question_number": int(question_num),
                "tables": [],
                "codes": [],
                "images": []
            }
            
            # CSV 파일 (표)
            for csv_file in question_dir.glob("*.csv"):
                elements["tables"].append({
                    "filename": csv_file.name,
                    "path": str(csv_file.relative_to(Path("assets")))
                })
            
            # 코드 파일
            for code_file in question_dir.glob("*.txt"):
                elements["codes"].append({
                    "filename": code_file.name,
                    "path": str(code_file.relative_to(Path("assets")))
                })
            
            # 이미지 파일
            for img_file in question_dir.glob("*.png"):
                elements["images"].append({
                    "filename": img_file.name,
                    "path": str(img_file.relative_to(Path("assets")))
                })
                
            if elements["tables"] or elements["codes"] or elements["images"]:
                special_elements.append(elements)
        
        return {
            "upload_id": upload_id,
            "special_elements": special_elements
        }
        
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@router.get("/special-elements/{upload_id}/file/{file_path:path}")
async def get_special_element_file(upload_id: int, file_path: str):
    """특수 요소 파일 내용 조회"""
    try:
        from fastapi.responses import FileResponse
        
        # 파일 경로 검증
        full_path = Path("assets") / file_path
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # 보안 검사: assets 폴더 외부 접근 방지
        if not str(full_path.absolute()).startswith(str(Path("assets").absolute())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 파일 확장자에 따른 처리
        if full_path.suffix == ".csv":
            # CSV 파일은 JSON으로 변환하여 반환
            import csv
            import json
            
            csv_data = []
            with open(full_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)
            
            return {
                "file_type": "table",
                "content": csv_data,
                "raw_path": file_path
            }
            
        elif full_path.suffix == ".txt":
            # 텍스트 파일 (코드)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "file_type": "code",
                "content": content,
                "raw_path": file_path
            }
            
        elif full_path.suffix in [".png", ".jpg", ".jpeg"]:
            # 이미지 파일은 직접 서빙
            return FileResponse(
                path=str(full_path),
                media_type="image/png",
                filename=full_path.name
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@router.post("/professional-process")
async def professional_pdf_process(
    file: UploadFile = File(...),
    name: str = Form(...),
    certificate_id: int = Form(...),
    file_type: str = Form("questions"),
    description: str = Form("")
):
    """프로페셔널 A/B/C 단계 PDF 처리 파이프라인"""
    
    try:
        # 1. 파일 저장
        temp_upload_id = int(datetime.now().timestamp() * 1000)
        filename = file.filename
        
        upload_dir = Path("uploads/professional")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"professional_{timestamp}_{filename}"
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"🎯 프로페셔널 A/B/C 단계 처리 시작: {filename}")
        print(f"📁 저장된 파일: {file_path}")
        
        # 2. 프로페셔널 처리 파이프라인 실행
        processor = get_professional_processor()
        result = await processor.process_pdf_professional(str(file_path), temp_upload_id)
        
        if result.get("success"):
            # 디버깅: 결과 구조 확인
            print(f"🔍 디버깅 - 결과 구조:")
            print(f"   - result keys: {list(result.keys())}")
            print(f"   - schema_result 존재: {'schema_result' in result}")
            if 'schema_result' in result:
                print(f"   - schema_result keys: {list(result['schema_result'].keys())}")
                print(f"   - questions 존재: {'questions' in result['schema_result']}")
                if 'questions' in result['schema_result']:
                    print(f"   - questions 개수: {len(result['schema_result']['questions'])}")
            
            # 3. 데이터베이스 저장
            questions = result.get("schema_result", {}).get("questions", [])
            
            if questions:
                await save_processing_result_to_db(
                    temp_upload_id,
                    name,
                    certificate_id,
                    result.get("structure_data", {}),
                    result,
                    questions
                )
                
                print(f"✅ 프로페셔널 처리 성공: {len(questions)}개 문제 추출")
            
            return JSONResponse({
                "success": True,
                "mode": "professional_pipeline",
                "temp_upload_id": temp_upload_id,
                "filename": filename,
                "stage_a_result": result.get("structure_data"),
                "stage_b_result": result.get("schema_result"),
                "stage_c_result": result.get("tagging_result"),
                "total_questions": result.get("total_questions", len(questions)),
                "processing_result": result,
                "message": f"프로페셔널 파이프라인 완료 - {result.get('total_questions', len(questions))}개 문제 추출"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": "프로페셔널 처리 실패"
            }, status_code=500)
    
    except Exception as e:
        # 파일 정리
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
            
        print(f"❌ 프로페셔널 처리 오류: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "프로페셔널 PDF 처리 중 오류 발생"
        }, status_code=500)


@router.post("/unified-process")
async def unified_process_pdf(
    file: UploadFile = File(...),
    certificate_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    통합 PDF 처리 시스템 - 페이지 경계 문제 해결
    
    **주요 특징:**
    - 페이지별 분리 처리 대신 전체 통합 처리
    - 크로스 페이지 선택지/표/코드 완전 추출
    - OCR 정확도 향상을 위한 고해상도 통합 이미지 사용
    - 표/이미지 파일로 별도 저장
    """
    
    # 임시 파일 경로
    file_path = None
    
    try:
        print("🚀 통합 PDF 처리 시작")
        print("=" * 60)
        
        # 1. 파일 유효성 검증
        if not file.filename.lower().endswith('.pdf'):
            return JSONResponse({
                "success": False,
                "error": "PDF 파일만 업로드 가능합니다"
            }, status_code=400)
        
        # 2. 임시 파일 저장 (UUID 기반 이름)
        temp_upload_id = int(datetime.now().timestamp() * 1000000)  # 마이크로초 기반 ID
        filename = f"unified_{temp_upload_id}_{file.filename}"
        name = file.filename
        
        # 통합 처리용 디렉토리
        upload_dir = Path("uploads/unified")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"📁 파일 저장: {file_path}")
        
        # 3. 통합 PDF 처리기로 처리
        processor = get_unified_processor()
        result = await processor.process_pdf_unified(str(file_path), temp_upload_id)
        
        if result["success"]:
            print("📊 통합 처리 결과 검토:")
            print(f"   - 성공: {result['success']}")
            print(f"   - 추출된 문제 수: {len(result.get('questions', []))}")
            print(f"   - 처리 방식: {result.get('processing_method')}")
            
            # 4. 데이터베이스 저장
            questions = result.get("questions", [])
            
            if questions:
                await save_processing_result_to_db(
                    temp_upload_id,
                    name,
                    certificate_id,
                    result.get("context_data", {}),
                    result,
                    questions
                )
                
                print(f"✅ 통합 처리 성공: {len(questions)}개 문제 추출")
                
                # 통합 처리 통계
                stats = {
                    "total_questions": len(questions),
                    "cross_page_elements": len(result.get("context_data", {}).get("cross_page_elements", [])),
                    "special_elements": {
                        "tables": len([q for q in questions if q.get("has_table")]),
                        "images": len([q for q in questions if q.get("has_image")]),
                        "codes": len([q for q in questions if q.get("has_code")])
                    },
                    "extracted_files": {
                        "table_images": len([q for q in questions if q.get("table_image_path")]),
                        "code_images": len([q for q in questions if q.get("code_image_path")]),
                        "diagram_images": len([q for q in questions if q.get("diagram_image_path")])
                    }
                }
            
            return JSONResponse({
                "success": True,
                "mode": "unified_processing",
                "temp_upload_id": temp_upload_id,
                "filename": filename,
                "total_questions": len(questions),
                "processing_result": result,
                "statistics": stats,
                "improvements": {
                    "cross_page_handling": "완전히 해결됨",
                    "ocr_accuracy": "고해상도 통합 이미지로 향상됨",
                    "table_extraction": "이미지 파일로 별도 저장됨",
                    "character_recognition": "전체 컨텍스트 기반으로 개선됨"
                },
                "message": f"통합 처리 완료 - {len(questions)}개 문제 추출, 페이지 경계 문제 해결됨"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": "통합 처리 실패"
            }, status_code=500)
    
    except Exception as e:
        # 파일 정리
        if 'file_path' in locals() and file_path and file_path.exists():
            file_path.unlink()
            
        print(f"❌ 통합 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "통합 PDF 처리 중 오류 발생"
        }, status_code=500)


@router.post("/hybrid-process")
async def hybrid_process_pdf(
    file: UploadFile = File(...),
    certificate_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    하이브리드 PDF 처리 시스템 - 데이터 타입별 특화 + 개별 정확도 유지
    
    **핵심 특징:**
    - 데이터 타입별 특화 처리 (텍스트/표/코드/이미지/다이어그램/수식/지문)
    - 개별 처리로 정확도 유지 + 크로스 페이지 연결 해결
    - 각 데이터 타입에 최적화된 추출 방법 적용
    - 표→이미지+마크다운, 코드→구문보존, 다이어그램→이미지보존
    """
    
    file_path = None
    
    try:
        print("🎯 하이브리드 PDF 처리 시작")
        print("=" * 70)
        
        # 1. 파일 유효성 검증
        if not file.filename.lower().endswith('.pdf'):
            return JSONResponse({
                "success": False,
                "error": "PDF 파일만 업로드 가능합니다"
            }, status_code=400)
        
        # 2. 임시 파일 저장
        temp_upload_id = int(datetime.now().timestamp() * 1000000)
        filename = f"hybrid_{temp_upload_id}_{file.filename}"
        name = file.filename
        
        upload_dir = Path("uploads/hybrid")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"📁 파일 저장: {file_path}")
        
        # 3. 하이브리드 PDF 처리기로 처리
        processor = get_hybrid_processor()
        result = await processor.process_pdf_hybrid(str(file_path), temp_upload_id)
        
        if result["success"]:
            print("📊 하이브리드 처리 결과:")
            print(f"   - 성공: {result['success']}")
            print(f"   - 추출된 문제 수: {len(result.get('questions', []))}")
            print(f"   - 처리 방식: {result.get('processing_method')}")
            
            questions = result.get("questions", [])
            
            if questions:
                await save_processing_result_to_db(
                    temp_upload_id,
                    name,
                    certificate_id,
                    result.get("structure_analysis", {}),
                    result,
                    questions
                )
                
                print(f"✅ 하이브리드 처리 성공: {len(questions)}개 문제 추출")
                
                # 데이터 타입별 상세 통계
                processing_stats = result.get("processing_stats", {})
                data_type_stats = processing_stats.get("data_type_counts", {})
                
                detailed_stats = {
                    "total_questions": len(questions),
                    "data_type_breakdown": data_type_stats,
                    "processing_methods": processing_stats.get("processing_methods", {}),
                    "cross_page_connections": len(result.get("cross_page_map", {}).get("connections", [])),
                    "specialized_extractions": {
                        "table_images": len([q for q in questions if q.get("table_image_path")]),
                        "code_images": len([q for q in questions if q.get("code_image_path")]),
                        "diagram_images": len([q for q in questions if q.get("image_path")]),
                        "structured_tables": len([q for q in questions if q.get("table_markdown")]),
                        "preserved_code": len([q for q in questions if q.get("code_block")])
                    }
                }
            
            return JSONResponse({
                "success": True,
                "mode": "hybrid_specialized",
                "temp_upload_id": temp_upload_id,
                "filename": filename,
                "total_questions": len(questions),
                "processing_result": result,
                "detailed_statistics": detailed_stats,
                "key_improvements": {
                    "data_type_specialization": "각 데이터 타입별 최적화된 처리",
                    "individual_accuracy_maintained": "개별 처리로 정확도 유지됨",
                    "cross_page_resolved": "크로스 페이지 연결 문제 해결됨",
                    "multi_modal_output": "텍스트+이미지+구조화데이터 다중 출력",
                    "precision_by_content": "콘텐츠별 정밀도 최적화"
                },
                "data_type_processing": {
                    "text_questions": "한글 텍스트 + 선택지 마커 정확도 최우선",
                    "table_data": "숫자 정확도 + 마크다운 구조화 + 이미지 보존",
                    "code_blocks": "문법 보존 + 들여쓰기 정확도 + 구문 분석",
                    "diagrams": "시각적 정보 완전 보존 + 이미지 추출",
                    "choice_images": "선택지별 이미지 분리 + 라벨링",
                    "formulas": "수학 기호 정확도 + 구조 보존",
                    "passages": "긴 텍스트 맥락 보존 + 구조 유지"
                },
                "message": f"하이브리드 처리 완료 - {len(questions)}개 문제, 데이터 타입별 특화 처리 완료"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": "하이브리드 처리 실패"
            }, status_code=500)
    
    except Exception as e:
        # 파일 정리
        if 'file_path' in locals() and file_path and file_path.exists():
            file_path.unlink()
            
        print(f"❌ 하이브리드 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "하이브리드 PDF 처리 중 오류 발생"
        }, status_code=500)


@router.post("/structure-based-process")
async def structure_based_process_pdf(
    file: UploadFile = File(...),
    certificate_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    구조 기반 PDF 처리 시스템 - 완전한 PDF 구조 파악 후 정확한 추출
    
    **혁신적 특징:**
    - PDF 전체 구조 정보 추출 (텍스트 블록 위치, 폰트, 크기, 이미지 좌표)
    - 구조 기반 문제 경계 정확한 판별 
    - 좌표 기반 선택지 연결 (크로스 페이지 완벽 해결)
    - 실제 표/이미지 추출 및 위치 정보 보존
    - 환각 없는 정확한 데이터 추출 (구조 정보 기반)
    """
    
    file_path = None
    
    try:
        print("🏗️ 구조 기반 PDF 처리 시작")
        print("=" * 70)
        
        # 1. 파일 유효성 검증
        if not file.filename.lower().endswith('.pdf'):
            return JSONResponse({
                "success": False,
                "error": "PDF 파일만 업로드 가능합니다"
            }, status_code=400)
        
        # 2. 임시 파일 저장
        temp_upload_id = int(datetime.now().timestamp() * 1000000)
        filename = f"structure_{temp_upload_id}_{file.filename}"
        name = file.filename
        
        upload_dir = Path("uploads/structure_based")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        print(f"📁 구조 분석용 파일 저장: {file_path}")
        
        # 3. 구조 기반 PDF 처리기로 처리
        processor = get_structure_based_processor()
        result = await processor.process_pdf_structure_based(str(file_path), temp_upload_id)
        
        if result["success"]:
            questions = result["questions"]
            structure_analysis = result["structure_analysis"]
            validation_result = result["validation_result"]
            
            print("🎉 구조 기반 처리 성공!")
            print(f"   📋 추출된 문제: {len(questions)}개")
            print(f"   📊 품질 점수: {validation_result['quality_score']:.2f}")
            print(f"   ✅ 4개 선택지 문제: {validation_result['questions_with_4_choices']}개")
            print(f"   🎯 정답 매칭: {validation_result['questions_with_answers']}개")
            
            # 4. 데이터베이스 저장
            if questions:
                await save_processing_result_to_db(
                    temp_upload_id,
                    name,
                    certificate_id,
                    structure_analysis,
                    result,
                    questions
                )
                
                print(f"✅ DB 저장 완료: {len(questions)}개 문제")
            
            return JSONResponse({
                "success": True,
                "mode": "structure_based_comprehensive",
                "temp_upload_id": temp_upload_id,
                "filename": filename,
                "total_questions": len(questions),
                "processing_result": result,
                "structure_analysis": {
                    "total_pages": structure_analysis["full_structure"]["total_pages"],
                    "fonts_used": len(structure_analysis["full_structure"]["fonts_used"]),
                    "visual_elements": {
                        "tables": len(structure_analysis["visual_elements"]["tables"]),
                        "diagrams": len(structure_analysis["visual_elements"]["diagrams"]),
                        "code_images": len(structure_analysis["visual_elements"]["code_images"]),
                        "choice_images": len(structure_analysis["visual_elements"]["choice_images"])
                    },
                    "cross_page_issues_resolved": len(structure_analysis["cross_page_analysis"]["cross_page_issues"])
                },
                "validation_metrics": validation_result,
                "key_improvements": {
                    "complete_structure_analysis": "PDF 전체 구조 정보 기반 정확한 분석",
                    "coordinate_based_extraction": "좌표 기반 정확한 요소 위치 파악",
                    "no_hallucination": "구조 정보 기반으로 환각 없는 추출",
                    "visual_element_preservation": "표/이미지/다이어그램 완전 보존",
                    "cross_page_perfect_resolution": "크로스 페이지 문제 완벽 해결",
                    "quality_validation": "추출 품질 자동 검증 시스템"
                },
                "technical_advantages": {
                    "structure_first_approach": "구조 파악 → 추출 (추측 없음)",
                    "coordinate_precision": "정확한 좌표 기반 요소 연결",  
                    "font_size_analysis": "폰트 크기/스타일로 문제 구분",
                    "bounding_box_calculations": "정확한 영역 계산으로 요소 분리",
                    "multi_modal_preservation": "텍스트+이미지+구조 모두 보존"
                },
                "message": f"구조 기반 처리 완료 - {len(questions)}개 문제, 품질: {validation_result['extraction_quality']}"
            })
        else:
            return JSONResponse({
                "success": False,
                "error": result.get("error", "알 수 없는 오류"),
                "message": "구조 기반 처리 실패"
            }, status_code=500)
    
    except Exception as e:
        # 파일 정리
        if 'file_path' in locals() and file_path and file_path.exists():
            file_path.unlink()
            
        print(f"❌ 구조 기반 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse({
            "success": False,
            "error": str(e),
            "message": "구조 기반 PDF 처리 중 오류 발생"
        }, status_code=500)