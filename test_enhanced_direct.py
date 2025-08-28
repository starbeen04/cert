#!/usr/bin/env python3
"""
Direct test of the enhanced PDF processor
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.enhanced_pdf_processor import enhanced_pdf_processor
from backend.database import get_db, engine
from sqlalchemy.orm import sessionmaker

def main():
    print("🧪 Enhanced PDF Processor Direct Test")
    print("=" * 50)
    
    # Create database session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test file path - use the one that was processed before
        test_file = "backend/uploads/pdfs/20250819_230927_9d999864_2. 2024년2회_정보처리산업기사필기 기출문제.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return
        
        print(f"📄 Testing file: {os.path.basename(test_file)}")
        print(f"📏 File size: {os.path.getsize(test_file)} bytes")
        
        async def run_test():
            print("\n🔄 Starting enhanced processing...")
            
            result = await enhanced_pdf_processor.process_pdf_with_enhanced_pipeline(
                upload_id=26,  # Using the existing upload ID
                file_path=test_file,
                file_type="questions",
                db=db
            )
            
            print("\n📊 Processing Results:")
            print("-" * 30)
            
            if result.get("success"):
                print("✅ Processing succeeded!")
                print(f"📋 Questions extracted: {result.get('extracted_count', 0)}")
                print(f"💰 Cost: ${result.get('cost', 0)}")
                print(f"⏱️ Processing time: {result.get('processing_time', 'unknown')}")
                
                if result.get('questions'):
                    print(f"\n📝 Sample questions:")
                    for i, q in enumerate(result['questions'][:3]):  # Show first 3
                        print(f"  {i+1}. {q.get('question_text', 'N/A')[:100]}...")
                
            else:
                print("❌ Processing failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            return result
        
        # Run the async test
        result = asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    main()