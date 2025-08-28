from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, Enum, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class UserRole(enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

class CertificateStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    ESSAY = "essay"

class AgentStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    certificates_created = relationship("Certificate", back_populates="creator", foreign_keys="Certificate.creator_id")
    study_sessions = relationship("StudySession", back_populates="user")
    ai_agents = relationship("AIAgent", back_populates="creator")

class Certificate(Base):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    issuer = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    status = Column(Enum(CertificateStatus), default=CertificateStatus.DRAFT, nullable=False)
    exam_duration_minutes = Column(Integer, nullable=True)
    passing_score = Column(Float, nullable=True)
    total_questions = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)  # Store as JSON array
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="certificates_created", foreign_keys=[creator_id])
    questions = relationship("Question", back_populates="certificate")
    study_materials = relationship("StudyMaterial", back_populates="certificate")
    study_sessions = relationship("StudySession", back_populates="certificate")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=False)  # easy, medium, hard
    points = Column(Integer, default=1)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    certificate = relationship("Certificate", back_populates="questions")

class StudyMaterial(Base):
    __tablename__ = "study_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    pdf_upload_id = Column(Integer, ForeignKey("pdf_uploads.id"), nullable=True)  # 새 PDF 업로드와 연결
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)  # 챕터와 연결
    
    # 기본 자료 정보
    material_id = Column(String(50), nullable=True)  # M001, M002 등
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    material_type = Column(String(50), nullable=False)  # pdf, text, video, link, 개념설명, 공식, 정리, 예제, 요약, 도표, 그래프
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)  # For PDF files
    upload_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_content = Column(Text, nullable=True)  # OCR extracted content
    
    # Claude 고급 분류 필드들 
    importance_level = Column(String(20), nullable=True)  # 핵심/중요/참고
    related_questions = Column(Text, nullable=True)  # JSON 형태의 연관 문제 ID들
    prerequisites = Column(Text, nullable=True)  # JSON 형태의 선수학습요소들
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    certificate = relationship("Certificate", back_populates="study_materials")

class AIAgent(Base):
    __tablename__ = "ai_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    agent_type = Column(String(100), nullable=False)  # tutor, quiz_master, study_planner, document_analysis, etc.
    agent_config = Column(JSON, nullable=True)  # Store AI model configuration
    prompt_template = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)  # 시스템 프롬프트 추가
    status = Column(Enum(AgentStatus), default=AgentStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True)  # 활성화 상태 추가
    model_name = Column(String(100), nullable=True)  # AI 모델명 추가 (gpt-4, claude-3.5 등)
    provider = Column(String(50), nullable=True)  # AI 제공사 (openai, anthropic 등)
    max_tokens = Column(Integer, default=4000)  # 최대 토큰 수
    temperature = Column(Float, default=0.7)  # 온도 설정
    priority = Column(Integer, default=1)  # 처리 우선순위
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable로 변경 (시스템 에이전트용)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="ai_agents")
    chat_sessions = relationship("ChatSession", back_populates="ai_agent")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ai_agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)
    session_name = Column(String(255), nullable=True)
    context = Column(JSON, nullable=True)  # Store conversation context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ai_agent = relationship("AIAgent", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Store additional message data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=False)
    session_type = Column(String(50), nullable=False)  # practice, exam, review
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, nullable=True)
    time_spent_minutes = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    passed = Column(Boolean, nullable=True)
    answers = Column(JSON, nullable=True)  # Store user answers
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="study_sessions")
    certificate = relationship("Certificate", back_populates="study_sessions")

