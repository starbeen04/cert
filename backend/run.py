#!/usr/bin/env python3
"""
CertFast Backend Startup Script
"""

import uvicorn
import os
from app.config import settings

if __name__ == "__main__":
    # Ensure uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,  # Set to False in production
        log_level="info"
    )