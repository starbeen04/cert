# CertFast Backend

FastAPI backend for the CertFast certificate study platform.

## Features

- **User Management**: Registration, authentication, and role-based access control
- **Certificate Management**: Create and manage certification courses
- **AI Agents**: Intelligent tutoring and question generation
- **PDF Processing**: OCR text extraction from uploaded documents
- **Study Materials**: Manage learning content and questions
- **Study Sessions**: Track learning progress and statistics

## Quick Start

### Prerequisites

- Python 3.8+
- MariaDB/MySQL database
- Redis (optional, for background tasks)

### Installation

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database and other configurations
```

5. Initialize the database:
```bash
# Create database migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

6. Run the application:
```bash
python run.py
# or
uvicorn main:app --host 0.0.0.0 --port 8100 --reload
```

The API will be available at:
- Main API: http://localhost:8100
- Interactive docs: http://localhost:8100/docs
- ReDoc: http://localhost:8100/redoc

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Users
- `GET /api/users/` - List users (admin only)
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update current user profile

### Certificates
- `GET /api/certificates/` - List certificates
- `POST /api/certificates/` - Create certificate (instructor/admin)
- `GET /api/certificates/{id}` - Get certificate details
- `PUT /api/certificates/{id}` - Update certificate
- `DELETE /api/certificates/{id}` - Delete certificate

### AI Agents
- `GET /api/ai-agents/` - List AI agents
- `POST /api/ai-agents/` - Create AI agent (instructor/admin)
- `POST /api/ai-agents/{id}/chat` - Start chat session
- `POST /api/ai-agents/sessions/{id}/messages` - Send message

### PDF Processing
- `POST /api/pdf/upload` - Upload PDF file
- `POST /api/pdf/{id}/process` - Process file with OCR
- `GET /api/pdf/{id}/text` - Get extracted text

### Study Materials
- `GET /api/study/materials` - List study materials
- `POST /api/study/materials` - Create study material
- `GET /api/study/questions` - List questions
- `POST /api/study/questions` - Create question
- `POST /api/study/sessions` - Start study session

## Database Schema

The backend uses SQLAlchemy ORM with the following main models:

- **User**: User accounts with role-based access
- **Certificate**: Certification courses
- **Question**: Quiz questions for certificates
- **StudyMaterial**: Learning resources
- **AIAgent**: AI tutoring agents
- **ChatSession**: AI chat conversations
- **StudySession**: Learning progress tracking
- **FileUpload**: Uploaded file management

## Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/certfast

# JWT Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# OCR
TESSERACT_PATH=/usr/bin/tesseract

# AI Integration
OPENAI_API_KEY=your-openai-key
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Production Deployment

1. Set environment variables for production
2. Use a production WSGI server (gunicorn)
3. Set up proper database connection pooling
4. Configure Redis for background tasks
5. Set up file storage (AWS S3, etc.)
6. Enable HTTPS and proper CORS settings

## Security

- JWT token-based authentication
- Role-based access control (Student, Instructor, Admin)
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy ORM
- File upload size and type restrictions
- CORS configuration for frontend integration

## API Documentation

Visit `/docs` for interactive Swagger documentation or `/redoc` for ReDoc documentation when the server is running.