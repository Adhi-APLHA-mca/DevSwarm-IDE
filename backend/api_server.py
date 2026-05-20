"""
FastAPI Backend Server for DevSwarm IDE
Exposes Business Analyst Agent as REST API endpoints
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from agents.business_analyst import BusinessAnalystAgent
from memory.memory_system import AgentMemory

# Load environment variables from backend directory
root_dir = Path(__file__).parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastAPI app
app = FastAPI(
    title="DevSwarm IDE Backend",
    description="Backend API for DevSwarm IDE with Business Analyst Agent",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM and Memory
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

memory = AgentMemory()
ba_agent = BusinessAnalystAgent(llm=llm, memory=memory)

# Pydantic models for request/response
class ClientGoalRequest(BaseModel):
    goal: str
    context: Optional[str] = None

class AnswersRequest(BaseModel):
    answers: Dict[str, str]

class InitiateBARequest(BaseModel):
    client_goal: str
    context: Optional[str] = None

class SubmitAnswersRequest(BaseModel):
    answers: Dict[str, str]

class AnswerRequest(BaseModel):
    question_index: int
    answer: str

# Global state for conversation
current_session = {
    "client_goal": None,
    "questions": [],
    "answers": {},
    "requirements": None,
    "ba_agent": ba_agent
}

# ===================== API ENDPOINTS =====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "DevSwarm IDE Backend Running"}

@app.post("/ba/initiate")
async def initiate_ba(request: InitiateBARequest):
    """
    Initiate Business Analyst conversation
    Returns list of clarifying questions
    """
    try:
        current_session["client_goal"] = request.client_goal
        current_session["answers"] = {}
        
        # Generate questions
        questions = await ba_agent.gather_requirements(
            client_goal=request.client_goal,
            additional_context=request.context
        )
        
        current_session["questions"] = questions
        
        return {
            "status": "success",
            "client_goal": request.client_goal,
            "questions": questions,
            "total_questions": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ba/answer")
async def submit_answer(request: AnswerRequest):
    """
    Submit answer to a specific question
    Returns next question or completion status
    """
    try:
        if not current_session["questions"]:
            raise HTTPException(status_code=400, detail="No active BA session")
        
        # Store answer
        if 0 <= request.question_index < len(current_session["questions"]):
            question = current_session["questions"][request.question_index]
            current_session["answers"][question] = request.answer
        else:
            raise HTTPException(status_code=400, detail="Invalid question index")
        
        # Check if all questions answered
        total = len(current_session["questions"])
        answered = len(current_session["answers"])
        
        response = {
            "status": "success",
            "question_index": request.question_index,
            "answered": answered,
            "total": total,
            "is_complete": answered >= total
        }
        
        # If all answered, process requirements
        if answered >= total:
            response["message"] = "All questions answered. Processing requirements..."
        else:
            response["next_question_index"] = request.question_index + 1
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ba/process")
async def process_requirements():
    """
    Process all answers and generate requirements
    Returns comprehensive requirements document
    """
    try:
        if len(current_session["answers"]) == 0:
            raise HTTPException(status_code=400, detail="No answers provided")
        
        # Process answers through BA agent
        requirements = await ba_agent.process_client_answers(current_session["answers"])
        functional = await ba_agent.extract_functional_requirements()
        nonfunctional = await ba_agent.extract_nonfunctional_requirements()
        risks = await ba_agent.analyze_risks()
        
        # Store in session
        current_session["requirements"] = {
            "summary": requirements.__dict__ if hasattr(requirements, '__dict__') else requirements,
            "functional": functional.__dict__ if hasattr(functional, '__dict__') else functional,
            "nonfunctional": nonfunctional.__dict__ if hasattr(nonfunctional, '__dict__') else nonfunctional,
            "risks": risks.__dict__ if hasattr(risks, '__dict__') else risks
        }
        
        return {
            "status": "success",
            "message": "Requirements processed successfully",
            "requirements": current_session["requirements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ba/status")
async def get_status():
    """Get current BA session status"""
    return {
        "has_active_session": bool(current_session["client_goal"]),
        "client_goal": current_session["client_goal"],
        "questions_count": len(current_session["questions"]),
        "answers_count": len(current_session["answers"]),
        "is_complete": len(current_session["answers"]) >= len(current_session["questions"])
    }

@app.get("/ba/questions")
async def get_questions():
    """Get all questions for current session"""
    return {
        "questions": current_session["questions"],
        "total": len(current_session["questions"])
    }

@app.post("/ba/reset")
async def reset_session():
    """Reset BA session"""
    current_session["client_goal"] = None
    current_session["questions"] = []
    current_session["answers"] = {}
    current_session["requirements"] = None
    return {"status": "success", "message": "Session reset"}

@app.get("/ba/requirements")
async def get_requirements():
    """Get processed requirements"""
    if not current_session["requirements"]:
        raise HTTPException(status_code=404, detail="No processed requirements yet")
    return {
        "status": "success",
        "message": "Requirements retrieved successfully",
        "requirements": current_session["requirements"]
    }

# ===================== HEALTH & DEBUG =====================

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "DevSwarm IDE Backend",
        "ba_agent_ready": ba_agent is not None,
        "memory_ready": memory is not None
    }

@app.get("/debug/session")
async def debug_session():
    """Debug endpoint - get current session state"""
    return {
        "client_goal": current_session["client_goal"],
        "questions_count": len(current_session["questions"]),
        "answers": current_session["answers"],
        "has_requirements": bool(current_session["requirements"])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
