-- cert_fast AI 자격증 학습 플랫폼 데이터베이스 스키마
-- MariaDB/MySQL 버전

CREATE DATABASE IF NOT EXISTS cert_fast CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cert_fast;

-- 사용자 테이블 (일반 사용자, 강사, 관리자)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('student', 'instructor', 'admin') DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    phone VARCHAR(20),
    birth_date DATE,
    profile_image VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_active (is_active)
);

-- 자격증 발급 기관 테이블
CREATE TABLE certificate_issuers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_code (code),
    INDEX idx_active (is_active)
);

-- 자격증 카테고리 테이블
CREATE TABLE certificate_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_id INT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES certificate_categories(id),
    INDEX idx_code (code),
    INDEX idx_parent (parent_id),
    INDEX idx_active (is_active)
);

-- 자격증 테이블
CREATE TABLE certificates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    issuer_id INT NOT NULL,
    category_id INT NOT NULL,
    description TEXT,
    exam_duration INT, -- 시험 시간 (분)
    passing_score INT DEFAULT 60, -- 합격 점수
    total_questions INT, -- 총 문제 수
    difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (issuer_id) REFERENCES certificate_issuers(id),
    FOREIGN KEY (category_id) REFERENCES certificate_categories(id),
    INDEX idx_code (code),
    INDEX idx_issuer (issuer_id),
    INDEX idx_category (category_id),
    INDEX idx_active (is_active)
);

-- 강사-자격증 매핑 테이블 (강사가 담당하는 자격증)
CREATE TABLE instructor_certificates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    instructor_id INT NOT NULL,
    certificate_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instructor_id) REFERENCES users(id),
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    UNIQUE KEY unique_instructor_certificate (instructor_id, certificate_id),
    INDEX idx_instructor (instructor_id),
    INDEX idx_certificate (certificate_id)
);

-- 학습 자료 테이블
CREATE TABLE study_materials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    certificate_id INT NOT NULL,
    title VARCHAR(300) NOT NULL,
    content TEXT,
    material_type ENUM('theory', 'practice', 'summary', 'video', 'document') DEFAULT 'theory',
    chapter VARCHAR(100),
    section VARCHAR(100),
    difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
    tags JSON, -- 태그 배열
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_certificate (certificate_id),
    INDEX idx_type (material_type),
    INDEX idx_active (is_active),
    FULLTEXT idx_content (title, content)
);

-- 문제 테이블
CREATE TABLE questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    certificate_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'short_answer', 'essay') DEFAULT 'multiple_choice',
    correct_answer TEXT NOT NULL,
    options JSON, -- 선택지 배열 (객관식용)
    explanation TEXT, -- 문제 해설
    solution TEXT, -- 문제 풀이
    difficulty_level ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    chapter VARCHAR(100),
    section VARCHAR(100),
    tags JSON, -- 태그 배열
    source ENUM('past_exam', 'theory', 'ai_generated') DEFAULT 'theory',
    is_verified BOOLEAN DEFAULT FALSE, -- 검수 완료 여부
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT NOT NULL,
    verified_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    INDEX idx_certificate (certificate_id),
    INDEX idx_type (question_type),
    INDEX idx_source (source),
    INDEX idx_verified (is_verified),
    INDEX idx_active (is_active),
    FULLTEXT idx_question (question_text)
);

-- 학습 세션 테이블 (사용자의 학습 기록)
CREATE TABLE study_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    certificate_id INT NOT NULL,
    session_type ENUM('theory', 'past_exam', 'ai_custom') NOT NULL,
    study_mode ENUM('practice', 'exam') DEFAULT 'practice',
    total_questions INT NOT NULL,
    correct_answers INT DEFAULT 0,
    wrong_answers INT DEFAULT 0,
    score DECIMAL(5,2), -- 점수 (백분율)
    time_spent INT, -- 소요 시간 (초)
    time_limit INT, -- 제한 시간 (초)
    is_completed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    INDEX idx_user (user_id),
    INDEX idx_certificate (certificate_id),
    INDEX idx_type (session_type),
    INDEX idx_completed (is_completed)
);

-- 학습 세션 상세 테이블 (개별 문제 답안)
CREATE TABLE study_session_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    question_id INT NOT NULL,
    user_answer TEXT,
    is_correct BOOLEAN,
    time_spent INT, -- 문제당 소요 시간 (초)
    is_marked BOOLEAN DEFAULT FALSE, -- 중요 표시
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id),
    INDEX idx_session (session_id),
    INDEX idx_question (question_id),
    INDEX idx_marked (is_marked)
);

-- AI 에이전트 테이블
CREATE TABLE ai_agents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    agent_type ENUM('ocr_processor', 'content_analyzer', 'question_generator', 'study_material_creator', 'answer_generator', 'content_reviewer', 'learning_analyzer', 'recommendation_engine') NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_key_id VARCHAR(100),
    system_prompt TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    last_used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_type (agent_type),
    INDEX idx_active (is_active),
    INDEX idx_last_used (last_used_at)
);

-- AI API 키 테이블
CREATE TABLE ai_api_keys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    provider ENUM('openai', 'anthropic', 'google', 'cohere', 'huggingface') NOT NULL,
    api_key VARCHAR(500) NOT NULL, -- 암호화 저장
    is_active BOOLEAN DEFAULT TRUE,
    daily_limit BIGINT, -- 일일 토큰 제한
    monthly_limit BIGINT, -- 월간 토큰 제한
    tokens_used_today BIGINT DEFAULT 0,
    tokens_used_month BIGINT DEFAULT 0,
    reset_date DATE, -- 월간 리셋 날짜
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_provider (provider),
    INDEX idx_active (is_active)
);

