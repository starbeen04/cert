"""
Utility functions for the CertFast backend
"""

import os
import uuid
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import re

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    name = Path(original_filename).stem
    extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}_{unique_id}{extension}"

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """Validate if file extension is allowed."""
    extension = Path(filename).suffix.lower()
    return extension in allowed_extensions

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove dangerous characters."""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name = Path(filename).stem[:200]
        extension = Path(filename).suffix
        filename = f"{name}{extension}"
    
    return filename

def extract_text_from_pdf_placeholder(file_path: str) -> str:
    """
    Placeholder function for PDF text extraction.
    In production, integrate with actual OCR libraries like:
    - pytesseract + pdf2image
    - PyPDF2 for text-based PDFs
    - pdfplumber
    - External APIs (Google Vision, AWS Textract)
    """
    return f"Extracted text from {file_path} - Implement actual OCR here"

def generate_questions_from_text_placeholder(text: str, num_questions: int = 10) -> List[Dict[str, Any]]:
    """
    Placeholder function for AI-based question generation.
    In production, integrate with AI services like:
    - OpenAI GPT
    - Google PaLM
    - Custom ML models
    """
    questions = []
    for i in range(num_questions):
        questions.append({
            "question_text": f"Sample question {i+1} generated from text",
            "question_type": "multiple_choice",
            "options": {
                "A": "Option A",
                "B": "Option B", 
                "C": "Option C",
                "D": "Option D"
            },
            "correct_answer": "A",
            "explanation": "This is a placeholder explanation",
            "difficulty": "medium"
        })
    
    return questions

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return feedback."""
    feedback = {
        "is_valid": True,
        "score": 0,
        "issues": []
    }
    
    if len(password) < 8:
        feedback["issues"].append("Password must be at least 8 characters long")
        feedback["is_valid"] = False
    else:
        feedback["score"] += 1
    
    if not re.search(r'[A-Z]', password):
        feedback["issues"].append("Password must contain at least one uppercase letter")
        feedback["is_valid"] = False
    else:
        feedback["score"] += 1
    
    if not re.search(r'[a-z]', password):
        feedback["issues"].append("Password must contain at least one lowercase letter")
        feedback["is_valid"] = False
    else:
        feedback["score"] += 1
    
    if not re.search(r'\d', password):
        feedback["issues"].append("Password must contain at least one number")
        feedback["is_valid"] = False
    else:
        feedback["score"] += 1
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        feedback["issues"].append("Password must contain at least one special character")
        feedback["score"] += 0.5
    else:
        feedback["score"] += 1
    
    return feedback

def paginate_query(query, page: int, size: int):
    """Apply pagination to a SQLAlchemy query."""
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    pages = (total + size - 1) // size
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

def calculate_study_streak(study_sessions) -> int:
    """Calculate current study streak in days."""
    if not study_sessions:
        return 0
    
    # Sort sessions by date (most recent first)
    sorted_sessions = sorted(study_sessions, key=lambda x: x.started_at, reverse=True)
    
    streak = 0
    current_date = datetime.now().date()
    
    for session in sorted_sessions:
        session_date = session.started_at.date()
        
        if session_date == current_date or session_date == current_date - timedelta(days=streak):
            if session_date == current_date - timedelta(days=streak):
                streak += 1
            current_date = session_date
        else:
            break
    
    return streak

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable format."""
    if minutes < 60:
        return f"{minutes} minutes"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    
    return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

def get_difficulty_color(difficulty: str) -> str:
    """Get color code for difficulty level."""
    colors = {
        "easy": "#4CAF50",      # Green
        "medium": "#FF9800",    # Orange
        "hard": "#F44336",      # Red
        "expert": "#9C27B0"     # Purple
    }
    return colors.get(difficulty.lower(), "#757575")  # Default gray

def calculate_score_percentage(correct_answers: int, total_questions: int) -> float:
    """Calculate score percentage."""
    if total_questions == 0:
        return 0.0
    return round((correct_answers / total_questions) * 100, 2)

def get_grade_from_percentage(percentage: float) -> str:
    """Get letter grade from percentage."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"

def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix