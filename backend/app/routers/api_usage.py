"""
API 키 사용량 관리 라우터
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.auth import get_admin_user
from app.models import User
from app.services.usage_analytics import UsageAnalyticsService

router = APIRouter()

@router.get("/stats/{api_key_id}")
async def get_api_key_stats(
    api_key_id: int,
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """특정 API 키의 상세 사용량 통계"""
    
    # API 키 존재 확인
    api_key = db.execute(
        text("SELECT id, key_name FROM api_keys WHERE id = :id AND is_active = 1"),
        {"id": api_key_id}
    ).fetchone()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    analytics = UsageAnalyticsService(db)
    stats = await analytics.get_api_key_stats(api_key_id, days)
    
    return {
        "api_key": {
            "id": api_key.id,
            "name": api_key.key_name
        },
        "period": {
            "days": days,
            "end_date": datetime.now().date().isoformat(),
            "start_date": (datetime.now() - timedelta(days=days)).date().isoformat()
        },
        **stats
    }

@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """전체 API 키 사용량 요약"""
    
    analytics = UsageAnalyticsService(db)
    summary = await analytics.get_all_api_keys_summary()
    
    # 전체 통계 계산
    total_monthly_usage = sum(key["current_monthly_usage"] for key in summary)
    total_daily_usage = sum(key["current_daily_usage"] for key in summary)
    total_today_requests = sum(key["today_requests"] for key in summary)
    
    return {
        "summary": {
            "total_api_keys": len(summary),
            "total_monthly_usage": total_monthly_usage,
            "total_daily_usage": total_daily_usage,
            "total_today_requests": total_today_requests,
            "active_keys": len([k for k in summary if k["today_requests"] > 0])
        },
        "api_keys": summary
    }

@router.get("/alerts")
async def get_usage_alerts(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """사용량 한도 경고 및 초과 알림"""
    
    analytics = UsageAnalyticsService(db)
    alerts = await analytics.check_usage_limits()
    
    # 알림 분류
    critical = [a for a in alerts if a["type"].endswith("_limit")]
    warnings = [a for a in alerts if a["type"].endswith("_warning")]
    
    return {
        "total_alerts": len(alerts),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "critical_alerts": critical,
        "warnings": warnings
    }

@router.get("/trends")
async def get_cost_trends(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """비용 트렌드 분석"""
    
    analytics = UsageAnalyticsService(db)
    trends = await analytics.get_cost_trends(days)
    
    return trends

@router.get("/realtime")
async def get_realtime_usage(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """실시간 사용량 현황 (최근 1시간)"""
    
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    # 최근 1시간 활동
    recent_activity = db.execute(
        text("""
            SELECT 
                ak.key_name,
                ak.provider,
                COUNT(*) as requests,
                SUM(ul.cost) as cost,
                AVG(ul.duration_seconds) as avg_duration
            FROM ai_usage_logs ul
            JOIN api_keys ak ON ul.api_key_id = ak.id
            WHERE ul.created_at >= :since
            GROUP BY ul.api_key_id, ak.key_name, ak.provider
            ORDER BY requests DESC
        """),
        {"since": one_hour_ago.isoformat()}
    ).fetchall()
    
    # 분당 요청 수
    minute_stats = db.execute(
        text("""
            SELECT 
                strftime('%Y-%m-%d %H:%M', created_at) as minute,
                COUNT(*) as requests,
                SUM(cost) as cost
            FROM ai_usage_logs
            WHERE created_at >= :since
            GROUP BY strftime('%Y-%m-%d %H:%M', created_at)
            ORDER BY minute DESC
            LIMIT 60
        """),
        {"since": one_hour_ago.isoformat()}
    ).fetchall()
    
    return {
        "period": "last_hour",
        "timestamp": datetime.now().isoformat(),
        "active_keys": [
            {
                "key_name": row.key_name,
                "provider": row.provider,
                "requests": row.requests,
                "cost": float(row.cost or 0),
                "avg_duration": float(row.avg_duration or 0)
            } for row in recent_activity
        ],
        "minute_breakdown": [
            {
                "minute": row.minute,
                "requests": row.requests,
                "cost": float(row.cost or 0)
            } for row in reversed(minute_stats)  # 시간순 정렬
        ],
        "totals": {
            "requests": sum(row.requests for row in recent_activity),
            "cost": sum(float(row.cost or 0) for row in recent_activity),
            "active_keys": len(recent_activity)
        }
    }

@router.post("/reset-daily")
async def reset_daily_usage(
    api_key_id: Optional[int] = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """일일 사용량 수동 초기화"""
    
    if api_key_id:
        # 특정 API 키만 초기화
        result = db.execute(
            text("""
                UPDATE api_keys 
                SET current_daily_usage = 0, 
                    last_reset_date = :today,
                    updated_at = :now
                WHERE id = :api_key_id AND is_active = 1
            """),
            {
                "api_key_id": api_key_id,
                "today": datetime.now().date().isoformat(),
                "now": datetime.now().isoformat()
            }
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")
        message = f"API key {api_key_id} daily usage reset"
    else:
        # 모든 API 키 초기화
        analytics = UsageAnalyticsService(db)
        await analytics.reset_daily_usage()
        message = "All API keys daily usage reset"
    
    return {"message": message}

@router.get("/export")
async def export_usage_data(
    start_date: str = Query(..., description="YYYY-MM-DD format"),
    end_date: str = Query(..., description="YYYY-MM-DD format"), 
    api_key_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """사용량 데이터 내보내기"""
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if (end_dt - start_dt).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    # 쿼리 구성
    query = """
        SELECT 
            ul.created_at,
            ak.key_name,
            ak.provider,
            ul.task_type,
            ul.model_used,
            ul.prompt_tokens,
            ul.completion_tokens,
            ul.total_tokens,
            ul.cost,
            ul.duration_seconds,
            ul.status
        FROM ai_usage_logs ul
        JOIN api_keys ak ON ul.api_key_id = ak.id
        WHERE ul.created_at >= :start_date AND ul.created_at <= :end_date
    """
    
    params = {
        "start_date": start_dt.isoformat(),
        "end_date": (end_dt + timedelta(days=1)).isoformat()
    }
    
    if api_key_id:
        query += " AND ul.api_key_id = :api_key_id"
        params["api_key_id"] = api_key_id
    
    query += " ORDER BY ul.created_at DESC"
    
    results = db.execute(text(query), params).fetchall()
    
    data = [
        {
            "timestamp": row.created_at,
            "api_key": row.key_name,
            "provider": row.provider,
            "task_type": row.task_type,
            "model": row.model_used,
            "prompt_tokens": row.prompt_tokens or 0,
            "completion_tokens": row.completion_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "cost": float(row.cost or 0),
            "duration": float(row.duration_seconds or 0),
            "status": row.status
        } for row in results
    ]
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_records": len(data),
        "total_cost": sum(item["cost"] for item in data),
        "total_tokens": sum(item["total_tokens"] for item in data),
        "data": data
    }