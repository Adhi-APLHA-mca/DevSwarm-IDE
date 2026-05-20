"""
CEO / Orchestrator Agent
The brain of DevSwarm - manages workflows, assigns tasks, tracks progress
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel, Field

from memory.memory_system import AgentMemory, MemoryType
from tools.toolkit import Toolkit
from agents.business_analyst import BusinessAnalystAgent


class TaskStatus(str, Enum):
    """Task status in workflow"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task(BaseModel):
    """Task definition"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    priority: int = 1  # 1-5, 5 being highest


class Roadmap(BaseModel):
    """Project roadmap"""
    client_prompt: str
    objective: str
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    current_phase: str = "planning"


class CEOAgent:
    """
    CEO/Orchestrator Agent
    
    Responsibilities:
    - Understand client prompt
    - Create roadmap
    - Divide tasks
    - Assign agents
    - Track progress
    - Resolve conflicts
    """
    
    def __init__(self, llm: Any, toolkit: Toolkit = None):
        self.llm = llm
        self.toolkit = toolkit or Toolkit()
        self.memory = AgentMemory()
        self.roadmap: Optional[Roadmap] = None
        self.message_history: List[BaseMessage] = []
        self.agents: Dict[str, Any] = {}  # Registry of available agents
        
        # Initialize specialized agents
        self.business_analyst = BusinessAnalystAgent(llm=llm, memory=self.memory)
        
        # System prompt for CEO
        self.system_prompt = SystemMessage(content="""
You are the CEO/Orchestrator Agent of DevSwarm - an autonomous AI development system.

Your responsibilities:
1. **Understanding**: Analyze client prompts to understand project goals
2. **Planning**: Create detailed roadmaps with clear objectives and phases
3. **Task Division**: Break down work into concrete, actionable tasks
4. **Assignment**: Match tasks to appropriate specialized agents
5. **Tracking**: Monitor progress and handle blockers
6. **Coordination**: Manage dependencies between tasks
7. **Conflict Resolution**: Handle conflicting decisions and prioritize work

You have access to:
- Project memory (short-term context + long-term learnings)
- Team of specialized agents (Code Writer, Reviewer, Debugger, etc.)
- Tools (code execution, git, web search, codebase RAG)

Decision-making principles:
- Break complex problems into manageable subtasks
- Consider dependencies carefully
- Prioritize based on criticality and risk
- Flag human decisions needed
- Learn from past projects
""")
    
    async def understand_prompt(self, client_prompt: str) -> Dict[str, Any]:
        """
        Analyze client prompt and extract requirements
        """
        if not self.message_history:
            self.message_history.append(self.system_prompt)
        
        self.message_history.append(HumanMessage(content=f"""
Analyze this client request and extract:
1. Main objective
2. Key requirements
3. Potential challenges
4. Suggested tech stack
5. Estimated complexity (1-5)

Client Request:
{client_prompt}

Provide structured analysis in JSON format.
"""))
        
        response = await self.llm.ainvoke(self.message_history)
        
        self.message_history.append(response)
        
        # Store in memory
        self.memory.short_term.add(
            content=f"Analyzed prompt: {client_prompt[:100]}...",
            tags=["analysis", "prompt"],
            importance=0.9
        )
        
        self.memory.long_term.add(
            content=f"Analyzed prompt: {client_prompt[:100]}",
            tags=["analysis", "prompt"],
            importance=0.9,
            agent="CEO"
        )
        
        return self._parse_json_response(response.content)
    
    async def create_roadmap(self, analysis: Dict[str, Any]) -> Roadmap:
        """
        Create detailed project roadmap
        """
        # Extract objective from analysis
        objective = analysis.get("main_objective") or analysis.get("objective") or "Development Project"
        
        self.message_history.append(HumanMessage(content=f"""
Based on this analysis, create a detailed project roadmap with 5-7 concrete tasks.

Analysis: {json.dumps(analysis, indent=2)}

Create roadmap in JSON format with this exact structure:
{{
    "tasks": [
        {{"description": "Task 1 description", "priority": 5, "dependencies": []}},
        {{"description": "Task 2 description", "priority": 5, "dependencies": []}},
        ...
    ]
}}

