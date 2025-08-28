from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import (
    StudyMaterial, 
    Question, 
    Certificate, 
    User, 
    StudySession,
    LearningStatistics
)
from app.schemas import (
    StudyMaterialCreate,
    StudyMaterialUpdate,
    StudyMaterialResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    StudySessionCreate,
    StudySessionUpdate,
    StudySessionResponse,
    LearningStatsResponse,
    PaginatedResponse
)
from app.auth import get_current_active_user, get_instructor_or_admin
from app.config import settings
from datetime import datetime

router = APIRouter()

# Study Materials endpoints
@router.get("/materials", response_model=PaginatedResponse)
async def get_study_materials(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    certificate_id: Optional[int] = None,
    material_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get study materials with filtering and pagination."""
    query = db.query(StudyMaterial)
    
    # Apply filters
    if certificate_id:
        query = query.filter(StudyMaterial.certificate_id == certificate_id)
    
    if material_type:
        query = query.filter(StudyMaterial.material_type == material_type)
    
    if search:
        query = query.filter(
            or_(
                StudyMaterial.title.contains(search),
                StudyMaterial.content.contains(search)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    materials = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=materials,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/materials", response_model=StudyMaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_study_material(
    material: StudyMaterialCreate,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new study material (instructor/admin only)."""
    # Verify certificate exists and user has permission
    certificate = db.query(Certificate).filter(Certificate.id == material.certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_material = StudyMaterial(**material.model_dump())
    
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    
    return db_material

@router.get("/materials/{material_id}", response_model=StudyMaterialResponse)
async def get_study_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Get study material by ID."""
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study material not found"
        )
    
    return material

@router.put("/materials/{material_id}", response_model=StudyMaterialResponse)
async def update_study_material(
    material_id: int,
    material_update: StudyMaterialUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update study material."""
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study material not found"
        )
    
    # Check permissions through certificate
    certificate = db.query(Certificate).filter(Certificate.id == material.certificate_id).first()
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update material fields
    for field, value in material_update.model_dump(exclude_unset=True).items():
        setattr(material, field, value)
    
    db.commit()
    db.refresh(material)
    
    return material

@router.delete("/materials/{material_id}")
async def delete_study_material(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete study material."""
    material = db.query(StudyMaterial).filter(StudyMaterial.id == material_id).first()
    
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study material not found"
        )
    
    # Check permissions through certificate
    certificate = db.query(Certificate).filter(Certificate.id == material.certificate_id).first()
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(material)
    db.commit()
    
    return {"message": "Study material deleted successfully"}

# Questions endpoints
@router.get("/questions", response_model=PaginatedResponse)
async def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    certificate_id: Optional[int] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get questions with filtering and pagination."""
    query = db.query(Question)
    
    # Apply filters
    if certificate_id:
        query = query.filter(Question.certificate_id == certificate_id)
    
    if question_type:
        query = query.filter(Question.question_type == question_type)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    questions = query.offset(offset).limit(size).all()
    
    # Calculate total pages
    pages = (total + size - 1) // size
    
    return PaginatedResponse(
        items=questions,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_instructor_or_admin),
    db: Session = Depends(get_db)
):
    """Create a new question (instructor/admin only)."""
    # Verify certificate exists and user has permission
    certificate = db.query(Certificate).filter(Certificate.id == question.certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_question = Question(**question.model_dump())
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # Update certificate question count
    certificate.total_questions = db.query(Question).filter(
        Question.certificate_id == certificate.id
    ).count()
    db.commit()
    
    return db_question

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """Get question by ID."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return question

@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions through certificate
    certificate = db.query(Certificate).filter(Certificate.id == question.certificate_id).first()
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update question fields
    for field, value in question_update.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    
    db.commit()
    db.refresh(question)
    
    return question

@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check permissions through certificate
    certificate = db.query(Certificate).filter(Certificate.id == question.certificate_id).first()
    if (certificate.creator_id != current_user.id and 
        current_user.role.value not in ["admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    certificate_id = question.certificate_id
    db.delete(question)
    db.commit()
    
    # Update certificate question count
    certificate.total_questions = db.query(Question).filter(
        Question.certificate_id == certificate_id
    ).count()
    db.commit()
    
    return {"message": "Question deleted successfully"}

# Study Sessions endpoints
@router.post("/sessions", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED)
async def create_study_session(
    session: StudySessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a new study session."""
    # Verify certificate exists
    certificate = db.query(Certificate).filter(Certificate.id == session.certificate_id).first()
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    db_session = StudySession(
        user_id=current_user.id,
        **session.model_dump()
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.get("/sessions/my", response_model=List[StudySessionResponse])
async def get_my_study_sessions(
    certificate_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get study sessions for current user."""
    query = db.query(StudySession).filter(StudySession.user_id == current_user.id)
    
    if certificate_id:
        query = query.filter(StudySession.certificate_id == certificate_id)
    
    sessions = query.order_by(StudySession.started_at.desc()).all()
    
    return sessions

@router.get("/sessions/{session_id}", response_model=StudySessionResponse)
async def get_study_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get study session by ID."""
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found"
        )
    
    return session

@router.put("/sessions/{session_id}", response_model=StudySessionResponse)
async def update_study_session(
    session_id: int,
    session_update: StudySessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update study session (submit answers, mark complete)."""
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found"
        )
    
    # Update session fields
    for field, value in session_update.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    
    # If marking as completed, calculate score
    if session_update.completed and session.answers:
        # TODO: Implement score calculation logic
        session.completed_at = datetime.utcnow()
        # Placeholder score calculation
        session.correct_answers = len(session.answers) // 2  # Mock calculation
        session.score_percentage = (session.correct_answers / session.total_questions) * 100
        
        # Check if passed
        certificate = db.query(Certificate).filter(Certificate.id == session.certificate_id).first()
        if certificate.passing_score:
            session.passed = session.score_percentage >= certificate.passing_score
    
    db.commit()
    db.refresh(session)
    
    # Update learning statistics
    if session.completed:
        update_learning_statistics(db, current_user.id, session.certificate_id, session)
    
    return session

@router.get("/statistics/{certificate_id}", response_model=LearningStatsResponse)
async def get_learning_statistics(
    certificate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get learning statistics for a certificate."""
    stats = db.query(LearningStatistics).filter(
        LearningStatistics.user_id == current_user.id,
        LearningStatistics.certificate_id == certificate_id
    ).first()
    
    if not stats:
        # Create initial statistics record
        stats = LearningStatistics(
            user_id=current_user.id,
            certificate_id=certificate_id
        )
        db.add(stats)
        db.commit()
        db.refresh(stats)
    
    return stats

def update_learning_statistics(db: Session, user_id: int, certificate_id: int, session: StudySession):
    """Update learning statistics after completing a study session."""
    stats = db.query(LearningStatistics).filter(
        LearningStatistics.user_id == user_id,
        LearningStatistics.certificate_id == certificate_id
    ).first()
    
    if not stats:
        stats = LearningStatistics(
            user_id=user_id,
            certificate_id=certificate_id
        )
        db.add(stats)
    
    # Update statistics
    stats.total_practice_sessions += 1
    stats.total_questions_answered += session.total_questions
    stats.total_correct_answers += session.correct_answers or 0
    
    if session.time_spent_minutes:
        stats.total_study_time_minutes += session.time_spent_minutes
    
    if session.score_percentage is not None:
        # Calculate average score
        all_sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.certificate_id == certificate_id,
            StudySession.completed == True,
            StudySession.score_percentage.isnot(None)
        ).all()
        
        if all_sessions:
            total_score = sum(s.score_percentage for s in all_sessions)
            stats.average_score = total_score / len(all_sessions)
            stats.best_score = max(s.score_percentage for s in all_sessions)
    
    stats.last_activity = datetime.utcnow()
    
    db.commit()