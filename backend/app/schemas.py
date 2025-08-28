from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models import UserRole, CertificateStatus, QuestionType, AgentStatus

# Base schemas
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# User schemas
class UserBase(BaseSchema):
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.STUDENT
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

class UserLogin(BaseSchema):
    username: str  # Can be username or email
    password: str

# Token schemas
class Token(BaseSchema):
    access_token: str
    token_type: str

class TokenData(BaseSchema):
    username: Optional[str] = None

# Certificate schemas
class CertificateBase(BaseSchema):
    title: str
    description: Optional[str] = None
    issuer: str
    category: str
    difficulty_level: str
    exam_duration_minutes: Optional[int] = None
    passing_score: Optional[float] = None
    tags: Optional[List[str]] = None

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    issuer: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    status: Optional[CertificateStatus] = None
    exam_duration_minutes: Optional[int] = None
    passing_score: Optional[float] = None
    tags: Optional[List[str]] = None

class CertificateResponse(CertificateBase):
    id: int
    status: CertificateStatus
    total_questions: int
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime]

# Question schemas
class QuestionBase(BaseSchema):
    question_text: str
    question_type: QuestionType
    options: Optional[Dict[str, Any]] = None
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str
    points: int = 1
    tags: Optional[List[str]] = None

class QuestionCreate(QuestionBase):
    certificate_id: int

class QuestionUpdate(BaseSchema):
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[Dict[str, Any]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    points: Optional[int] = None
    tags: Optional[List[str]] = None

class QuestionResponse(QuestionBase):
    id: int
    certificate_id: int
    created_at: datetime
    updated_at: Optional[datetime]

# Study Material schemas
class StudyMaterialBase(BaseSchema):
    title: str
    content: str
    material_type: str

class StudyMaterialCreate(StudyMaterialBase):
    certificate_id: int

class StudyMaterialUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    material_type: Optional[str] = None

class StudyMaterialResponse(StudyMaterialBase):
    id: int
    certificate_id: int
    file_path: Optional[str]
    file_size: Optional[int]
    page_count: Optional[int]
    upload_status: str
    created_at: datetime
    updated_at: Optional[datetime]

# AI Agent schemas
class AIAgentBase(BaseSchema):
    name: str
    description: Optional[str] = None
    agent_type: str
    agent_config: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None

class AIAgentCreate(AIAgentBase):
    pass

class AIAgentUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    status: Optional[AgentStatus] = None

class AIAgentResponse(AIAgentBase):
    id: int
    status: AgentStatus
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime]

# Chat schemas
class ChatSessionCreate(BaseSchema):
    ai_agent_id: int
    session_name: Optional[str] = None

class ChatSessionResponse(BaseSchema):
    id: int
    user_id: int
    ai_agent_id: int
    session_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class ChatMessageCreate(BaseSchema):
    content: str

class ChatMessageResponse(BaseSchema):
    id: int
    session_id: int
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

# Study Session schemas
class StudySessionCreate(BaseSchema):
    certificate_id: int
    session_type: str
    total_questions: int

class StudySessionUpdate(BaseSchema):
    answers: Optional[Dict[str, Any]] = None
    completed: Optional[bool] = None
    time_spent_minutes: Optional[int] = None

class StudySessionResponse(BaseSchema):
    id: int
    user_id: int
    certificate_id: int
    session_type: str
    total_questions: int
    correct_answers: int
    score_percentage: Optional[float]
    time_spent_minutes: Optional[int]
    completed: bool
    passed: Optional[bool]
    started_at: datetime
    completed_at: Optional[datetime]

# File Upload schemas
class FileUploadResponse(BaseSchema):
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_status: str
    created_at: datetime

# Statistics schemas
class LearningStatsResponse(BaseSchema):
    user_id: int
    certificate_id: int
    total_study_time_minutes: int
    total_practice_sessions: int
    total_questions_answered: int
    total_correct_answers: int
    average_score: Optional[float]
    best_score: Optional[float]
    streak_days: int
    last_activity: Optional[datetime]

# Pagination schemas
class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# AI 관련 schemas
class APIKeyCreate(BaseSchema):
    provider: str  # openai, anthropic, google
    key_name: str
    api_key: str
    is_active: bool = True
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None

class APIKeyUpdate(BaseSchema):
    key_name: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None

class APIKeyResponse(BaseSchema):
    id: int
    provider: str
    key_name: str
    is_active: bool
    daily_limit: Optional[float]
    monthly_limit: Optional[float]
    current_daily_usage: float
    current_monthly_usage: float
    last_reset_date: Optional[date]
    created_at: datetime
    updated_at: Optional[datetime]

class AIAgentCreate(BaseSchema):
    name: str
    description: Optional[str] = None
    agent_type: str
    model_name: Optional[str] = None
    provider: Optional[str] = None
    is_active: bool = True
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    agent_config: Optional[dict] = None
    priority: int = 1

class AIAgentUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    model_name: Optional[str] = None
    provider: Optional[str] = None
    is_active: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None
    agent_config: Optional[dict] = None
    priority: Optional[int] = None

class AIAgentResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str]
    agent_type: str
    model_name: Optional[str]
    provider: Optional[str]
    is_active: bool
    max_tokens: int
    temperature: float
    system_prompt: Optional[str]
    agent_config: Optional[dict]
    priority: int
    created_at: datetime
    updated_at: Optional[datetime]

class AIUsageLogResponse(BaseSchema):
    id: int
    agent_id: int
    api_key_id: int
    user_id: Optional[int]
    task_type: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    duration_seconds: Optional[float]
    status: str
    error_message: Optional[str]
    created_at: datetime

class AITaskCreate(BaseSchema):
    task_type: str
    agent_id: Optional[int] = None
    user_id: Optional[int] = None
    file_upload_id: Optional[int] = None
    input_data: Optional[dict] = None

class AITaskResponse(BaseSchema):
    id: int
    task_type: str
    agent_id: Optional[int]
    user_id: Optional[int]
    file_upload_id: Optional[int]
    status: str
    progress: int
    input_data: Optional[dict]
    output_data: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]