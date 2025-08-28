"""
Health check and system status endpoints (simplified version)
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CertFast API",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check (simplified without DB)."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "healthy",
            "database": "not_configured",
            "storage": "healthy"
        },
        "uptime": "running",
        "version": "1.0.0"
    }