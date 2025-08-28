# AI 에이전트 관리 및 사용량 모니터링 전용 라우터
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import AIAgent, AIUsageLog, AITask, APIKey
from ..schemas import (
    AIAgentCreate, AIAgentUpdate, AIAgentResponse,
    AIUsageLogResponse, AITaskCreate, AITaskResponse,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse
)
from ..auth import get_admin_user, User

router = APIRouter(prefix="/api/ai-management", tags=["ai-management"])

# Simple test endpoint
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "AI Management router is working"}

# Test endpoint for agents without auth
@router.get("/agents/test")
async def test_agents(db: Session = Depends(get_db)):
    """Test agents endpoint without complex dependencies"""
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT COUNT(*) FROM ai_agents")).scalar()
        return {"message": "Agent test successful", "agent_count": result}
    except Exception as e:
        return {"error": str(e)}

# API 키 관리 엔드포인트들
@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """모든 API 키 조회 (관리자만)"""
    keys = db.query(APIKey).all()
    return keys

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """새 API 키 등록"""
    # 같은 이름의 키가 있는지 확인
    existing_key = db.query(APIKey).filter(APIKey.key_name == api_key_data.key_name).first()
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="같은 이름의 API 키가 이미 존재합니다"
        )
    
    # API 키는 실제로는 암호화해서 저장해야 하지만, 데모용으로 일단 그대로 저장
    db_key = APIKey(
        provider=api_key_data.provider,
        key_name=api_key_data.key_name,
        api_key=api_key_data.api_key,  # 실제로는 암호화 필요
        is_active=api_key_data.is_active,
        daily_limit=api_key_data.daily_limit,
        monthly_limit=api_key_data.monthly_limit,
        last_reset_date=datetime.now().date()
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return db_key

# PDF 처리용 AI 에이전트 관리
@router.get("/processing-agents", response_model=List[AIAgentResponse])
async def get_processing_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """PDF 처리용 AI 에이전트 목록 조회"""
    processing_types = [
        "document_analysis", "question_extraction", "study_material_generation",
        "question_generation", "database_management", "user_analysis", 
        "explanation_generation", "quality_verification"
    ]
    
    agents = db.query(AIAgent).filter(AIAgent.agent_type.in_(processing_types)).all()
    return agents

@router.post("/processing-agents", response_model=AIAgentResponse)
async def create_processing_agent(
    agent_data: AIAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """PDF 처리용 AI 에이전트 생성"""
    # 같은 이름의 에이전트 체크
    existing_agent = db.query(AIAgent).filter(AIAgent.name == agent_data.name).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="같은 이름의 에이전트가 이미 존재합니다"
        )
    
    db_agent = AIAgent(
        name=agent_data.name,
        description=agent_data.description,
        agent_type=agent_data.agent_type,
        model_name=agent_data.model_name,
        provider=agent_data.provider,
        is_active=agent_data.is_active,
        max_tokens=agent_data.max_tokens,
        temperature=agent_data.temperature,
        system_prompt=agent_data.system_prompt,
        agent_config=agent_data.agent_config,
        priority=agent_data.priority
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent

@router.post("/processing-agents/{agent_id}/toggle")
async def toggle_processing_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """에이전트 활성화/비활성화 토글"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 에이전트를 찾을 수 없습니다"
        )
    
    agent.is_active = not agent.is_active
    db.commit()
    db.refresh(agent)
    
    return {
        "message": f"AI 에이전트가 {'활성화' if agent.is_active else '비활성화'}되었습니다",
        "is_active": agent.is_active
    }

# 사용량 모니터링
@router.get("/usage-overview")
async def get_usage_overview(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """전체 AI 사용량 개요"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 전체 사용량 로그
    usage_logs = db.query(AIUsageLog).filter(
        AIUsageLog.created_at >= start_date
    ).all()
    
    # 에이전트별 통계
    agent_stats = {}
    for log in usage_logs:
        agent_id = log.agent_id
        if agent_id not in agent_stats:
            agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
            agent_stats[agent_id] = {
                "agent_name": agent.name if agent else f"Agent #{agent_id}",
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "success_rate": 0
            }
        
        agent_stats[agent_id]["total_calls"] += 1
        agent_stats[agent_id]["total_tokens"] += log.total_tokens
        agent_stats[agent_id]["total_cost"] += log.cost
    
    # 성공률 계산
    for agent_id, stats in agent_stats.items():
        success_logs = [log for log in usage_logs 
                       if log.agent_id == agent_id and log.status == "success"]
        stats["success_rate"] = (len(success_logs) / stats["total_calls"]) * 100
    
    return {
        "period_days": days,
        "total_calls": len(usage_logs),
        "total_tokens": sum(log.total_tokens for log in usage_logs),
        "total_cost": sum(log.cost for log in usage_logs),
        "agent_statistics": list(agent_stats.values()),
        "daily_usage": _calculate_daily_usage(usage_logs, days)
    }

@router.get("/agents/{agent_id}/usage-detail")
async def get_agent_usage_detail(
    agent_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """특정 에이전트의 상세 사용량"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 에이전트를 찾을 수 없습니다"
        )
    
    start_date = datetime.now() - timedelta(days=days)
    usage_logs = db.query(AIUsageLog).filter(
        AIUsageLog.agent_id == agent_id,
        AIUsageLog.created_at >= start_date
    ).order_by(AIUsageLog.created_at.desc()).all()
    
    # 최근 작업
    recent_tasks = db.query(AITask).filter(
        AITask.agent_id == agent_id
    ).order_by(AITask.created_at.desc()).limit(10).all()
    
    return {
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type,
            "model": agent.model_name,
            "is_active": agent.is_active
        },
        "usage_logs": usage_logs,
        "recent_tasks": recent_tasks,
        "statistics": {
            "total_calls": len(usage_logs),
            "total_tokens": sum(log.total_tokens for log in usage_logs),
            "total_cost": sum(log.cost for log in usage_logs),
            "average_response_time": sum(log.duration_seconds or 0 for log in usage_logs) / len(usage_logs) if usage_logs else 0,
            "success_rate": (len([log for log in usage_logs if log.status == "success"]) / len(usage_logs)) * 100 if usage_logs else 0
        }
    }

# 프론트엔드용 에이전트 API 엔드포인트들
@router.get("/agents")
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db)
):
    """AI 에이전트 목록 조회 (프론트엔드용)"""
    query = db.query(AIAgent)
    
    if search:
        query = query.filter(AIAgent.name.contains(search))
    
    agents = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "agents": agents,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """개별 AI 에이전트 조회"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="AI 에이전트를 찾을 수 없습니다")
    return agent

@router.post("/agents")
async def create_agent(agent_data: AIAgentCreate, db: Session = Depends(get_db)):
    """AI 에이전트 생성"""
    return await _create_processing_agent(agent_data, db)

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: int, agent_data: AIAgentUpdate, db: Session = Depends(get_db)):
    """AI 에이전트 수정"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="AI 에이전트를 찾을 수 없습니다")
    
    update_data = agent_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    return agent

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """AI 에이전트 삭제"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="AI 에이전트를 찾을 수 없습니다")
    
    db.delete(agent)
    db.commit()
    return {"message": "AI 에이전트가 삭제되었습니다"}

@router.post("/agents/{agent_id}/test")
async def test_agent(agent_id: int, test_data: dict, db: Session = Depends(get_db)):
    """AI 에이전트 테스트"""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="AI 에이전트를 찾을 수 없습니다")
    
    prompt = test_data.get("prompt", "")
    # Mock response for testing
    response_text = f"[{agent.model_name}] {agent.name} 응답:\\n\\n질문: {prompt}\\n\\n테스트 응답입니다."
    
    return {"response": response_text}

@router.get("/models")
async def get_available_models():
    """사용 가능한 AI 모델 목록"""
    return {
        "models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo", 
            "claude-3-haiku",
            "claude-3-sonnet",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus"
        ]
    }

