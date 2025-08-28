"""
API 키 사용량 분석 서비스
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import get_db

class UsageAnalyticsService:
    """API 키 사용량 분석 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_api_key_stats(self, api_key_id: int, days: int = 7) -> Dict[str, Any]:
        """특정 API 키의 통계 조회"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 기본 통계
        basic_stats = self.db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost) as total_cost,
                    AVG(duration_seconds) as avg_duration,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_requests,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_requests
                FROM ai_usage_logs 
                WHERE api_key_id = :api_key_id 
                AND created_at >= :start_date
            """),
            {
                "api_key_id": api_key_id,
                "start_date": start_date.isoformat()
            }
        ).fetchone()
        
        # 일별 사용량
        daily_usage = self.db.execute(
            text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(cost) as cost
                FROM ai_usage_logs 
                WHERE api_key_id = :api_key_id 
                AND created_at >= :start_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """),
            {
                "api_key_id": api_key_id,
                "start_date": start_date.isoformat()
            }
        ).fetchall()
        
        # 모델별 사용량
        model_usage = self.db.execute(
            text("""
                SELECT 
                    model_used,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(cost) as cost
                FROM ai_usage_logs 
                WHERE api_key_id = :api_key_id 
                AND created_at >= :start_date
                GROUP BY model_used
                ORDER BY cost DESC
            """),
            {
                "api_key_id": api_key_id,
                "start_date": start_date.isoformat()
            }
        ).fetchall()
        
        # 작업 유형별 사용량
        task_usage = self.db.execute(
            text("""
                SELECT 
                    task_type,
                    COUNT(*) as requests,
                    SUM(cost) as cost,
                    AVG(duration_seconds) as avg_duration
                FROM ai_usage_logs 
                WHERE api_key_id = :api_key_id 
                AND created_at >= :start_date
                GROUP BY task_type
                ORDER BY cost DESC
            """),
            {
                "api_key_id": api_key_id,
                "start_date": start_date.isoformat()
            }
        ).fetchall()
        
        return {
            "basic_stats": {
                "total_requests": basic_stats.total_requests or 0,
                "total_tokens": basic_stats.total_tokens or 0,
                "total_cost": float(basic_stats.total_cost or 0),
                "avg_duration": float(basic_stats.avg_duration or 0),
                "success_rate": (basic_stats.successful_requests / max(basic_stats.total_requests, 1)) * 100,
                "error_count": basic_stats.failed_requests or 0
            },
            "daily_usage": [
                {
                    "date": row.date,
                    "requests": row.requests,
                    "tokens": row.tokens or 0,
                    "cost": float(row.cost or 0)
                } for row in daily_usage
            ],
            "model_breakdown": [
                {
                    "model": row.model_used,
                    "requests": row.requests,
                    "tokens": row.tokens or 0,
                    "cost": float(row.cost or 0)
                } for row in model_usage
            ],
            "task_breakdown": [
                {
                    "task_type": row.task_type,
                    "requests": row.requests,
                    "cost": float(row.cost or 0),
                    "avg_duration": float(row.avg_duration or 0)
                } for row in task_usage
            ]
        }
    
    async def get_all_api_keys_summary(self) -> List[Dict[str, Any]]:
        """모든 API 키의 사용량 요약"""
        today = datetime.now().date()
        
        summary = self.db.execute(
            text("""
                SELECT 
                    ak.id,
                    ak.key_name,
                    ak.provider,
                    ak.monthly_limit,
                    ak.current_monthly_usage,
                    ak.daily_limit,
                    ak.current_daily_usage,
                    COALESCE(logs.today_requests, 0) as today_requests,
                    COALESCE(logs.today_cost, 0) as today_cost,
                    COALESCE(logs.week_cost, 0) as week_cost
                FROM api_keys ak
                LEFT JOIN (
                    SELECT 
                        api_key_id,
                        COUNT(CASE WHEN DATE(created_at) = :today THEN 1 END) as today_requests,
                        SUM(CASE WHEN DATE(created_at) = :today THEN cost ELSE 0 END) as today_cost,
                        SUM(CASE WHEN created_at >= :week_ago THEN cost ELSE 0 END) as week_cost
                    FROM ai_usage_logs
                    WHERE created_at >= :week_ago
                    GROUP BY api_key_id
                ) logs ON ak.id = logs.api_key_id
                WHERE ak.is_active = 1
                ORDER BY ak.current_monthly_usage DESC
            """),
            {
                "today": today.isoformat(),
                "week_ago": (datetime.now() - timedelta(days=7)).isoformat()
            }
        ).fetchall()
        
        return [
            {
                "id": row.id,
                "key_name": row.key_name,
                "provider": row.provider,
                "monthly_limit": float(row.monthly_limit or 0),
                "current_monthly_usage": float(row.current_monthly_usage or 0),
                "daily_limit": float(row.daily_limit or 0),
                "current_daily_usage": float(row.current_daily_usage or 0),
                "today_requests": row.today_requests,
                "today_cost": float(row.today_cost or 0),
                "week_cost": float(row.week_cost or 0),
                "monthly_usage_percent": (row.current_monthly_usage / max(row.monthly_limit, 1)) * 100 if row.monthly_limit else 0,
                "daily_usage_percent": (row.current_daily_usage / max(row.daily_limit, 1)) * 100 if row.daily_limit else 0
            } for row in summary
        ]
    
    async def check_usage_limits(self) -> List[Dict[str, Any]]:
        """사용량 한도 초과 확인"""
        alerts = []
        
        # 일일 한도 초과 확인
        daily_exceeded = self.db.execute(
            text("""
                SELECT id, key_name, daily_limit, current_daily_usage
                FROM api_keys 
                WHERE is_active = 1 
                AND daily_limit > 0 
                AND current_daily_usage >= daily_limit * 0.9
            """)
        ).fetchall()
        
        for row in daily_exceeded:
            usage_percent = (row.current_daily_usage / row.daily_limit) * 100
            alerts.append({
                "type": "daily_limit" if usage_percent >= 100 else "daily_warning",
                "api_key_id": row.id,
                "key_name": row.key_name,
                "limit": row.daily_limit,
                "current_usage": row.current_daily_usage,
                "usage_percent": usage_percent,
                "message": f"일일 한도 {'초과' if usage_percent >= 100 else '90% 도달'}: {row.key_name}"
            })
        
        # 월간 한도 초과 확인
        monthly_exceeded = self.db.execute(
            text("""
                SELECT id, key_name, monthly_limit, current_monthly_usage
                FROM api_keys 
                WHERE is_active = 1 
                AND monthly_limit > 0 
                AND current_monthly_usage >= monthly_limit * 0.9
            """)
        ).fetchall()
        
        for row in monthly_exceeded:
            usage_percent = (row.current_monthly_usage / row.monthly_limit) * 100
            alerts.append({
                "type": "monthly_limit" if usage_percent >= 100 else "monthly_warning",
                "api_key_id": row.id,
                "key_name": row.key_name,
                "limit": row.monthly_limit,
                "current_usage": row.current_monthly_usage,
                "usage_percent": usage_percent,
                "message": f"월간 한도 {'초과' if usage_percent >= 100 else '90% 도달'}: {row.key_name}"
            })
        
        return alerts
    
    async def reset_daily_usage(self):
        """일일 사용량 초기화 (매일 자정 실행)"""
        self.db.execute(
            text("""
                UPDATE api_keys 
                SET current_daily_usage = 0, 
                    last_reset_date = :today
                WHERE is_active = 1
            """),
            {"today": datetime.now().date().isoformat()}
        )
        self.db.commit()
    
    async def get_cost_trends(self, days: int = 30) -> Dict[str, Any]:
        """비용 트렌드 분석"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 일별 전체 비용
        daily_costs = self.db.execute(
            text("""
                SELECT 
                    DATE(created_at) as date,
                    SUM(cost) as total_cost,
                    COUNT(*) as total_requests
                FROM ai_usage_logs 
                WHERE created_at >= :start_date
                GROUP BY DATE(created_at)
                ORDER BY date
            """),
            {"start_date": start_date.isoformat()}
        ).fetchall()
        
        # 제공업체별 비용
        provider_costs = self.db.execute(
            text("""
                SELECT 
                    ak.provider,
                    SUM(ul.cost) as total_cost,
                    COUNT(ul.id) as total_requests
                FROM ai_usage_logs ul
                JOIN api_keys ak ON ul.api_key_id = ak.id
                WHERE ul.created_at >= :start_date
                GROUP BY ak.provider
                ORDER BY total_cost DESC
            """),
            {"start_date": start_date.isoformat()}
        ).fetchall()
        
        return {
            "daily_trends": [
                {
                    "date": row.date,
                    "cost": float(row.total_cost or 0),
                    "requests": row.total_requests
                } for row in daily_costs
            ],
            "provider_breakdown": [
                {
                    "provider": row.provider,
                    "cost": float(row.total_cost or 0),
                    "requests": row.total_requests
                } for row in provider_costs
            ],
            "period_summary": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "total_cost": sum(float(row.total_cost or 0) for row in daily_costs),
                "total_requests": sum(row.total_requests for row in daily_costs),
                "avg_daily_cost": sum(float(row.total_cost or 0) for row in daily_costs) / max(len(daily_costs), 1)
            }
        }