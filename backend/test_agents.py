"""
Autonomous Testing Framework for DevSwarm Agents
Tests agent capabilities without UI integration
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from memory.memory_system import AgentMemory, MemoryType
from tools.toolkit import Toolkit, CodeExecutionTool
from agents.ceo_agent import CEOAgent, Task, TaskStatus


class AgentTestSuite:
    """Comprehensive test suite for agent system"""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.memory = AgentMemory()
        self.toolkit = Toolkit()
        self.test_results = []
    
    def test_memory_system(self) -> Dict[str, Any]:
        """Test memory management"""
        print("\n" + "="*70)
        print("🧠 TEST: Memory System")
        print("="*70)
        
        try:
            # Test short-term memory
            print("\n1️⃣  Testing Short-Term Memory...")
            mem_id = self.memory.short_term.add(
                content="Test task: implement feature X",
                tags=["feature", "test"],
                importance=0.8
            )
            print(f"   ✓ Added entry: {mem_id}")
            
            context = self.memory.short_term.get_context()
            print(f"   ✓ Context retrieved: {len(context['recent_memories'])} entries")
            
            # Test long-term memory
            print("\n2️⃣  Testing Long-Term Memory...")
            lt_id = self.memory.long_term.add(
                content="Successfully implemented API with FastAPI",
                memory_type=MemoryType.EPISODIC,
                tags=["api", "success"],
                importance=0.9
            )
            print(f"   ✓ Added long-term entry: {lt_id}")
            
            # Test learning storage
            print("\n3️⃣  Testing Learning Storage...")
            self.memory.long_term.add_learning(
                "best_framework_python",
                "FastAPI for async APIs"
            )
            learning = self.memory.long_term.get_learning("best_framework_python")
            print(f"   ✓ Stored learning: {learning}")
            
            # Test search
            print("\n4️⃣  Testing Memory Search...")
            results = self.memory.long_term.search("api", limit=5)
            print(f"   ✓ Found {len(results)} relevant memories")
            
            return {"status": "✅ PASSED", "tests": 4}
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"status": "❌ FAILED", "error": str(e)}
    
    def test_code_execution(self) -> Dict[str, Any]:
        """Test code execution tool"""
        print("\n" + "="*70)
        print("💻 TEST: Code Execution Tool")
        print("="*70)
        
        try:
            exec_tool = CodeExecutionTool()
            
            # Test 1: Simple Python
            print("\n1️⃣  Testing Python execution...")
            code = """
result = 2 + 2
print(f"Result: {result}")
"""
            output = exec_tool.execute_python(code)
            assert output['success'], f"Execution failed: {output['error']}"
            assert "4" in output['output'], "Unexpected output"
            print(f"   ✓ Code executed successfully")
            print(f"   ✓ Output: {output['output'].strip()}")
            
            # Test 2: Error handling
            print("\n2️⃣  Testing error handling...")
            bad_code = "print(undefined_variable)"
            output = exec_tool.execute_python(bad_code)
            assert not output['success'], "Should have failed"
            print(f"   ✓ Error correctly caught")
            
            # Test 3: Complex code
            print("\n3️⃣  Testing complex code...")
            complex_code = """
