# cert_fast - AI 자격증 학습 플랫폼

Vue.js + FastAPI + MariaDB를 활용한 AI 기반 자격증 학습 플랫폼입니다.

## 🚀 프로젝트 구조

```
cert_fast/
├── backend/                 # FastAPI 백엔드 (포트 8100)
│   ├── app/
│   │   ├── routers/        # API 라우터
│   │   ├── models.py       # 데이터베이스 모델
│   │   ├── schemas.py      # Pydantic 스키마
│   │   └── ...
│   ├── main.py             # FastAPI 애플리케이션
│   └── requirements.txt    # Python 의존성
├── frontend/               # Vue.js 프론트엔드 (포트 3100)
│   ├── src/
│   │   ├── views/          # 페이지 컴포넌트
│   │   ├── components/     # 재사용 컴포넌트
│   │   ├── stores/         # Pinia 스토어
│   │   └── ...
│   ├── package.json        # Node.js 의존성
│   └── vite.config.ts      # Vite 설정
├── database_schema.sql     # 데이터베이스 스키마
├── setup.bat              # 초기 설정 스크립트
├── start_servers.bat      # 서버 시작 스크립트
└── stop_servers.bat       # 서버 종료 스크립트
```

## 🛠️ 설치 및 실행

### 1. 초기 설정

```bash
# 의존성 설치 및 환경 설정
setup.bat
```

### 2. 데이터베이스 설정

1. MariaDB/MySQL 서버 설치 및 실행
2. 데이터베이스 생성:
   ```sql
   mysql -u root -p < database_schema.sql
   ```
3. `backend/.env` 파일 수정:
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost/cert_fast
   SECRET_KEY=your-secret-key-here
   ```

### 3. 서버 실행

```bash
# 백엔드와 프론트엔드 서버 동시 시작
start_servers.bat
```

또는 개별 실행:
```bash
# 백엔드만 실행 (포트 8100)
cd backend
python run.py

# 프론트엔드만 실행 (포트 3100)
cd frontend
npm run dev
```

### 4. 서버 종료

```bash
stop_servers.bat
```

## 🌐 접속 URL

- **프론트엔드**: http://localhost:3100
- **백엔드 API**: http://localhost:8100
- **API 문서**: http://localhost:8100/docs
- **ReDoc**: http://localhost:8100/redoc

## 👥 사용자 유형

### 1. 일반 사용자 (학습자)
- **이론 학습**: 자격증별 이론 공부 및 문제 풀이
- **기출 문제**: 실제 시험 문제 풀이 (시간 제한)
- **AI 맞춤형 문제**: 개인화된 AI 생성 문제

### 2. 강사 사용자
- **학습자 통계**: 담당 자격증 학습자들의 성과 분석
- **콘텐츠 검수**: AI 생성 문제/해설 검토 및 수정
- **Q&A 관리**: 신고된 문제 처리

### 3. 관리자
- **사용자 관리**: 전체 사용자 관리
- **자격증 관리**: 자격증 발급기관, 유형, 문제 관리
- **AI 관리**: AI 에이전트 설정 및 모니터링
- **PDF 처리**: 문서 업로드 및 OCR 처리

## 🤖 AI 에이전트 시스템

### 주요 AI 에이전트
1. **OCR 처리기**: PDF 이미지화 및 텍스트 추출
2. **콘텐츠 분석기**: 문서 분석 및 데이터베이스 분류
3. **문제 생성기**: 학습 내용 기반 문제 생성
4. **해설 생성기**: 문제 해설 및 풀이 생성
5. **학습 분석기**: 사용자별 학습 데이터 분석
6. **추천 엔진**: 개인화된 학습 가이드라인 제공

## 🗄️ 데이터베이스 구조

### 주요 테이블
- `users`: 사용자 정보 (학습자, 강사, 관리자)
- `certificates`: 자격증 정보
- `questions`: 문제 및 해설
- `study_materials`: 학습 자료
- `ai_agents`: AI 에이전트 설정
- `learning_statistics`: 학습 통계
- `file_uploads`: PDF 업로드 관리

## 🔧 개발 환경

### 백엔드 (FastAPI)
- **Python**: 3.9+
- **FastAPI**: 최신 버전
- **SQLAlchemy**: ORM
- **Alembic**: 데이터베이스 마이그레이션
- **JWT**: 인증 시스템

### 프론트엔드 (Vue.js)
- **Vue 3**: Composition API
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Element Plus**: UI 컴포넌트
- **Pinia**: 상태 관리

### 데이터베이스
- **MariaDB/MySQL**: 메인 데이터베이스
- **UTF8MB4**: 문자셋 지원

## 📊 기능 목록

### 관리자 기능
- [x] 사용자 관리 (생성, 수정, 삭제, 활성화/비활성화)
- [x] 자격증 관리 (발급기관, 카테고리, 자격증 CRUD)
- [x] AI 에이전트 관리 (모델, 프롬프트, 사용량 모니터링)
- [x] PDF 업로드 및 OCR 처리
- [x] 시스템 모니터링 및 로그 관리

### 학습 기능
- [ ] 이론 학습 시스템
- [ ] 기출 문제 시험 모드
- [ ] AI 맞춤형 문제 추천
- [ ] 학습 진도 및 통계

### AI 기능
- [ ] 자동 문제 생성
- [ ] 해설 및 풀이 생성
- [ ] 학습 패턴 분석
- [ ] 개인화 추천

## 🔐 보안

- JWT 기반 인증
- 역할 기반 접근 제어 (RBAC)
- 파일 업로드 검증
- SQL 인젝션 방지
- XSS 방지

## 📝 라이센스

이 프로젝트는 개인 학습 목적으로 제작되었습니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해 주세요.

## 📞 지원

문제가 발생하면 다음을 확인해 주세요:
1. 모든 의존성이 올바르게 설치되었는지
2. 데이터베이스 연결 설정이 정확한지
3. 포트 8100, 3100이 사용 가능한지"# cert" 