Each task must have: description, priority (1-5), and dependencies list.
"""))
        
        response = await self.llm.ainvoke(self.message_history)
        
        self.message_history.append(response)
        
        # Parse and create Roadmap
        roadmap_data = self._parse_json_response(response.content)
        
        tasks_list = roadmap_data.get("tasks", [])
        if not tasks_list:
            # Fallback: generate tasks from analysis
            tasks_list = [
                {"description": "Setup project structure and environment", "priority": 5, "dependencies": []},
                {"description": "Implement core functionality", "priority": 5, "dependencies": ["Setup"]},
                {"description": "Add error handling and validation", "priority": 4, "dependencies": ["Implement"]},
                {"description": "Write unit tests", "priority": 4, "dependencies": ["Implement"]},
                {"description": "Documentation and examples", "priority": 3, "dependencies": ["Tests"]},
            ]
        
        self.roadmap = Roadmap(
            client_prompt="",
            objective=objective,
            tasks=[
                Task(
                    id=f"task_{i}",
                    description=task.get("description", f"Task {i+1}"),
                    priority=task.get("priority", 1),
                    dependencies=task.get("dependencies", [])
                )
                for i, task in enumerate(tasks_list)
            ]
        )
        
        # Store in memory
        self.memory.long_term.add(
            content=f"Created roadmap for: {self.roadmap.objective}",
            tags=["roadmap", "planning"],
            importance=0.95,
            agent="CEO"
        )
        
        return self.roadmap
    
    def assign_task(self, task: Task, available_agents: List[str]) -> Tuple[str, float]:
        """
        Assign task to most suitable agent
        Returns: (agent_name, confidence_score)
        """
        # Simple assignment logic - can be enhanced with LLM
        task_keywords = task.description.lower()
        
        # Routing logic
        if any(word in task_keywords for word in ["write", "code", "implement", "feature"]):
            agent = "CodeWriter"
        elif any(word in task_keywords for word in ["review", "test", "check", "quality"]):
            agent = "CodeReviewer"
        elif any(word in task_keywords for word in ["debug", "fix", "error", "issue"]):
            agent = "Debugger"
        elif any(word in task_keywords for word in ["document", "explain", "comment"]):
            agent = "Documentor"
        else:
            agent = available_agents[0] if available_agents else "GeneralAgent"
        
        task.assigned_agent = agent
        return agent, 0.85
    
    def track_progress(self) -> Dict[str, Any]:
        """Track overall project progress"""
        if not self.roadmap:
            return {"status": "no_roadmap"}
        
        total_tasks = len(self.roadmap.tasks)
        completed = sum(1 for t in self.roadmap.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.roadmap.tasks if t.status == TaskStatus.IN_PROGRESS)
        failed = sum(1 for t in self.roadmap.tasks if t.status == TaskStatus.FAILED)
        
        progress = {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total_tasks - completed - in_progress - failed,
            "failed": failed,
            "completion_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            "tasks_by_status": {
                "pending": [t.id for t in self.roadmap.tasks if t.status == TaskStatus.PENDING],
                "in_progress": [t.id for t in self.roadmap.tasks if t.status == TaskStatus.IN_PROGRESS],
                "completed": [t.id for t in self.roadmap.tasks if t.status == TaskStatus.COMPLETED],
                "failed": [t.id for t in self.roadmap.tasks if t.status == TaskStatus.FAILED],
            }
        }
        
        return progress
    
    async def resolve_conflict(self, conflict_description: str) -> str:
        """Handle conflicts and blockers"""
        self.message_history.append(HumanMessage(content=f"""
We have a conflict/blocker in the project:
{conflict_description}

Current progress: {self.track_progress()}

Suggest resolution with:
1. Root cause
2. Recommended solution
3. Alternative approaches
4. Risk assessment
"""))
        
        response = await self.llm.ainvoke(self.message_history)
        
        self.message_history.append(response)
        
        return response.content
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register available agent"""
        self.agents[agent_name] = agent_instance
    
    def get_context_for_llm(self) -> Dict[str, Any]:
        """Prepare context for LLM calls"""
        return {
            "roadmap": self.roadmap.dict() if self.roadmap else None,
            "progress": self.track_progress(),
            "memory": self.memory.get_full_context(),
            "available_agents": list(self.agents.keys()),
            "message_history_length": len(self.message_history)
        }
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        import json
        import re
        
        try:
            # Try to find JSON in response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                print(f"No JSON found in response: {response_text[:100]}")
                return {}
            
            # Clean up common issues
            json_str = json_str.replace('\n', ' ')
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Attempted to parse: {response_text[:200]}")
            return {}
    
    async def gather_business_requirements(
        self, 
        client_goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Business Analyst Agent to deeply understand requirements
        Interactive mode - asks user questions and processes answers
        
        Args:
            client_goal: Optional pre-defined goal. If None, prompts user for input
        
        Returns:
            Complete requirements document (summary, functional, non-functional, risks)
        """
        # Get client goal from user if not provided
        if not client_goal:
            print("\n" + "="*70)
            print("🎯 TELL ME YOUR PROJECT GOAL")
            print("="*70 + "\n")
            client_goal = input("What do you want to build? ").strip()
            if not client_goal:
                print("❌ No goal provided. Aborting.")
                return {}
        
        # Step 1: BA asks questions interactively and collects user answers
        print("\n🔄 Starting Business Analysis...\n")
        client_answers = await self.business_analyst.ask_questions_interactively(client_goal)
        
        if not client_answers:
            print("\n❌ No answers provided. Cannot proceed.")
            return {}
        
        # Step 2: Process answers into structured requirements
        print("\n⚙️  Processing your answers...")
        summary = await self.business_analyst.process_client_answers(client_answers)
        
        # Step 3: Extract all requirement types
        print("\n📋 Extracting functional requirements...")
        functional_reqs = await self.business_analyst.extract_functional_requirements()
        
        print("\n⚙️  Extracting non-functional requirements...")
        nonfunctional_reqs = await self.business_analyst.extract_nonfunctional_requirements()
        
        print("\n⚠️  Analyzing risks...")
        risk_analysis = await self.business_analyst.analyze_risks()
        
        # Step 4: Generate complete doc
        print("\n📄 Generating complete requirements document...\n")
        complete_doc = await self.business_analyst.generate_complete_requirements_doc()
        
        # Store in memory
        self.memory.long_term.add(
            content=f"Business requirements gathered: {len(functional_reqs.core_features)} core features",
            tags=["business_analysis", "requirements", "complete"],
            importance=0.95,
            agent="CEO",
            project=client_goal[:30]
        )
        
        return complete_doc
