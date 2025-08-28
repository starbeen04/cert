from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models import AIAgent, User, ChatSession, ChatMessage, AIUsageLog, AgentStatus
from app.schemas import (
    AIAgentCreate, 
    AIAgentUpdate, 
    AIAgentResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    PaginatedResponse
)
from app.auth import get_current_active_user, get_instructor_or_admin, get_current_admin_user
from app.config import settings
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_ai_agents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all AI agents with filtering and pagination."""
    query = db.query(AIAgent)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                AIAgent.name.contains(search),
                AIAgent.description.contains(search)
            )
        )
    
    if agent_type:
        query = query.filter(AIAgent.agent_type == agent_type)
    
    if status:
        query = query.filter(AIAgent.status == status)
    else:
        # Only show active agents by default
        query = query.filter(AIAgent.status == "active")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    agents = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=agents,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_agent(
    agent: AIAgentCreate,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new AI agent (instructor/admin only)."""
    db_agent = AIAgent(
        **agent.model_dump(),
        creator_id=current_user.id
    )
    
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    return db_agent

@router.get("/my", response_model=PaginatedResponse)
async def get_my_ai_agents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI agents created by current user."""
    query = db.query(AIAgent).filter(AIAgent.creator_id == current_user.id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    agents = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=agents,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/types")
async def get_agent_types():
    """Get available AI agent types."""
    return [
        {"type": "tutor", "description": "AI tutor for personalized learning"},
        {"type": "quiz_master", "description": "AI quiz generator and evaluator"},
        {"type": "study_planner", "description": "AI study schedule planner"},
        {"type": "content_analyzer", "description": "AI content analysis and summarization"}
    ]

@router.get("/{agent_id}", response_model=AIAgentResponse)
async def get_ai_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get AI agent by ID."""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI agent not found"
        )
    
    return agent

