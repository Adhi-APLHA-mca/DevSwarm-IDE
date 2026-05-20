"""
Main entry point for DevSwarm Agent System
Demonstrates autonomous agent workflow with Groq LLM
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from workflows.orchestrator import DevSwarmOrchestrator
from memory.memory_system import AgentMemory
from tools.toolkit import Toolkit

# Load environment variables
load_dotenv()


async def main():
    """Main orchestrator demonstration"""
    
    print(f"\n{'='*70}")
    print(f"🚀 DevSwarm - Autonomous AI Agent System")
    print(f"{'='*70}\n")
    
    # Initialize Groq LLM
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        print("❌ ERROR: GROQ_API_KEY not set in environment")
        print("   Set it in .env file or environment variables")
        return
    
    print("✓ Using Groq API as LLM backend")
    print(f"  API Key: {groq_api_key[:10]}...")
    
    llm = ChatGroq(
        model="gpt-4o-mini",
        temperature=0.7,
        groq_api_key=groq_api_key
    )
    
    # Initialize orchestrator
    orchestrator = DevSwarmOrchestrator(llm, codebase_path=".")
    
    # Example client prompts to test
    test_prompts = [
        """
Create a Python CLI tool that:
1. Reads CSV files
2. Performs data analysis (mean, median, mode)
3. Generates charts
4. Exports results as JSON

Requirements:
- Use pandas and matplotlib
- Add unit tests
- Document with docstrings
- Handle errors gracefully
        """,
        
        """
Build a REST API for a TODO application:
1. CRUD operations for todos
2. User authentication with JWT
3. Database (SQLite or PostgreSQL)
4. Comprehensive error handling
5. Unit tests with >80% coverage

Use FastAPI and async/await
        """,
    ]
    
    # Run demonstration
    print("\n" + "="*70)
    print("📋 AVAILABLE TEST PROMPTS:")
    print("="*70)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{i}. {prompt.strip()[:50]}...")
    
    # For autonomous testing, use first prompt
    print("\n" + "="*70)
    print("🤖 AUTONOMOUS MODE - Running first test prompt")
    print("="*70)
    
    selected_prompt = test_prompts[0]
    
    print(f"\nClient Request:\n{selected_prompt}\n")
    
    # Run orchestrator
    result = await orchestrator.run(selected_prompt)
    
    # Print results
    print("\n" + "="*70)
    print("📊 EXECUTION RESULTS")
    print("="*70)
    
    print(f"\nFinal Status: {result['status']}")
    print(f"Analysis: {result['analysis']}")
    
    if result['roadmap']:
        print(f"\nRoadmap Objective: {result['roadmap'].objective}")
        print(f"Total Tasks: {len(result['roadmap'].tasks)}")
        
        print("\nTasks:")
        for task in result['roadmap'].tasks:
            print(f"  - {task.id}: {task.description}")
            print(f"    Status: {task.status}")
            if task.result:
                print(f"    Result: {task.result[:50]}...")
    
    if result['errors']:
        print(f"\nErrors: {result['errors']}")
    
    if result['progress_history']:
        final_progress = result['progress_history'][-1]
        print(f"\nFinal Progress: {final_progress['completion_percentage']:.1f}%")
    
    print("\n" + "="*70)
    print("✅ Orchestrator run completed")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