# API 키 관리 엔드포인트들 (테스트용 - 인증 없음)
@router.get("/test-api-keys-full")
async def get_api_keys_test(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    provider: str = None,
    db: Session = Depends(get_db)
):
    """API 키 목록 조회 (테스트용)"""
    query = db.query(APIKey)
    
    if search:
        query = query.filter(APIKey.key_name.contains(search))
    
    if provider:
        query = query.filter(APIKey.provider == provider)
    
    api_keys = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "api_keys": api_keys,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/test-api-keys/{key_id}")  
async def get_api_key_test(key_id: int, db: Session = Depends(get_db)):
    """개별 API 키 조회 (테스트용)"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    return api_key

@router.post("/test-api-keys")
async def create_api_key_test(key_data: dict, db: Session = Depends(get_db)):
    """API 키 생성 (테스트용)"""
    # 같은 이름의 키가 있는지 확인
    existing_key = db.query(APIKey).filter(APIKey.key_name == key_data["key_name"]).first()
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="같은 이름의 API 키가 이미 존재합니다"
        )
    
    db_key = APIKey(
        key_name=key_data["key_name"],
        description=key_data.get("description"),
        provider=key_data["provider"],
        encrypted_key=key_data["api_key"],  # 실제로는 암호화해야 함
        is_active=key_data.get("is_active", True)
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return db_key

@router.put("/test-api-keys/{key_id}")
async def update_api_key_test(key_id: int, key_data: dict, db: Session = Depends(get_db)):
    """API 키 수정 (테스트용)"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    # 업데이트할 필드들
    if "key_name" in key_data:
        api_key.key_name = key_data["key_name"]
    if "description" in key_data:
        api_key.description = key_data["description"]
    if "api_key" in key_data and key_data["api_key"]:
        api_key.encrypted_key = key_data["api_key"]  # 실제로는 암호화해야 함
    if "is_active" in key_data:
        api_key.is_active = key_data["is_active"]
    
    db.commit()
    db.refresh(api_key)
    return api_key