@router.put("/{agent_id}", response_model=AIAgentResponse)
async def update_ai_agent(
    agent_id: int,
    agent_update: AIAgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update AI agent."""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI agent not found"
        )
    
    # Check permissions
    if (agent.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update agent fields
    for field, value in agent_update.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent

@router.delete("/{agent_id}")
async def delete_ai_agent(
    agent_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete AI agent."""
    agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI agent not found"
        )
    
    # Check permissions
    if (agent.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(agent)
    db.commit()
    
    return {"message": "AI agent deleted successfully"}

# Chat Session endpoints
@router.post("/{agent_id}/chat", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    agent_id: int,
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session with an AI agent."""
    # Verify agent exists and is active
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.status == "active"
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI agent not found or inactive"
        )
    
    db_session = ChatSession(
        user_id=current_user.id,
        ai_agent_id=agent_id,
        session_name=session_data.session_name
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.get("/sessions/my", response_model=List[ChatSessionResponse])
async def get_my_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for current user."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return sessions

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Create user message
    user_message = ChatMessage(
        session_id=session_id,
        message_type="user",
        content=message_data.content
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 실제 AI 서비스 호출
    try:
        from services.ai_service import ai_service
        ai_response_content = await ai_service.generate_response(
            model_name=session.ai_agent.model_name,
            system_prompt=session.ai_agent.system_prompt,
            user_prompt=message_data.content
        )
    except Exception as e:
        ai_response_content = f"AI 서비스 오류: {str(e)}"
    
    ai_message = ChatMessage(
        session_id=session_id,
        message_type="assistant",
        content=ai_response_content
    )
    
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    # Update session timestamp
    from datetime import datetime
    session.updated_at = datetime.utcnow()
    db.commit()
    
    return ai_message

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a chat session."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return messages

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}

# ============================================================================
# 관리자용 AI 에이전트 관리 API
# ============================================================================

@router.post("/admin/create", status_code=status.HTTP_201_CREATED)
async def admin_create_ai_agent(
    name: str,
    description: Optional[str] = None,
    agent_type: str = "tutor",
    model_name: str = "claude-3-5-sonnet-20241022",
    provider: str = "anthropic",
    system_prompt: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    priority: int = 1,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 AI 에이전트 생성"""
    try:
        ai_agent = AIAgent(
            name=name,
            description=description,
            agent_type=agent_type,
            model_name=model_name,
            provider=provider,
            system_prompt=system_prompt or f"You are a helpful {agent_type} AI assistant.",
            status=AgentStatus.ACTIVE,
            is_active=True,
            max_tokens=max_tokens,
            temperature=temperature,
            priority=priority,
            creator_id=current_user.id
        )
        
        db.add(ai_agent)
        db.commit()
        db.refresh(ai_agent)
        
        return {
            "success": True,
            "agent_id": ai_agent.id,
            "message": f"AI 에이전트 '{name}'이 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 에이전트 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/admin/{agent_id}/update")
async def admin_update_ai_agent(
    agent_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    agent_type: Optional[str] = None,
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 AI 에이전트 정보 수정"""
    try:
        ai_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI 에이전트를 찾을 수 없습니다."
            )
        
        # 업데이트할 필드들 적용
        if name is not None:
            ai_agent.name = name
        if description is not None:
            ai_agent.description = description
        if agent_type is not None:
            ai_agent.agent_type = agent_type
        if model_name is not None:
            ai_agent.model_name = model_name
        if provider is not None:
            ai_agent.provider = provider
        if system_prompt is not None:
            ai_agent.system_prompt = system_prompt
        if max_tokens is not None:
            ai_agent.max_tokens = max_tokens
        if temperature is not None:
            ai_agent.temperature = temperature
        if priority is not None:
            ai_agent.priority = priority
        if status is not None:
            ai_agent.status = AgentStatus(status)
        if is_active is not None:
            ai_agent.is_active = is_active
            
        ai_agent.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ai_agent)
        
        return {
            "success": True,
            "message": "AI 에이전트 정보가 성공적으로 업데이트되었습니다.",
            "agent": {
                "id": ai_agent.id,
                "name": ai_agent.name,
                "agent_type": ai_agent.agent_type,
                "status": ai_agent.status.value,
                "updated_at": ai_agent.updated_at
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 에이전트 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/admin/{agent_id}/delete")
async def admin_delete_ai_agent(
    agent_id: int,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 AI 에이전트 삭제"""
    try:
        ai_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI 에이전트를 찾을 수 없습니다."
            )
        
        # 관련 채팅 세션 수 확인
        session_count = db.query(ChatSession).filter(ChatSession.ai_agent_id == agent_id).count()
        
        # 소프트 삭제 (상태를 INACTIVE로 변경)
        ai_agent.status = AgentStatus.INACTIVE
        ai_agent.is_active = False
        ai_agent.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"AI 에이전트 '{ai_agent.name}'이 비활성화되었습니다.",
            "affected_sessions": session_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 에이전트 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/admin/stats")
async def get_admin_ai_agent_stats(
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 AI 에이전트 통계"""
    try:
        # 전체 에이전트 수
        total_agents = db.query(AIAgent).count()
        
        # 상태별 에이전트 수
        active_count = db.query(AIAgent).filter(AIAgent.status == AgentStatus.ACTIVE).count()
        inactive_count = db.query(AIAgent).filter(AIAgent.status == AgentStatus.INACTIVE).count()
        training_count = db.query(AIAgent).filter(AIAgent.status == AgentStatus.TRAINING).count()
        
        # 타입별 에이전트 수
        type_stats = db.query(AIAgent.agent_type, func.count(AIAgent.id))\
            .group_by(AIAgent.agent_type)\
            .all()
        
        # 제공사별 에이전트 수
        provider_stats = db.query(AIAgent.provider, func.count(AIAgent.id))\
            .group_by(AIAgent.provider)\
            .all()
        
        # 최근 생성된 에이전트들
        recent_agents = db.query(AIAgent)\
            .order_by(AIAgent.created_at.desc())\
            .limit(5)\
            .all()
        
        # 총 채팅 세션 수
        total_sessions = db.query(ChatSession).count()
        
        return {
            "success": True,
            "statistics": {
                "total_agents": total_agents,
                "status_breakdown": {
                    "active": active_count,
                    "inactive": inactive_count,
                    "training": training_count
                },
                "type_breakdown": [
                    {"type": agent_type, "count": count} for agent_type, count in type_stats
                ],
                "provider_breakdown": [
                    {"provider": provider, "count": count} for provider, count in provider_stats
                ],
                "total_chat_sessions": total_sessions,
                "recent_agents": [
                    {
                        "id": agent.id,
                        "name": agent.name,
                        "agent_type": agent.agent_type,
                        "provider": agent.provider,
                        "status": agent.status.value,
                        "created_at": agent.created_at
                    } for agent in recent_agents
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{agent_id}/usage/stats")
async def get_agent_usage_stats(
    agent_id: int,
    days: int = 30,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """특정 AI 에이전트의 사용 통계"""
    try:
        # 에이전트 존재 확인
        ai_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not ai_agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI 에이전트를 찾을 수 없습니다."
            )
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 사용량 통계
        usage_stats = db.query(
            func.sum(AIUsageLog.cost).label('total_cost'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.count(AIUsageLog.id).label('total_requests'),
            func.avg(AIUsageLog.duration_seconds).label('avg_duration')
        ).filter(
            AIUsageLog.agent_id == agent_id,
            AIUsageLog.created_at >= start_date
        ).first()
        
        # 일별 사용량 트렌드
        daily_usage = db.query(
            func.date(AIUsageLog.created_at).label('date'),
            func.sum(AIUsageLog.cost).label('daily_cost'),
            func.sum(AIUsageLog.total_tokens).label('daily_tokens'),
            func.count(AIUsageLog.id).label('daily_requests')
        ).filter(
            AIUsageLog.agent_id == agent_id,
            AIUsageLog.created_at >= start_date
        ).group_by(
            func.date(AIUsageLog.created_at)
        ).order_by(
            func.date(AIUsageLog.created_at)
        ).all()
        
        # 태스크 타입별 사용량
        task_stats = db.query(
            AIUsageLog.task_type,
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).filter(
            AIUsageLog.agent_id == agent_id,
            AIUsageLog.created_at >= start_date
        ).group_by(
            AIUsageLog.task_type
        ).all()
        
        # 채팅 세션 수
        session_count = db.query(ChatSession).filter(ChatSession.ai_agent_id == agent_id).count()
        
        return {
            "success": True,
            "agent_info": {
                "id": ai_agent.id,
                "name": ai_agent.name,
                "agent_type": ai_agent.agent_type,
                "provider": ai_agent.provider
            },
            "period_days": days,
            "summary": {
                "total_cost": float(usage_stats.total_cost or 0),
                "total_tokens": int(usage_stats.total_tokens or 0),
                "total_requests": int(usage_stats.total_requests or 0),
                "average_duration": float(usage_stats.avg_duration or 0),
                "total_sessions": session_count
            },
            "daily_trends": [
                {
                    "date": trend.date.isoformat(),
                    "cost": float(trend.daily_cost or 0),
                    "tokens": int(trend.daily_tokens or 0),
                    "requests": int(trend.daily_requests or 0)
                } for trend in daily_usage
            ],
            "task_breakdown": [
                {
                    "task_type": stat.task_type,
                    "cost": float(stat.cost or 0),
                    "tokens": int(stat.tokens or 0),
                    "requests": int(stat.requests or 0)
                } for stat in task_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용량 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/usage/overview")
async def get_ai_usage_overview(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """전체 AI 사용량 개요 (관리자만)"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # 전체 사용량 통계
        total_stats = db.query(
            func.sum(AIUsageLog.cost).label('total_cost'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.count(AIUsageLog.id).label('total_requests'),
            func.count(func.distinct(AIUsageLog.agent_id)).label('active_agents')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).first()
        
        # 에이전트별 사용량 TOP 10
        top_agents = db.query(
            AIAgent.name,
            AIAgent.agent_type,
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).join(
            AIUsageLog, AIAgent.id == AIUsageLog.agent_id
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            AIAgent.id, AIAgent.name, AIAgent.agent_type
        ).order_by(
            func.sum(AIUsageLog.cost).desc()
        ).limit(10).all()
        
        # 에러 통계
        error_stats = db.query(
            AIUsageLog.status,
            func.count(AIUsageLog.id).label('count')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            AIUsageLog.status
        ).all()
        
        # 시간대별 사용량
        hourly_usage = db.query(
            func.extract('hour', AIUsageLog.created_at).label('hour'),
            func.sum(AIUsageLog.cost).label('cost'),
            func.count(AIUsageLog.id).label('requests')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            func.extract('hour', AIUsageLog.created_at)
        ).order_by(
            func.extract('hour', AIUsageLog.created_at)
        ).all()
        
        return {
            "success": True,
            "period_days": days,
            "overview": {
                "total_cost": float(total_stats.total_cost or 0),
                "total_tokens": int(total_stats.total_tokens or 0),
                "total_requests": int(total_stats.total_requests or 0),
                "active_agents": int(total_stats.active_agents or 0)
            },
            "top_agents": [
                {
                    "name": agent.name,
                    "type": agent.agent_type,
                    "cost": float(agent.cost or 0),
                    "tokens": int(agent.tokens or 0),
                    "requests": int(agent.requests or 0)
                } for agent in top_agents
            ],
            "error_breakdown": [
                {
                    "status": stat.status,
                    "count": int(stat.count or 0)
                } for stat in error_stats
            ],
            "hourly_usage": [
                {
                    "hour": int(usage.hour),
                    "cost": float(usage.cost or 0),
                    "requests": int(usage.requests or 0)
                } for usage in hourly_usage
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용량 개요 조회 중 오류가 발생했습니다: {str(e)}"
        )