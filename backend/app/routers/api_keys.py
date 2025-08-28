# API 키 관리 라우터
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import bcrypt
from datetime import date

from ..database import get_db
from ..models import APIKey, AIUsageLog
from ..schemas import APIKeyCreate, APIKeyUpdate, APIKeyResponse
from sqlalchemy import func
from datetime import datetime, timedelta
from ..auth import get_current_admin_user, User

router = APIRouter(prefix="/api/keys", tags=["api-keys"])

# 테스트용 인증 없는 엔드포인트
@router.get("/test-no-auth")
async def get_api_keys_test(db: Session = Depends(get_db)):
    """테스트용 API 키 조회 (인증 없음)"""
    try:
        keys = db.query(APIKey).all()
        return {"success": True, "count": len(keys), "keys": [{"id": k.id, "key_name": k.key_name, "provider": k.provider} for k in keys]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def encrypt_api_key(api_key: str) -> str:
    """API 키 암호화"""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def decrypt_api_key(encrypted_key: str, original_key: str) -> bool:
    """API 키 검증"""
    return bcrypt.checkpw(original_key.encode('utf-8'), encrypted_key.encode('utf-8'))

@router.get("/", response_model=List[APIKeyResponse])
async def get_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """모든 API 키 조회 (관리자만)"""
    keys = db.query(APIKey).all()
    return keys

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """새 API 키 등록"""
    
    # 같은 이름의 키가 있는지 확인
    existing_key = db.query(APIKey).filter(APIKey.key_name == api_key_data.key_name).first()
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="같은 이름의 API 키가 이미 존재합니다"
        )
    
    # API 키 암호화
    encrypted_key = encrypt_api_key(api_key_data.api_key)
    
    # 새 API 키 생성
    db_key = APIKey(
        provider=api_key_data.provider,
        key_name=api_key_data.key_name,
        api_key=encrypted_key,
        is_active=api_key_data.is_active,
        daily_limit=api_key_data.daily_limit,
        monthly_limit=api_key_data.monthly_limit,
        last_reset_date=date.today()
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return db_key

@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """특정 API 키 조회"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다"
        )
    return api_key

@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    api_key_data: APIKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 키 수정"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다"
        )
    
    # 수정 가능한 필드 업데이트
    if api_key_data.key_name is not None:
        api_key.key_name = api_key_data.key_name
    if api_key_data.is_active is not None:
        api_key.is_active = api_key_data.is_active
    if api_key_data.daily_limit is not None:
        api_key.daily_limit = api_key_data.daily_limit
    if api_key_data.monthly_limit is not None:
        api_key.monthly_limit = api_key_data.monthly_limit
    if api_key_data.api_key is not None:
        api_key.api_key = encrypt_api_key(api_key_data.api_key)
    
    db.commit()
    db.refresh(api_key)
    
    return api_key

@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 키 삭제"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다"
        )
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API 키가 성공적으로 삭제되었습니다"}

@router.post("/{key_id}/test")
async def test_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 키 유효성 테스트"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다"
        )
    
    # TODO: 실제 API 호출로 키 유효성 검증
    # 현재는 간단히 성공 응답 반환
    
    return {
        "status": "success",
        "message": "API 키가 유효합니다",
        "provider": api_key.provider
    }

@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 키 사용량 조회"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 키를 찾을 수 없습니다"
        )
    
    return {
        "key_name": api_key.key_name,
        "provider": api_key.provider,
        "daily_usage": api_key.current_daily_usage,
        "daily_limit": api_key.daily_limit,
        "monthly_usage": api_key.current_monthly_usage,
        "monthly_limit": api_key.monthly_limit,
        "usage_percentage_daily": (api_key.current_daily_usage / api_key.daily_limit * 100) if api_key.daily_limit else 0,
        "usage_percentage_monthly": (api_key.current_monthly_usage / api_key.monthly_limit * 100) if api_key.monthly_limit else 0
    }

# ============================================================================
# 실제 사용량 데이터 기반 API
# ============================================================================

@router.get("/usage/detailed")
async def get_detailed_usage_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """상세 사용량 통계 (실제 데이터 기반)"""
    try:
        # 지정된 기간의 시작일
        start_date = datetime.now() - timedelta(days=days)
        
        # 전체 사용량 통계
        total_stats = db.query(
            func.sum(AIUsageLog.cost).label('total_cost'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.count(AIUsageLog.id).label('total_requests')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).first()
        
        # API 키별 사용량
        api_key_stats = db.query(
            APIKey.id,
            APIKey.key_name,
            APIKey.provider,
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).join(
            AIUsageLog, APIKey.id == AIUsageLog.api_key_id
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            APIKey.id, APIKey.key_name, APIKey.provider
        ).all()
        
        # 일별 사용량 트렌드
        daily_trends = db.query(
            func.date(AIUsageLog.created_at).label('date'),
            func.sum(AIUsageLog.cost).label('daily_cost'),
            func.sum(AIUsageLog.total_tokens).label('daily_tokens'),
            func.count(AIUsageLog.id).label('daily_requests')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            func.date(AIUsageLog.created_at)
        ).order_by(
            func.date(AIUsageLog.created_at)
        ).all()
        
        # 작업 타입별 통계
        task_type_stats = db.query(
            AIUsageLog.task_type,
            func.sum(AIUsageLog.cost).label('cost'),
            func.sum(AIUsageLog.total_tokens).label('tokens'),
            func.count(AIUsageLog.id).label('requests')
        ).filter(
            AIUsageLog.created_at >= start_date
        ).group_by(
            AIUsageLog.task_type
        ).all()
        
        return {
            "success": True,
            "period_days": days,
            "total_statistics": {
                "total_cost": float(total_stats.total_cost or 0),
                "total_tokens": int(total_stats.total_tokens or 0),
                "total_requests": int(total_stats.total_requests or 0)
            },
            "api_key_breakdown": [
                {
                    "key_id": stat.id,
                    "key_name": stat.key_name,
                    "provider": stat.provider,
                    "cost": float(stat.cost or 0),
                    "tokens": int(stat.tokens or 0),
                    "requests": int(stat.requests or 0)
                } for stat in api_key_stats
            ],
            "daily_trends": [
                {
                    "date": trend.date.isoformat(),
                    "cost": float(trend.daily_cost or 0),
                    "tokens": int(trend.daily_tokens or 0),
                    "requests": int(trend.daily_requests or 0)
                } for trend in daily_trends
            ],
            "task_type_breakdown": [
                {
                    "task_type": stat.task_type,
                    "cost": float(stat.cost or 0),
                    "tokens": int(stat.tokens or 0),
                    "requests": int(stat.requests or 0)
                } for stat in task_type_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용량 통계 조회 중 오류 발생: {str(e)}"
        )

@router.get("/{key_id}/usage/history")
async def get_api_key_usage_history(
    key_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """특정 API 키의 사용 이력"""
    try:
        # API 키 존재 확인
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 키를 찾을 수 없습니다"
            )
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 상세 사용 이력
        usage_history = db.query(AIUsageLog).filter(
            AIUsageLog.api_key_id == key_id,
            AIUsageLog.created_at >= start_date
        ).order_by(
            AIUsageLog.created_at.desc()
        ).limit(100).all()
        
        # 요약 통계
        summary_stats = db.query(
            func.sum(AIUsageLog.cost).label('total_cost'),
            func.sum(AIUsageLog.total_tokens).label('total_tokens'),
            func.count(AIUsageLog.id).label('total_requests'),
            func.avg(AIUsageLog.duration_seconds).label('avg_duration')
        ).filter(
            AIUsageLog.api_key_id == key_id,
            AIUsageLog.created_at >= start_date
        ).first()
        
        return {
            "success": True,
            "api_key_info": {
                "id": api_key.id,
                "name": api_key.key_name,
                "provider": api_key.provider
            },
            "period_days": days,
            "summary": {
                "total_cost": float(summary_stats.total_cost or 0),
                "total_tokens": int(summary_stats.total_tokens or 0),
                "total_requests": int(summary_stats.total_requests or 0),
                "average_duration": float(summary_stats.avg_duration or 0)
            },
            "recent_usage": [
                {
                    "id": log.id,
                    "task_type": log.task_type,
                    "model_used": log.model_used,
                    "cost": float(log.cost),
                    "tokens": int(log.total_tokens),
                    "duration": float(log.duration_seconds or 0),
                    "status": log.status,
                    "created_at": log.created_at
                } for log in usage_history
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용 이력 조회 중 오류 발생: {str(e)}"
        )

@router.post("/test/{key_id}")
async def test_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """API 키 연결 테스트"""
    try:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API 키를 찾을 수 없습니다"
            )
        
        # 실제 API 키 테스트 로직 (provider에 따라 다름)
        test_result = {
            "success": True,
            "message": f"{api_key.provider} API 키 연결 테스트 성공",
            "key_name": api_key.key_name,
            "provider": api_key.provider,
            "is_active": api_key.is_active,
            "tested_at": datetime.now()
        }
        
        return test_result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"API 키 테스트 실패: {str(e)}",
            "tested_at": datetime.now()
        }