@router.delete("/test-api-keys/{key_id}")
async def delete_api_key_test(key_id: int, db: Session = Depends(get_db)):
    """API 키 삭제 (테스트용)"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    db.delete(api_key)
    db.commit()
    return {"message": "API 키가 삭제되었습니다"}

@router.post("/test-api-keys/{key_id}/toggle")
async def toggle_api_key_test(key_id: int, db: Session = Depends(get_db)):
    """API 키 활성화/비활성화 토글 (테스트용)"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    api_key.is_active = not api_key.is_active
    db.commit()
    db.refresh(api_key)
    
    return {
        "message": f"API 키가 {'활성화' if api_key.is_active else '비활성화'}되었습니다",
        "is_active": api_key.is_active
    }

# 테스트용 엔드포인트들 (인증 없음)
@router.get("/test-agents")
async def get_test_agents(db: Session = Depends(get_db)):
    """AI 에이전트 목록 조회 - 테스트용"""
    agents = db.query(AIAgent).all()
    return {"agents": len(agents), "data": agents}

@router.get("/test-api-keys")
async def get_test_api_keys(db: Session = Depends(get_db)):
    """API 키 목록 조회 - 테스트용"""
    keys = db.query(APIKey).all()
    return {"api_keys": len(keys), "data": [{"id": k.id, "provider": k.provider, "key_name": k.key_name, "is_active": k.is_active} for k in keys]}

@router.post("/initialize-test")
async def initialize_ai_system_test(db: Session = Depends(get_db)):
    """AI 시스템 초기화 - 테스트용 (인증 없음)"""
    return await _initialize_ai_system(db)

