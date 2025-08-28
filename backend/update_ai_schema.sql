-- AI 에이전트 테이블에 새로운 컬럼들 추가
ALTER TABLE ai_agents ADD COLUMN system_prompt TEXT;
ALTER TABLE ai_agents ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE ai_agents ADD COLUMN model_name VARCHAR(100);
ALTER TABLE ai_agents ADD COLUMN provider VARCHAR(50);
ALTER TABLE ai_agents ADD COLUMN max_tokens INTEGER DEFAULT 4000;
ALTER TABLE ai_agents ADD COLUMN temperature REAL DEFAULT 0.7;
ALTER TABLE ai_agents ADD COLUMN priority INTEGER DEFAULT 1;

-- creator_id를 nullable로 변경 (기존 제약 조건이 있으면 새 테이블 생성 후 데이터 이동)
-- SQLite는 ALTER COLUMN을 지원하지 않으므로 임시 테이블 사용

-- API 키 관리 테이블 생성
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider VARCHAR(50) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    daily_limit REAL,
    monthly_limit REAL,
    current_daily_usage REAL DEFAULT 0.0,
    current_monthly_usage REAL DEFAULT 0.0,
    last_reset_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- AI 사용량 로그 테이블 생성
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    api_key_id INTEGER NOT NULL,
    user_id INTEGER,
    task_type VARCHAR(100) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    duration_seconds REAL,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    request_data TEXT,
    response_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- AI 작업 테이블 생성
CREATE TABLE IF NOT EXISTS ai_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    agent_id INTEGER NOT NULL,
    user_id INTEGER,
    file_upload_id INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_data TEXT,
    output_data TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id)
);