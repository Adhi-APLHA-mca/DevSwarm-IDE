"""
Main Orchestrator Workflow using LangGraph
Manages stateful execution of agent tasks
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.types import StateSnapshot

from agents.ceo_agent import CEOAgent, Roadmap, Task, TaskStatus
from memory.memory_system import AgentMemory, MemoryType
from tools.toolkit import Toolkit


class WorkflowState(dict):
    """State machine for workflow"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setdefault('client_prompt', None)
        self.setdefault('analysis', {})
        self.setdefault('roadmap', None)
        self.setdefault('current_task', None)
        self.setdefault('task_results', {})
        self.setdefault('errors', [])
        self.setdefault('status', 'initializing')
        self.setdefault('progress_history', [])
        self.setdefault('requires_human_approval', False)
        self.setdefault('approval_question', None)


class DevSwarmOrchestrator:
    """
    Main orchestrator using LangGraph for stateful workflows
    Handles multi-step processes with decision points
    """
    
    def __init__(self, llm: Any, codebase_path: str = "."):
        self.llm = llm
        self.toolkit = Toolkit(codebase_path)
        self.memory = AgentMemory()
        self.ceo = CEOAgent(llm, self.toolkit)
        self.workflow = self._create_workflow()
        self.execution_state = None
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (state transitions)
        workflow.add_node("receive_prompt", self._receive_prompt)
        workflow.add_node("analyze_prompt", self._analyze_prompt)
        workflow.add_node("create_roadmap", self._create_roadmap)
        workflow.add_node("validate_plan", self._validate_plan)
        workflow.add_node("request_approval", self._request_approval)
        workflow.add_node("execute_tasks", self._execute_tasks)
        workflow.add_node("monitor_progress", self._monitor_progress)
        workflow.add_node("handle_failures", self._handle_failures)
        workflow.add_node("complete_project", self._complete_project)
        workflow.add_node("error_handler", self._error_handler)
        
        # Add edges (transitions)
        workflow.add_edge("receive_prompt", "analyze_prompt")
        workflow.add_edge("analyze_prompt", "create_roadmap")
        workflow.add_edge("create_roadmap", "validate_plan")
        workflow.add_edge("validate_plan", "request_approval")
        
        # Conditional edge - requires human approval
        workflow.add_conditional_edges(
            "request_approval",
            self._should_get_approval,
            {
                True: "request_approval",
                False: "execute_tasks"
            }
        )
        
        workflow.add_edge("execute_tasks", "monitor_progress")
        
        # Monitor progress - check status
        workflow.add_conditional_edges(
            "monitor_progress",
            self._check_progress_status,
            {
                "complete": "complete_project",
                "in_progress": "monitor_progress",
                "failed": "handle_failures",
                "error": "error_handler"
            }
        )
        
        workflow.add_edge("handle_failures", "execute_tasks")
        workflow.add_edge("complete_project", END)
        workflow.add_edge("error_handler", END)
        
        # Set entry point
        workflow.set_entry_point("receive_prompt")
        
        return workflow
    
    async def _receive_prompt(self, state: WorkflowState) -> WorkflowState:
        """Receive and validate client prompt"""
        print("📥 Receiving client prompt...")
        state['status'] = 'analyzing'
        return state
    
    async def _analyze_prompt(self, state: WorkflowState) -> WorkflowState:
        """Analyze prompt with CEO agent"""
        print("🔍 CEO Agent analyzing prompt...")
        
        try:
            analysis = await self.ceo.understand_prompt(state['client_prompt'])
            state['analysis'] = analysis
            state['status'] = 'planning'
            return state
        except Exception as e:
            state['errors'].append(str(e))
            state['status'] = 'error'
            return state
    
    async def _create_roadmap(self, state: WorkflowState) -> WorkflowState:
        """Create project roadmap"""
        print("🗺️  CEO Agent creating roadmap...")
        
        try:
            roadmap = await self.ceo.create_roadmap(state['analysis'])
            state['roadmap'] = roadmap
            state['status'] = 'planning_validation'
            
            # Store in memory
            self.memory.long_term.add(
                content=f"Roadmap created for: {roadmap.objective}",
                memory_type=MemoryType.SEMANTIC,
                tags=["roadmap", state['client_prompt'][:20]],
                importance=0.95
            )
            
            return state
        except Exception as e:
            state['errors'].append(str(e))
            state['status'] = 'error'
            return state
    
    async def _validate_plan(self, state: WorkflowState) -> WorkflowState:
        """Validate the created plan"""
        print("✓ Validating roadmap...")
        
        roadmap = state['roadmap']
        
        # Validation checks
        checks = {
            "has_tasks": len(roadmap.tasks) > 0,
            "has_objective": len(roadmap.objective) > 0,
            "tasks_have_descriptions": all(t.description for t in roadmap.tasks),
            "dependencies_valid": self._validate_dependencies(roadmap.tasks)
        }
        
        all_valid = all(checks.values())
        
        if all_valid:
            state['status'] = 'ready_for_approval'
            print(f"✅ Roadmap valid with {len(roadmap.tasks)} tasks")
        else:
            state['errors'].append(f"Validation failed: {checks}")
            state['status'] = 'validation_failed'
        
        return state
    
    async def _request_approval(self, state: WorkflowState) -> WorkflowState:
        """Request human approval for plan"""
        print("\n" + "="*60)
        print("🤝 HUMAN APPROVAL REQUIRED")
        print("="*60)
        
        roadmap = state['roadmap']
        
        approval_text = f"""
PROJECT ROADMAP FOR APPROVAL:
Objective: {roadmap.objective}
Total Tasks: {len(roadmap.tasks)}

TASKS:
"""
        for task in roadmap.tasks:
            approval_text += f"  [{task.id}] {task.description} (Priority: {task.priority})\n"
        
        print(approval_text)
        print("\nApprove? (yes/no): ", end="")
        
        # For now, auto-approve in autonomous mode
        response = "yes"  # input()
        print(response)
        
        if response.lower() == 'yes':
            state['status'] = 'executing'
            return state
        else:
            state['status'] = 'rejected'
            state['errors'].append("User rejected roadmap")
            return state
    
    def _should_get_approval(self, state: WorkflowState) -> bool:
        """Check if approval already given"""
        return state['status'] == 'ready_for_approval'
    
    async def _execute_tasks(self, state: WorkflowState) -> WorkflowState:
        """Execute tasks from roadmap"""
        print("🚀 Executing tasks...")
        
        roadmap = state['roadmap']
        
        for task in roadmap.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.IN_PROGRESS
                
                # Assign to agent
                agent_name, confidence = self.ceo.assign_task(
                    task, 
                    list(self.ceo.agents.keys())
                )
                
                print(f"  → Task {task.id}: Assigned to {agent_name}")
                
                # Simulate task execution (in real system, would call agent)
                try:
                    # Here we would call the actual agent
                    result = await self._simulate_task_execution(task)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    
                    state['task_results'][task.id] = result
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    state['errors'].append(f"Task {task.id} failed: {e}")
        
        state['status'] = 'monitoring'
        return state
    
    async def _monitor_progress(self, state: WorkflowState) -> WorkflowState:
        """Monitor task progress"""
        progress = self.ceo.track_progress()
        
        print(f"\n📊 Progress: {progress['completion_percentage']:.1f}% complete")
        print(f"   ✓ {progress['completed']} completed")
        print(f"   → {progress['in_progress']} in progress")
        print(f"   ⏳ {progress['pending']} pending")
        
        state['progress_history'].append(progress)
        
        return state
    
    def _check_progress_status(self, state: WorkflowState) -> str:
        """Determine next step based on progress"""
        progress = self.ceo.track_progress()
        
        if progress['completion_percentage'] == 100:
            return "complete"
        elif progress['failed'] > 0:
            return "failed"
        elif len(state['errors']) > 0:
            return "error"
        else:
            return "in_progress"
    
    async def _handle_failures(self, state: WorkflowState) -> WorkflowState:
        """Handle task failures"""
        print("⚠️  Handling failures...")
        
        roadmap = state['roadmap']
        failed_tasks = [t for t in roadmap.tasks if t.status == TaskStatus.FAILED]
        
        for task in failed_tasks:
            print(f"  Attempting retry for {task.id}: {task.error}")
            # Logic to retry or escalate
        
        return state
    
    async def _complete_project(self, state: WorkflowState) -> WorkflowState:
        """Complete project"""
        print("\n" + "="*60)
        print("✅ PROJECT COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        progress = self.ceo.track_progress()
        print(f"\nFinal Status:")
        print(f"  Total Tasks: {progress['total_tasks']}")
        print(f"  Completed: {progress['completed']}")
        print(f"  Failed: {progress['failed']}")
        
        state['status'] = 'completed'
        
        # Store completion in memory
        self.memory.long_term.add(
            content=f"Project completed: {state['client_prompt'][:100]}",
            memory_type=MemoryType.EPISODIC,
            tags=["completed"],
            importance=0.9
        )
        
        return state
    
    async def _error_handler(self, state: WorkflowState) -> WorkflowState:
        """Handle workflow errors"""
        print("\n❌ ERROR in workflow")
        for error in state['errors']:
            print(f"  - {error}")
        
        state['status'] = 'error'
        return state
    
    def _validate_dependencies(self, tasks: List[Task]) -> bool:
        """Validate task dependencies"""
        task_ids = {t.id for t in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    return False
        
        return True
    
    async def _simulate_task_execution(self, task: Task) -> str:
        """Simulate task execution (placeholder)"""
        await asyncio.sleep(0.5)  # Simulate work
        return f"Executed: {task.description}"
    
    async def run(self, client_prompt: str) -> Dict[str, Any]:
        """Execute complete workflow"""
        print(f"\n{'='*60}")
        print(f"🎯 DevSwarm Orchestrator Starting")
        print(f"{'='*60}\n")
        
        state = WorkflowState(client_prompt=client_prompt)
        
        try:
            # Run through all workflow nodes manually
            # In production, would use workflow.invoke()
            
            state = await self._receive_prompt(state)
            state = await self._analyze_prompt(state)
            
            if state['status'] != 'error':
                state = await self._create_roadmap(state)
                state = await self._validate_plan(state)
                
                if state['status'] != 'validation_failed':
                    state = await self._request_approval(state)
                    
                    if state['status'] == 'executing':
                        state = await self._execute_tasks(state)
                        state = await self._monitor_progress(state)
                        
                        if state['status'] == 'complete':
                            state = await self._complete_project(state)
                        elif state['status'] == 'failed':
                            state = await self._handle_failures(state)
                    
                    if state['status'] == 'error':
                        state = await self._error_handler(state)
        
        except Exception as e:
            print(f"Fatal error in workflow: {e}")
            state['status'] = 'fatal_error'
            state['errors'].append(str(e))
        
        return state