# 초기 데이터 설정
@router.post("/initialize")
async def initialize_ai_system(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """AI 시스템 초기화 - 기본 에이전트 및 API 키 설정"""
    return await _initialize_ai_system(db)

async def _initialize_ai_system(db: Session):
    """AI 시스템 초기화 내부 로직"""
    
    # 기본 AI 에이전트 생성
    default_agents = [
        {
            "name": "문서 분석 에이전트",
            "description": "PDF 문서 구조 분석 및 타입 식별",
            "agent_type": "document_analysis",
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "system_prompt": "당신은 PDF 문서를 분석하는 전문가입니다. 문서의 구조와 내용을 파악하여 문제집인지 교재인지 분류하고, 각 페이지의 콘텐츠 타입을 식별하세요.",
            "priority": 1
        },
        {
            "name": "문제 추출 에이전트",
            "description": "문제와 선택지, 정답 정밀 추출",
            "agent_type": "question_extraction",
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "system_prompt": "당신은 문제를 추출하는 전문가입니다. 텍스트에서 객관식 문제, 선택지, 정답을 정확하게 분리하고 구조화하세요.",
            "priority": 2
        },
        {
            "name": "학습자료 생성 에이전트",
            "description": "추출된 문제 기반 학습자료 생성",
            "agent_type": "study_material_generation",
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "system_prompt": "당신은 학습자료를 생성하는 교육 전문가입니다. 문제들을 분석하여 주제별 요약, 핵심 개념, 연관 문제를 정리하세요.",
            "priority": 3
        },
        {
            "name": "문제 생성 에이전트",
            "description": "이론 자료 기반 새로운 문제 생성",
            "agent_type": "question_generation",
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "system_prompt": "당신은 문제 출제 전문가입니다. 주어진 이론 내용을 바탕으로 다양한 난이도의 객관식 문제를 생성하세요.",
            "priority": 4
        },
        {
            "name": "해설 생성 에이전트",
            "description": "문제별 상세 해설 및 정답 생성",
            "agent_type": "explanation_generation",
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "system_prompt": "당신은 문제 해설 전문가입니다. 각 문제에 대해 단계별 풀이과정과 상세한 설명을 제공하세요.",
            "priority": 5
        }
    ]
    
    created_agents = 0
    for agent_data in default_agents:
        existing_agent = db.query(AIAgent).filter(AIAgent.name == agent_data["name"]).first()
        if not existing_agent:
            db_agent = AIAgent(
                name=agent_data["name"],
                description=agent_data["description"],
                agent_type=agent_data["agent_type"],
                model_name=agent_data["model_name"],
                provider=agent_data["provider"],
                system_prompt=agent_data["system_prompt"],
                priority=agent_data["priority"],
                is_active=True
            )
            db.add(db_agent)
            created_agents += 1
    
    # Claude API 키 등록
    claude_key_data = {
        "provider": "anthropic",
        "key_name": "Claude Main API Key",
        "api_key": "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",
        "is_active": True,
        "daily_limit": 50.0,  # $50 일일 한도
        "monthly_limit": 1000.0  # $1000 월간 한도
    }
    
    existing_key = db.query(APIKey).filter(APIKey.key_name == claude_key_data["key_name"]).first()
    created_keys = 0
    if not existing_key:
        db_key = APIKey(**claude_key_data, last_reset_date=datetime.now().date())
        db.add(db_key)
        created_keys = 1
    
    db.commit()
    
    return {
        "message": "AI 시스템 초기화가 완료되었습니다",
        "created_agents": created_agents,
        "created_api_keys": created_keys,
        "total_agents": len(default_agents)
    }

def _calculate_daily_usage(usage_logs, days):
    """일별 사용량 계산 헬퍼 함수"""
    daily_data = {}
    for log in usage_logs:
        date_str = log.created_at.strftime("%Y-%m-%d")
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "calls": 0,
                "tokens": 0,
                "cost": 0.0
            }
        daily_data[date_str]["calls"] += 1
        daily_data[date_str]["tokens"] += log.total_tokens
        daily_data[date_str]["cost"] += log.cost
    
    return list(daily_data.values())