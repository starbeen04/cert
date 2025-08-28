import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FileUpload, User
from app.schemas import FileUploadResponse
from app.auth import get_current_active_user
from app.config import settings
import uuid
from pathlib import Path

router = APIRouter()

# OCR processing function (placeholder - would integrate with actual OCR service)
async def process_pdf_with_ocr(file_path: str) -> str:
    """
    Process PDF file with OCR to extract text.
    This is a placeholder function - in production, you would integrate with:
    - Tesseract OCR
    - Google Cloud Vision API
    - AWS Textract
    - Azure Computer Vision
    """
    # For now, return a placeholder text
    return f"OCR extracted text from {file_path} - This is a placeholder. Integrate with actual OCR service."

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    name = Path(original_filename).stem
    extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{name}_{unique_id}{extension}"

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_file(
    file: UploadFile = File(...),
    title: str = Form(None),
    description: str = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF file for OCR processing."""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('application/pdf'):
        if get_file_extension(file.filename) not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )
    
    # Validate file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = upload_dir / unique_filename
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create file upload record
        db_file = FileUpload(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            content_type=file.content_type or "application/pdf",
            upload_status="uploaded",
            uploaded_by=current_user.id,
            metadata={
                "title": title,
                "description": description
            }
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

@router.post("/{file_id}/process", response_model=FileUploadResponse)
async def process_uploaded_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process uploaded file with OCR."""
    
    # Get file record
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file_record.upload_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is already being processed"
        )
    
    if file_record.upload_status == "completed":
        return file_record
    
    try:
        # Update status to processing
        file_record.upload_status = "processing"
        db.commit()
        
        # Process file with OCR
        ocr_text = await process_pdf_with_ocr(file_record.file_path)
        
        # Update record with OCR results
        file_record.ocr_text = ocr_text
        file_record.upload_status = "completed"
        db.commit()
        db.refresh(file_record)
        
        return file_record
        
    except Exception as e:
        # Update status to failed
        file_record.upload_status = "failed"
        if file_record.metadata:
            file_record.metadata["error"] = str(e)
        else:
            file_record.metadata = {"error": str(e)}
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(e)}"
        )

@router.get("/uploads", response_model=List[FileUploadResponse])
async def get_my_uploads(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all uploads for current user."""
    files = db.query(FileUpload).filter(
        FileUpload.uploaded_by == current_user.id
    ).order_by(FileUpload.created_at.desc()).all()
    
    return files

@router.get("/{file_id}", response_model=FileUploadResponse)
async def get_upload_details(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get upload details by ID."""
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return file_record

@router.get("/{file_id}/text")
async def get_extracted_text(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get extracted OCR text from file."""
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file_record.upload_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has not been processed yet"
        )
    
    return {
        "file_id": file_id,
        "filename": file_record.original_filename,
        "extracted_text": file_record.ocr_text,
        "processed_at": file_record.updated_at
    }

@router.delete("/{file_id}")
async def delete_uploaded_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete uploaded file."""
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete physical file
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        db.delete(file_record)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.post("/{file_id}/generate-questions")
async def generate_questions_from_file(
    file_id: int,
    num_questions: int = Form(10),
    difficulty: str = Form("medium"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate questions from processed file content."""
    file_record = db.query(FileUpload).filter(
        FileUpload.id == file_id,
        FileUpload.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file_record.upload_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has not been processed yet"
        )
    
    # TODO: Integrate with AI service to generate questions from OCR text
    # For now, return a placeholder response
    return {
        "message": "Question generation requested",
        "file_id": file_id,
        "num_questions": num_questions,
        "difficulty": difficulty,
        "status": "Processing - questions will be generated from the extracted text"
    }