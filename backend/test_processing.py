#!/usr/bin/env python3
"""
Test script to manually trigger PDF processing
"""
import asyncio
from services.pdf_processor import pdf_processor
from app.database import engine
from sqlalchemy import text

async def manual_process_pdf():
    """Manually process pending PDFs"""
    
    # Get pending uploads from database
    with engine.connect() as conn:
        pending_files = conn.execute(
            text("SELECT * FROM pdf_uploads WHERE processing_status = 'pending' ORDER BY id")
        ).fetchall()
        
        print(f"Found {len(pending_files)} pending files to process:")
        
        for file_record in pending_files:
            print(f"  - ID: {file_record.id}, Filename: {file_record.filename}, Type: {file_record.file_type}")
            
            # Manually trigger processing
            await pdf_processor.add_to_queue(
                upload_id=file_record.id,
                file_path=file_record.file_path,
                file_type=file_record.file_type,
                certificate_id=file_record.certificate_id
            )
            
            print(f"  Added to processing queue: {file_record.id}")

if __name__ == "__main__":
    print("Starting manual PDF processing...")
    asyncio.run(manual_process_pdf())
    print("Manual processing trigger completed.")