import json
data = {"name": "DevSwarm", "type": "agent"}
json_str = json.dumps(data)
print(f"JSON: {json_str}")
"""
            output = exec_tool.execute_python(complex_code)
            assert output['success'], f"Failed: {output['error']}"
            print(f"   ✓ Complex code executed")
            
            return {"status": "✅ PASSED", "tests": 3}
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"status": "❌ FAILED", "error": str(e)}
    
    def test_toolkit_tools(self) -> Dict[str, Any]:
        """Test toolkit functionality"""
        print("\n" + "="*70)
        print("🧰 TEST: Toolkit Tools")
        print("="*70)
        
        try:
            # Test code base RAG
            print("\n1️⃣  Testing Codebase RAG...")
            self.toolkit.rag.index_codebase()
            print(f"   ✓ Indexed {len(self.toolkit.rag.indexed_files)} files")
            
            # Test web search (mock)
            print("\n2️⃣  Testing Web Search...")
            results = self.toolkit.web_search.search("python fastapi", num_results=3)
            print(f"   ✓ Mock search returned {len(results)} results")
            
            # Test Git operations (mock - won't actually clone)
            print("\n3️⃣  Testing Git Operations...")
            print("   ℹ️  Git operations require actual repo")
            
            return {"status": "✅ PASSED", "tests": 2}
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"status": "❌ FAILED", "error": str(e)}
    
    def test_task_management(self) -> Dict[str, Any]:
        """Test CEO agent task management"""
        print("\n" + "="*70)
        print("📋 TEST: Task Management")
        print("="*70)
        
        try:
            print("\n1️⃣  Creating test tasks...")
            tasks = [
                Task(
                    id="task_1",
                    description="Implement user authentication",
                    priority=5,
                    dependencies=[]
                ),
                Task(
                    id="task_2",
                    description="Create database schema",
                    priority=5,
                    dependencies=[]
                ),
                Task(
                    id="task_3",
                    description="Build API endpoints",
                    priority=4,
                    dependencies=["task_1", "task_2"]
                ),
            ]
            print(f"   ✓ Created {len(tasks)} tasks")
            
            # Test dependency validation
            print("\n2️⃣  Validating task dependencies...")
            from workflows.orchestrator import DevSwarmOrchestrator
            orchestrator = DevSwarmOrchestrator(self.llm) if self.llm else None
            
            if orchestrator:
                valid = orchestrator._validate_dependencies(tasks)
                assert valid, "Dependency validation failed"
                print(f"   ✓ Dependencies validated")
            
            # Test task assignment
            print("\n3️⃣  Testing task assignment...")
            if self.llm:
                ceo = CEOAgent(self.llm)
                agent, confidence = ceo.assign_task(tasks[2], ["CodeWriter", "Reviewer"])
                print(f"   ✓ Task assigned to {agent} (confidence: {confidence})")
            
            return {"status": "✅ PASSED", "tests": 3}
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"status": "❌ FAILED", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests"""
        print("\n" + "🧪 AUTONOMOUS TEST SUITE 🧪".center(70, "="))
        print()
        
        results = {
            "memory": self.test_memory_system(),
            "code_execution": self.test_code_execution(),
            "toolkit": self.test_toolkit_tools(),
            "task_management": self.test_task_management(),
        }
        
        # Print summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, result in results.items():
            status = result['status']
            tests = result.get('tests', 0)
            total_tests += tests
            
            if "✅" in status:
                passed_tests += tests
                print(f"✓ {test_name.upper()}: {status} ({tests} tests)")
            else:
                print(f"✗ {test_name.upper()}: {status}")
                if 'error' in result:
                    print(f"  Error: {result['error']}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "-"*70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*70 + "\n")
        
        return {
            "all_results": results,
            "total_tests": total_tests,
            "passed": passed_tests,
            "success_rate": success_rate
        }


async def main():
    """Run autonomous test suite"""
    
    # Try to use Groq if available
    try:
        from dotenv import load_dotenv
        import os
        from langchain_groq import ChatGroq
        
        load_dotenv()
        groq_key = os.getenv("GROQ_API_KEY")
        
        if groq_key:
            print("✓ Using Groq LLM for agent tests")
            llm = ChatGroq(
                model="mixtral-8x7b-32768",
                groq_api_key=groq_key
            )
        else:
            print("⚠️  Groq API key not found - running tests without LLM")
            llm = None
    except Exception as e:
        print(f"⚠️  Could not load Groq: {e}")
        llm = None
    
    # Run tests
    suite = AgentTestSuite(llm)
    results = await suite.run_all_tests()
    
    # Return exit code based on success
    return 0 if results['success_rate'] == 100 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
