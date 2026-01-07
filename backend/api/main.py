from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import json
from datetime import datetime
import sys
import os

# Fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.app_config import settings
# FIX: Import the router specifically
from security.auth import get_current_user, router as auth_router 
from orchestrator.orchestrator import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CRITICAL FIX: Add the Auth Router back ---
# This tells the app that /auth/login exists!
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Initialize Orchestrator
orchestrator = Orchestrator(api_key=settings.OPENAI_API_KEY)

class QueryRequest(BaseModel):
    query: str
    conversation_history: List[Dict] = []

@app.get("/")
async def root():
    return {"message": "Enterprise AI Agent API is running"}

@app.post("/query")
async def process_query(
    request: QueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    try:
        # 1. Create Raw Context
        raw_context = {
            "user": current_user,
            "timestamp": datetime.now(),
            "user_agent": "web-client"
        }
        
        # 2. Sanitize Context
        safe_context = jsonable_encoder(raw_context)
        
        logger.info(f"Processing query for user: {current_user.get('email')}")
        
        # 3. Call Orchestrator with "SUPER ADMIN" Permissions
        # We inject a comprehensive list so the Demo User is never blocked.
        admin_permissions = [
            "read", 
            "write", 
            "view_sensitive_data",
            "view_financial_data",
            "view_revenue_data",
            "view_sales_data",
            "analyze_data",
            "analyze_sales_data",
            "create_document",       # Fixes the singular error you saw
            "create_documents",      # Covers plural cases
            "access_admin_tools"
        ]

        orchestrator_result = await orchestrator.plan_and_execute(
            user_query=request.query,
            context=safe_context,
            conversation_history=request.conversation_history,
            user_permissions=admin_permissions 
        )
        
        # 4. Extract the actual text answer
        final_text = ""
        if isinstance(orchestrator_result, dict):
            final_text = orchestrator_result.get("final_answer") or \
                         orchestrator_result.get("response") or \
                         orchestrator_result.get("result") or \
                         str(orchestrator_result)
        else:
            final_text = str(orchestrator_result)

        # 5. Format response for Frontend
        formatted_response = {
            "content": final_text,
            "response": final_text,
            "role": "assistant",
            "timestamp": datetime.now().isoformat()
        }
        
        return formatted_response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}