class LearningStatistics(Base):
    __tablename__ = "learning_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=False)
    total_study_time_minutes = Column(Integer, default=0)
    total_practice_sessions = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)
    best_score = Column(Float, nullable=True)
    streak_days = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    upload_status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    ocr_text = Column(Text, nullable=True)
    file_metadata = Column(JSON, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# AI 에이전트 관련 추가 모델들 (AIAgent는 이미 위에 정의됨)

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)  # openai, anthropic, google
    key_name = Column(String(100), nullable=False)  # 사용자 정의 키 이름
    api_key = Column(String(500), nullable=False)  # 암호화된 API 키
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Float, nullable=True)  # 일일 사용 한도 ($)
    monthly_limit = Column(Float, nullable=True)  # 월간 사용 한도 ($)
    current_daily_usage = Column(Float, default=0.0)
    current_monthly_usage = Column(Float, default=0.0)
    last_reset_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    task_type = Column(String(100), nullable=False)  # pdf_analysis, question_generation, etc.
    model_used = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)  # USD
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(50), default="success")  # success, error, timeout
    error_message = Column(Text, nullable=True)
    request_data = Column(JSON, nullable=True)  # 요청 데이터 (개인정보 제외)
    response_data = Column(JSON, nullable=True)  # 응답 데이터 요약
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AITask(Base):
    __tablename__ = "ai_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100), nullable=False)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_upload_id = Column(Integer, nullable=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100%
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PdfUpload(Base):
    __tablename__ = "pdf_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)  # original_filename 대신 original_name
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    file_type = Column(String(50), nullable=True)  # questions, study_material, etc.
    processing_status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    ai_agent = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CertificateInfo(Base):
    __tablename__ = "certificates_info"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    issuing_organization = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    difficulty_level = Column(String(50), nullable=True)
    exam_duration_minutes = Column(Integer, nullable=True)
    passing_score = Column(Float, nullable=True)
    requirements = Column(Text, nullable=True)
    exam_info = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExtractedQuestion(Base):
    __tablename__ = "extracted_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_upload_id = Column(Integer, ForeignKey("pdf_uploads.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    
    # 기본 문제 정보
    question_id = Column(String(50), nullable=True)  # Q001, Q002 등
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    correct_answer = Column(Text, nullable=True)
    options = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    
    # 추가 문제 상세 정보
    passage = Column(Text, nullable=True)  # 지문, 보기, 표, 그래프 등 문제 관련 추가 정보
    additional_info = Column(Text, nullable=True)  # 부가적인 설명이나 참고사항
    
    # Claude 고급 분류 필드들
    bloom_taxonomy = Column(String(50), nullable=True)  # 지식/이해/적용/분석/종합/평가
    topic_tags = Column(Text, nullable=True)  # JSON 형태의 세부주제 태그들
    keywords = Column(Text, nullable=True)  # JSON 형태의 핵심 키워드들
    estimated_time = Column(String(20), nullable=True)  # 풀이 예상 소요시간
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 새로운 PDF 전처리 시스템 모델들
class DocumentAnalysis(Base):
    """문서 분석 결과 - GPT Vision으로 분석한 문서 구조와 메타데이터"""
    __tablename__ = "document_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_upload_id = Column(Integer, ForeignKey("pdf_uploads.id"), nullable=False)
    
    # 문서 기본 정보
    total_pages = Column(Integer, nullable=False)
    document_type = Column(String(100), nullable=True)  # 기출문제, 해설집, 요약서 등
    has_text_layer = Column(Boolean, default=False)  # PDF에 텍스트 레이어 존재 여부
    is_scanned = Column(Boolean, default=False)  # 스캔본 여부
    
    # GPT 분석 결과
    layout_analysis = Column(JSON, nullable=True)  # 레이아웃 분석 결과
    content_structure = Column(JSON, nullable=True)  # 문제/해설/정답표 구조
    document_metadata = Column(JSON, nullable=True)  # 과목, 연도, 회차 등
    
    # OpenAI API 사용 정보
    api_key_used = Column(String(100), nullable=True)
    total_tokens_used = Column(Integer, default=0)
    analysis_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PageAnalysis(Base):
    """페이지별 분석 결과"""
    __tablename__ = "page_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    document_analysis_id = Column(Integer, ForeignKey("document_analysis.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    
    # 페이지 기본 정보
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    dpi = Column(Integer, nullable=True)
    
    # GPT 분석 결과
    page_type = Column(String(50), nullable=True)  # 문제페이지, 해설페이지, 정답표 등
    layout_info = Column(JSON, nullable=True)  # 레이아웃 정보 (단일/이단/다단 등)
    question_regions = Column(JSON, nullable=True)  # 문제 영역들의 bbox
    content_regions = Column(JSON, nullable=True)  # 기타 콘텐츠 영역들
    
    # 전처리 레시피
    preprocessing_recipe = Column(JSON, nullable=True)  # GPT가 생성한 전처리 계획
    
    # 썸네일 정보
    thumbnail_path = Column(String(500), nullable=True)  # 저해상도 썸네일 경로
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PreprocessingResult(Base):
    """전처리 실행 결과"""
    __tablename__ = "preprocessing_results"
    
    id = Column(Integer, primary_key=True, index=True)
    page_analysis_id = Column(Integer, ForeignKey("page_analysis.id"), nullable=False)
    
    # 전처리 결과
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_image_path = Column(String(500), nullable=True)  # 전처리된 전체 페이지 이미지
    
    # 영역별 크롭 결과
    cropped_regions = Column(JSON, nullable=True)  # 크롭된 영역들의 정보와 파일 경로
    
    # 전처리 세부 정보
    operations_performed = Column(JSON, nullable=True)  # 수행된 전처리 작업들
    quality_metrics = Column(JSON, nullable=True)  # 이미지 품질 지표들
    
    # 처리 시간
    processing_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class OcrResult(Base):
    """OCR 처리 결과"""
    __tablename__ = "ocr_results"
    
    id = Column(Integer, primary_key=True, index=True)
    preprocessing_result_id = Column(Integer, ForeignKey("preprocessing_results.id"), nullable=False)
    region_type = Column(String(50), nullable=False)  # question, answer, explanation, figure_caption 등
    region_bbox = Column(JSON, nullable=True)  # 해당 영역의 bbox 정보
    
    # OCR 결과
    raw_text = Column(Text, nullable=True)  # 원본 OCR 텍스트
    confidence_score = Column(Float, nullable=True)  # OCR 신뢰도
    
    # 구조화된 결과
    structured_content = Column(JSON, nullable=True)  # 구조화된 콘텐츠 (문제번호, 선택지 등)
    
    # OCR 엔진 정보
    ocr_engine = Column(String(50), nullable=True)  # tesseract, paddleocr 등
    ocr_config = Column(JSON, nullable=True)  # OCR 설정 정보
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcessingStep(Base):
    """처리 단계별 상태 기록"""
    __tablename__ = "processing_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_upload_id = Column(Integer, ForeignKey("pdf_uploads.id"), nullable=False)
    step_name = Column(String(100), nullable=False)  # document_analysis, page_analysis, preprocessing, ocr, postprocessing
    step_order = Column(Integer, nullable=False)  # 처리 순서
    
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, skipped
    progress_percent = Column(Integer, default=0)  # 0-100
    
    # 단계별 결과 정보
    result_data = Column(JSON, nullable=True)  # 단계별 처리 결과
    error_message = Column(Text, nullable=True)
    
    # 시간 정보
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 고급 교육 콘텐츠 분류 모델들 (Claude 기반)

class Chapter(Base):
    """챕터/단원 정보"""
    __tablename__ = "chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_upload_id = Column(Integer, ForeignKey("pdf_uploads.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    main_topics = Column(JSON, nullable=True)  # 주요 개념 목록
    learning_objectives = Column(JSON, nullable=True)  # 학습목표 목록
    page_range = Column(String(50), nullable=True)  # 페이지 범위
    created_at = Column(DateTime(timezone=True), server_default=func.now())