-- AI 작업 로그 테이블
CREATE TABLE ai_processing_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    agent_id INT NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    input_data JSON,
    output_data JSON,
    tokens_used INT,
    processing_time INT, -- 처리 시간 (밀리초)
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    user_id INT,
    certificate_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    INDEX idx_agent (agent_id),
    INDEX idx_task_type (task_type),
    INDEX idx_status (status),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);

-- 파일 업로드 테이블
CREATE TABLE file_uploads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    mime_type VARCHAR(100),
    certificate_id INT,
    uploaded_by INT NOT NULL,
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    ocr_text TEXT,
    extracted_questions INT DEFAULT 0, -- 추출된 문제 수
    processing_log JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    INDEX idx_certificate (certificate_id),
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_status (processing_status),
    INDEX idx_created (created_at)
);

-- 문제/해설 신고 테이블
CREATE TABLE content_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_type ENUM('question', 'explanation', 'solution', 'study_material') NOT NULL,
    content_id INT NOT NULL,
    reporter_id INT NOT NULL,
    report_type ENUM('incorrect_answer', 'typo', 'unclear_explanation', 'inappropriate_content', 'other') NOT NULL,
    description TEXT NOT NULL,
    status ENUM('pending', 'in_review', 'resolved', 'rejected') DEFAULT 'pending',
    assigned_to INT, -- 담당 강사
    resolution_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    INDEX idx_content (content_type, content_id),
    INDEX idx_reporter (reporter_id),
    INDEX idx_status (status),
    INDEX idx_assigned (assigned_to)
);

-- 신고 응답/댓글 테이블
CREATE TABLE content_report_responses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_id INT NOT NULL,
    responder_id INT NOT NULL,
    response_text TEXT NOT NULL,
    is_resolution BOOLEAN DEFAULT FALSE, -- 최종 해결 답변 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (report_id) REFERENCES content_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (responder_id) REFERENCES users(id),
    INDEX idx_report (report_id),
    INDEX idx_responder (responder_id)
);

-- 사용자 학습 통계 테이블
CREATE TABLE learning_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    certificate_id INT NOT NULL,
    total_study_time INT DEFAULT 0, -- 총 학습 시간 (분)
    total_questions_solved INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    theory_sessions INT DEFAULT 0,
    exam_sessions INT DEFAULT 0,
    ai_custom_sessions INT DEFAULT 0,
    average_score DECIMAL(5,2),
    best_score DECIMAL(5,2),
    weak_categories JSON, -- 취약 분야
    strong_categories JSON, -- 강한 분야
    last_study_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    UNIQUE KEY unique_user_certificate (user_id, certificate_id),
    INDEX idx_user (user_id),
    INDEX idx_certificate (certificate_id),
    INDEX idx_last_study (last_study_date)
);

-- 시스템 설정 테이블
CREATE TABLE system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    data_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    is_encrypted BOOLEAN DEFAULT FALSE,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_key (setting_key)
);

-- 초기 데이터 삽입
INSERT INTO certificate_issuers (name, code, description, website) VALUES
('한국산업인력공단', 'HRD', '국가기술자격 및 직업능력개발 관련 자격증 발급', 'https://www.hrdkorea.or.kr'),
('한국데이터산업진흥원', 'KDATA', '데이터 분야 전문 자격증 발급', 'https://www.kdata.or.kr'),
('한국정보통신기술협회', 'TTA', 'ICT 분야 전문 자격증 발급', 'https://www.tta.or.kr');

INSERT INTO certificate_categories (name, code, description) VALUES
('정보기술', 'IT', 'IT 관련 자격증'),
('데이터분석', 'DATA', '데이터 분석 및 처리 관련 자격증'),
('네트워크', 'NETWORK', '네트워크 관련 자격증'),
('보안', 'SECURITY', '정보보안 관련 자격증');

INSERT INTO certificates (name, code, issuer_id, category_id, description, exam_duration, total_questions) VALUES
('정보처리기사', 'CRAFTSMAN_IT', 1, 1, '정보시스템의 개발과 운영에 필요한 실무능력 검정', 150, 100),
('빅데이터분석기사', 'CRAFTSMAN_BIGDATA', 2, 2, '빅데이터 이해 및 분석기획, 데이터 수집·저장·처리 등', 240, 120),
('정보보안기사', 'CRAFTSMAN_SECURITY', 1, 4, '정보보안 분야의 전문 기술인력 양성', 150, 100);

INSERT INTO ai_agents (name, agent_type, model_name, system_prompt) VALUES
('OCR 처리기', 'ocr_processor', 'gpt-4-vision', 'PDF 이미지에서 텍스트를 정확하게 추출합니다.'),
('내용 분석기', 'content_analyzer', 'gpt-4', '업로드된 학습 자료를 분석하여 적절한 카테고리로 분류합니다.'),
('문제 생성기', 'question_generator', 'gpt-4', '학습 내용을 바탕으로 적절한 난이도의 문제를 생성합니다.'),
('해설 생성기', 'answer_generator', 'gpt-4', '문제에 대한 정확하고 이해하기 쉬운 해설을 생성합니다.');

INSERT INTO system_settings (setting_key, setting_value, description, data_type) VALUES
('max_file_size', '10485760', '최대 파일 업로드 크기 (바이트)', 'integer'),
('allowed_file_types', '["pdf", "doc", "docx"]', '허용되는 파일 형식', 'json'),
('default_exam_time', '120', '기본 시험 시간 (분)', 'integer'),
('passing_score', '60', '기본 합격 점수', 'integer');

-- 초기 관리자 계정 (비밀번호는 애플리케이션에서 해시화하여 삽입)
-- INSERT INTO users (username, email, password_hash, full_name, role) VALUES
-- ('admin', 'admin@certfast.com', '$hashed_password', '시스템 관리자', 'admin');