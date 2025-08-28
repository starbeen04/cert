"""
실제 AI API 엔드포인트 - OpenAI/Anthropic 실제 호출
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import time

from ..database import get_db
from ..services.real_ai_service import real_ai_service
from ..services.usage_logger import usage_logger
from ..services.enhanced_usage_tracker import enhanced_usage_tracker

router = APIRouter()

@router.post("/ai/chat")
async def ai_chat(
    request_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """실제 AI 채팅 API 호출"""
    
    start_time = time.time()
    message = request_data.get("message", "안녕하세요!")
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # 실제 AI API 호출
    if "anthropic" in x_api_key or "sk-ant" in x_api_key:
        result = await real_ai_service.call_anthropic_chat(message)
    elif "openai" in x_api_key or "sk-proj" in x_api_key:
        result = await real_ai_service.call_openai_chat(message)
    else:
        # 기본값으로 Claude 사용 (유일한 활성 키)
        result = await real_ai_service.call_anthropic_chat(message)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 향상된 사용량 로깅 (이미 real_ai_service에서 enhanced_usage_tracker 사용으로 처리됨)
    # 중복 로깅 방지를 위해 주석 처리
    # if result.get("success"):
    #     await enhanced_usage_tracker.log_enhanced_usage(
    #         api_key=x_api_key,
    #         endpoint="/ai/chat", 
    #         usage_result=result
    #     )
    
    return result

@router.post("/ai/analyze")
async def ai_analyze(
    request_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """실제 AI 문서 분석 API 호출"""
    
    start_time = time.time()
    document = request_data.get("document", "분석할 문서")
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # 실제 AI API 호출
    result = await real_ai_service.analyze_document(document, x_api_key)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 실제 사용량 로깅
    duration = time.time() - start_time
    usage = result.get("usage", {})
    model = result.get("model", "unknown")
    
    await usage_logger.log_real_usage(
        api_key=x_api_key,
        endpoint="/ai/analyze",
        model=model,
        prompt_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
        completion_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
        duration_seconds=duration
    )
    
    # 응답 형식 맞추기
    return {
        "analysis": result.get("response", "분석 결과"),
        "confidence": 0.95,  # 실제로는 AI 응답에서 추출 가능
        "model": result.get("model", "unknown"),
        "usage": result.get("usage", {}),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }

@router.post("/ai/completion")
async def ai_completion(
    request_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """실제 AI 텍스트 완성 API 호출"""
    
    start_time = time.time()
    prompt = request_data.get("prompt", "텍스트를 완성해주세요")
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # 실제 AI API 호출
    result = await real_ai_service.complete_text(prompt, x_api_key)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 실제 사용량 로깅
    duration = time.time() - start_time
    usage = result.get("usage", {})
    model = result.get("model", "unknown")
    
    await usage_logger.log_real_usage(
        api_key=x_api_key,
        endpoint="/ai/completion",
        model=model,
        prompt_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
        completion_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
        duration_seconds=duration
    )
    
    # 응답 형식 맞추기
    return {
        "completion": result.get("response", "완성된 텍스트"),
        "model": result.get("model", "unknown"),
        "usage": result.get("usage", {}),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }

@router.post("/documents/analyze")
async def document_analyze(
    request_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """실제 문서 분석 API 호출"""
    
    start_time = time.time()
    file_name = request_data.get("file_name", "document.pdf")
    content = request_data.get("content", f"{file_name}의 내용")
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # 문서 분석용 프롬프트
    document_text = f"파일명: {file_name}\n내용: {content}"
    result = await real_ai_service.analyze_document(document_text, x_api_key)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 실제 사용량 로깅
    duration = time.time() - start_time
    usage = result.get("usage", {})
    model = result.get("model", "unknown")
    
    await usage_logger.log_real_usage(
        api_key=x_api_key,
        endpoint="/documents/analyze",
        model=model,
        prompt_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
        completion_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
        duration_seconds=duration
    )
    
    # 응답 형식 맞추기
    return {
        "document_type": "분석된 문서",
        "analysis": result.get("response", "문서 분석 완료"),
        "model": result.get("model", "unknown"),
        "usage": result.get("usage", {}),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }

@router.post("/questions/generate")
async def generate_questions(
    request_data: Dict[str, Any],
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    """실제 문제 생성 API 호출"""
    
    start_time = time.time()
    topic = request_data.get("topic", "일반 상식")
    count = request_data.get("count", 5)
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # 실제 AI API 호출
    result = await real_ai_service.generate_questions(topic, count, x_api_key)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 실제 사용량 로깅
    duration = time.time() - start_time
    usage = result.get("usage", {})
    model = result.get("model", "unknown")
    
    await usage_logger.log_real_usage(
        api_key=x_api_key,
        endpoint="/questions/generate",
        model=model,
        prompt_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
        completion_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
        duration_seconds=duration
    )
    
    # 응답 형식 맞추기
    return {
        "generated_questions": f"{topic} 주제로 {count}개의 문제가 생성되었습니다.",
        "questions": result.get("response", "문제 생성 완료"),
        "model": result.get("model", "unknown"),
        "usage": result.get("usage", {}),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }