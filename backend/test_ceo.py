"""
Test CEO Agent and Business Analyst Agent Integration
Interactive Mode - User provides real input for requirements
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from agents.ceo_agent import CEOAgent
from agents.business_analyst import BusinessAnalystAgent

load_dotenv()


async def test_business_analyst_interactive():
    """Test Business Analyst Agent with real user input"""
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        print("❌ ERROR: GROQ_API_KEY not in .env")
        return
    
    print("\n" + "="*70)
    print("📊 BUSINESS ANALYST AGENT - INTERACTIVE TEST")
    print("="*70)
    
    llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_key)
    ba = BusinessAnalystAgent(llm=llm)
    
    # Get client goal from user
    print("\nEnter your project goal (or press Enter for demo project):")
    client_goal = input("Project Goal: ").strip()
    
    if not client_goal:
        client_goal = "Build a social networking platform for professionals"
        print(f"\nUsing demo: {client_goal}")
    
    try:
        # BA asks questions and collects answers
        client_answers = await ba.ask_questions_interactively(client_goal)
        
        if not client_answers:
            print("❌ No answers provided")
            return
        
        # Process answers
        print("\n⚙️  Processing your answers...")
        summary = await ba.process_client_answers(client_answers)
        print(f"✅ Summary created:")
        print(f"   Objective: {summary.client_goal[:80]}...")
        print(f"   Platform: {summary.platform_type}")
        print(f"   Target Users: {summary.target_users[:60]}...")
        
        # Extract functional requirements
        print("\n📋 Extracting functional requirements...")
        func_reqs = await ba.extract_functional_requirements()
        print(f"✅ Found {len(func_reqs.core_features)} core features:")
        for i, feature in enumerate(func_reqs.core_features[:5], 1):
            print(f"   {i}. {feature[:60]}")
        
        # Extract non-functional requirements
        print("\n⚙️  Extracting non-functional requirements...")
        nonfunc_reqs = await ba.extract_nonfunctional_requirements()
        print(f"✅ Non-functional requirements:")
        print(f"   Users: {nonfunc_reqs.expected_users}")
        print(f"   Traffic: {nonfunc_reqs.expected_traffic}")
        print(f"   Response Time: {nonfunc_reqs.response_time}")
        print(f"   Security: {nonfunc_reqs.security_level}")
        
        # Analyze risks
        print("\n⚠️  Analyzing risks...")
        risks = await ba.analyze_risks()
        print(f"✅ Risk analysis:")
        print(f"   High Risks: {len(risks.high_risks)}")
        print(f"   Medium Risks: {len(risks.medium_risks)}")
        print(f"   Critical Blockers: {len(risks.critical_blockers)}")
        
        print("\n" + "="*70)
        print("✅ BUSINESS ANALYST INTERACTIVE TEST COMPLETE!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_ceo_with_ba_integration():
    """Test CEO Agent with Business Analyst integration - Interactive"""
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        print("❌ ERROR: GROQ_API_KEY not in .env")
        return
    
    print("\n" + "="*70)
    print("🧠 CEO + BUSINESS ANALYST INTEGRATION - INTERACTIVE TEST")
    print("="*70)
    
    llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_key)
    ceo = CEOAgent(llm)
    
    try:
        # CEO uses BA interactively (no pre-defined answers)
        print("\n🔗 CEO delegating to Business Analyst for deep analysis...\n")
        
        requirements_doc = await ceo.gather_business_requirements()
        
        if not requirements_doc:
            print("❌ No requirements gathered")
            return
        
        print(f"\n✅ Business requirements gathered!")
        print(f"   Summary: {list(requirements_doc['summary'].keys())}")
        print(f"   Functional: {list(requirements_doc['functional_requirements'].keys())}")
        print(f"   Non-Functional: {list(requirements_doc['nonfunctional_requirements'].keys())}")
        print(f"   Risks: {list(requirements_doc['risk_analysis'].keys())}\n")
        
        # Now CEO creates roadmap based on real requirements
        print("🗺️  CEO creating roadmap based on business analysis...")
        
        analysis = {
            "main_objective": requirements_doc['summary'].get('client_goal', 'Project'),
            "key_requirements": requirements_doc['functional_requirements'].get('core_features', []),
            "constraints": requirements_doc['summary'].get('constraints', {}),
            "suggested_tech_stack": ["TBD based on requirements"]
        }
        
        roadmap = await ceo.create_roadmap(analysis)
        print(f"\n✅ Roadmap created:")
        print(f"   Objective: {roadmap.objective[:80]}...")
        print(f"   Tasks: {len(roadmap.tasks)}\n")
        
        for i, task in enumerate(roadmap.tasks[:7], 1):
            print(f"   [{i}] {task.description}")
            print(f"       Priority: {task.priority}/5\n")
        
        # Track progress
        progress = ceo.track_progress()
        print(f"📈 Progress:")
        print(f"   Total Tasks: {progress['total_tasks']}")
        print(f"   Completion: {progress['completion_percentage']:.1f}%\n")
        
        print("="*70)
        print("✅ CEO + BA INTEGRATION TEST COMPLETE!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_ceo_basic():
    """Test basic CEO Agent functionality"""
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        print("❌ ERROR: GROQ_API_KEY not in .env")
        return
    
    print("\n" + "="*70)
    print("🧠 CEO AGENT BASIC TEST")
    print("="*70 + "\n")
    
    llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_key)
    ceo = CEOAgent(llm)
    
    prompt = "Build a Python calculator with a secret vault feature"
    
    print(f"📥 Testing with prompt: {prompt}\n")
    
    try:
        # Test understand_prompt
        print("🔍 CEO analyzing prompt...")
        analysis = await ceo.understand_prompt(prompt)
        print(f"✅ Analysis complete")
        print(f"   Objective: {analysis.get('main_objective', 'N/A')[:60]}...")
        print(f"   Complexity: {analysis.get('estimated_complexity', 'N/A')}\n")
        
        # Test create_roadmap
        print("🗺️  CEO creating roadmap...")
        roadmap = await ceo.create_roadmap(analysis)
        print(f"✅ Roadmap created:")
        print(f"   Objective: {roadmap.objective[:60]}...")
        print(f"   Tasks: {len(roadmap.tasks)}\n")
        
        for task in roadmap.tasks[:5]:
            print(f"   [{task.id}] {task.description} (Priority: {task.priority})")
        
        print("\n" + "="*70)
        print("✅ CEO BASIC TEST COMPLETE!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run tests"""
    print("\n🚀 DEVSWARM AGENT TESTING SUITE\n")
    
    # Show menu
    print("="*70)
    print("CHOOSE A TEST:")
    print("1. Business Analyst Agent (Interactive Q&A)")
    print("2. CEO + BA Integration (Interactive)")
    print("3. CEO Basic Test (Demo)")
    print("4. Run All Tests")
    print("="*70 + "\n")
    
    choice = input("Enter choice (1-4) or press Enter for all: ").strip()
    
    if choice == "1":
        await test_business_analyst_interactive()
    elif choice == "2":
        await test_ceo_with_ba_integration()
    elif choice == "3":
        await test_ceo_basic()
    elif choice == "4" or choice == "":
        print("\nRunning all tests...\n")
        await test_business_analyst_interactive()
        print("\n" + "="*70 + "\n")
        await test_ceo_with_ba_integration()
        print("\n" + "="*70 + "\n")
        await test_ceo_basic()
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())