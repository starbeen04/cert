from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Certificate, User, Question
from app.schemas import (
    CertificateCreate, 
    CertificateUpdate, 
    CertificateResponse, 
    PaginatedResponse
)
from app.models import CertificateStatus
from datetime import datetime
from app.auth import get_current_active_user, get_instructor_or_admin
from app.config import settings

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_certificates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    issuer: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all certificates with filtering and pagination."""
    query = db.query(Certificate)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Certificate.title.contains(search),
                Certificate.description.contains(search),
                Certificate.issuer.contains(search)
            )
        )
    
    if category:
        query = query.filter(Certificate.category == category)
    
    if difficulty:
        query = query.filter(Certificate.difficulty_level == difficulty)
    
    if issuer:
        query = query.filter(Certificate.issuer == issuer)
    
    if status:
        query = query.filter(Certificate.status == status)
    else:
        # Only show active certificates by default for non-authenticated users
        query = query.filter(Certificate.status == "active")
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    certificates = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=certificates,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    certificate: CertificateCreate,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new certificate (instructor/admin only)."""
    db_certificate = Certificate(
        **certificate.model_dump(),
        creator_id=current_user.id
    )
    
    db.add(db_certificate)
    db.commit()
    db.refresh(db_certificate)
    
    return db_certificate

@router.get("/my", response_model=PaginatedResponse)
async def get_my_certificates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get certificates created by current user."""
    query = db.query(Certificate).filter(Certificate.creator_id == current_user.id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    certificates = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=certificates,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/categories")
async def get_certificate_categories(db: Session = Depends(get_db)):
    """Get all certificate categories."""
    categories = db.query(Certificate.category).distinct().all()
    return [category[0] for category in categories if category[0]]

@router.get("/issuers")
async def get_certificate_issuers(db: Session = Depends(get_db)):
    """Get all certificate issuers."""
    issuers = db.query(Certificate.issuer).distinct().all()
    return [issuer[0] for issuer in issuers if issuer[0]]

@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    """Get certificate by ID."""
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return certificate

@router.put("/{certificate_id}", response_model=CertificateResponse)
async def update_certificate(
    certificate_id: int,
    certificate_update: CertificateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update certificate."""
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Check permissions
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update certificate fields
    for field, value in certificate_update.model_dump(exclude_unset=True).items():
        setattr(certificate, field, value)
    
    db.commit()
    db.refresh(certificate)
    
    return certificate

@router.delete("/{certificate_id}")
async def delete_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete certificate."""
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Check permissions
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(certificate)
    db.commit()
    
    return {"message": "Certificate deleted successfully"}

@router.get("/{certificate_id}/stats")
async def get_certificate_stats(
    certificate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get certificate statistics."""
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    # Check permissions
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get statistics
    question_count = db.query(Question).filter(Question.certificate_id == certificate_id).count()
    
    return {
        "certificate_id": certificate_id,
        "total_questions": question_count,
        "created_at": certificate.created_at,
        "updated_at": certificate.updated_at,
        "status": certificate.status
    }

# ============================================================================
# 관리자용 자격증 관리 API
# ============================================================================

@router.post("/admin/create", status_code=status.HTTP_201_CREATED)
async def admin_create_certificate(
    title: str,
    description: Optional[str] = None,
    issuer: str = "cert_fast",
    category: str = "기술",
    difficulty_level: str = "intermediate",
    exam_duration_minutes: Optional[int] = 120,
    passing_score: Optional[float] = 60.0,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 자격증 생성"""
    try:
        certificate = Certificate(
            title=title,
            description=description,
            issuer=issuer,
            category=category,
            difficulty_level=difficulty_level,
            status=CertificateStatus.ACTIVE,
            exam_duration_minutes=exam_duration_minutes,
            passing_score=passing_score,
            total_questions=0,
            tags=tags or [],
            creator_id=current_user.id
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        return {
            "success": True,
            "certificate_id": certificate.id,
            "message": f"자격증 '{title}'이 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자격증 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/admin/{certificate_id}/update")
async def admin_update_certificate(
    certificate_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    issuer: Optional[str] = None,
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    exam_duration_minutes: Optional[int] = None,
    passing_score: Optional[float] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 자격증 정보 수정"""
    try:
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="자격증을 찾을 수 없습니다."
            )
        
        # 업데이트할 필드들 적용
        if title is not None:
            certificate.title = title
        if description is not None:
            certificate.description = description
        if issuer is not None:
            certificate.issuer = issuer
        if category is not None:
            certificate.category = category
        if difficulty_level is not None:
            certificate.difficulty_level = difficulty_level
        if exam_duration_minutes is not None:
            certificate.exam_duration_minutes = exam_duration_minutes
        if passing_score is not None:
            certificate.passing_score = passing_score
        if status is not None:
            certificate.status = CertificateStatus(status)
        if tags is not None:
            certificate.tags = tags
            
        certificate.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(certificate)
        
        return {
            "success": True,
            "message": "자격증 정보가 성공적으로 업데이트되었습니다.",
            "certificate": {
                "id": certificate.id,
                "title": certificate.title,
                "issuer": certificate.issuer,
                "status": certificate.status.value,
                "updated_at": certificate.updated_at
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자격증 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/admin/{certificate_id}/delete")
async def admin_delete_certificate(
    certificate_id: int,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 자격증 삭제"""
    try:
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="자격증을 찾을 수 없습니다."
            )
        
        # 관련 문제 수 확인
        question_count = db.query(Question).filter(Question.certificate_id == certificate_id).count()
        
        # 소프트 삭제 (상태를 INACTIVE로 변경)
        certificate.status = CertificateStatus.INACTIVE
        certificate.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"자격증 '{certificate.title}'이 비활성화되었습니다.",
            "affected_questions": question_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자격증 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/admin/stats")
async def get_admin_certificate_stats(
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """관리자용 자격증 통계"""
    try:
        # 전체 자격증 수
        total_certificates = db.query(Certificate).count()
        
        # 상태별 자격증 수
        active_count = db.query(Certificate).filter(Certificate.status == CertificateStatus.ACTIVE).count()
        inactive_count = db.query(Certificate).filter(Certificate.status == CertificateStatus.INACTIVE).count()
        draft_count = db.query(Certificate).filter(Certificate.status == CertificateStatus.DRAFT).count()
        
        # 카테고리별 자격증 수
        category_stats = db.query(Certificate.category, db.func.count(Certificate.id))\
            .group_by(Certificate.category)\
            .all()
        
        # 발급기관별 자격증 수
        issuer_stats = db.query(Certificate.issuer, db.func.count(Certificate.id))\
            .group_by(Certificate.issuer)\
            .all()
        
        # 최근 생성된 자격증들
        recent_certificates = db.query(Certificate)\
            .order_by(Certificate.created_at.desc())\
            .limit(5)\
            .all()
        
        return {
            "success": True,
            "statistics": {
                "total_certificates": total_certificates,
                "status_breakdown": {
                    "active": active_count,
                    "inactive": inactive_count,
                    "draft": draft_count
                },
                "category_breakdown": [
                    {"category": cat, "count": count} for cat, count in category_stats
                ],
                "issuer_breakdown": [
                    {"issuer": issuer, "count": count} for issuer, count in issuer_stats
                ],
                "recent_certificates": [
                    {
                        "id": cert.id,
                        "title": cert.title,
                        "issuer": cert.issuer,
                        "category": cert.category,
                        "status": cert.status.value,
                        "created_at": cert.created_at
                    } for cert in recent_certificates
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )