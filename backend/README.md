# 🤖 DevSwarm Backend Agents

Autonomous AI agent system for DevSwarm IDE using LangChain, LangGraph, and Groq LLM.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│          DevSwarm Orchestrator (Main Entry)             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│      LangGraph Stateful Workflow (orchestrator.py)      │
│                                                          │
│  receive_prompt → analyze → create_roadmap → validate  │
│       ↓                                        ↓         │
│  request_approval → execute_tasks → monitor → complete │
│       ↓                    ↓                             │
│   handle_failures ← ← ← ← ← handle_errors              │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼──────────────────┐
        ↓                 ↓                  ↓
   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
   │ CEO Agent   │  │ Memory System│  │   Toolkit    │
   │ (ceo_agent) │  │(memory_sys)  │  │ (toolkit.py) │
   └─────────────┘  └──────────────┘  └──────────────┘
         ↓                 ↓                  ↓
   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
   │ Task Mgmt   │  │Short-term &  │  │ Code Exec    │
   │ Roadmap     │  │Long-term Mem │  │ Git Ops      │
   │ Progress    │  │Learning      │  │ Web Search   │
   │ Assignment  │  │              │  │ Codebase RAG │
   └─────────────┘  └──────────────┘  └──────────────┘

                 │ Groq API (LLM) │
```

## 📁 Directory Structure

```
backend/
├── agents/              # Agent implementations
│   ├── ceo_agent.py     # CEO/Orchestrator Agent
│   ├── code_writer.py   # (Coming soon) Code writing agent
│   ├── reviewer.py      # (Coming soon) Code review agent
│   └── debugger.py      # (Coming soon) Debugging agent
│
├── workflows/           # LangGraph workflows
│   └── orchestrator.py  # Main stateful workflow
│
├── memory/              # Memory management
│   ├── memory_system.py # Short-term & long-term memory
│   └── long_term.json   # Persistent memory storage
│
├── tools/               # Toolkit for agents
│   └── toolkit.py       # Code execution, Git, Search, RAG
│
├── main.py              # Entry point for testing
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🎯 CEO/Orchestrator Agent

**The Brain** - Manages the entire autonomous workflow.

### Responsibilities:
1. **Understanding** - Analyze client prompts
2. **Planning** - Create detailed roadmaps
3. **Task Division** - Break work into subtasks
4. **Assignment** - Route tasks to specialized agents
5. **Tracking** - Monitor progress and handle blockers
6. **Coordination** - Manage task dependencies
7. **Conflict Resolution** - Handle issues and prioritize

### Key Features:
- Stateful conversations using LangChain messages
- Roadmap generation with task dependencies
- Progress tracking and status monitoring
- Human-in-the-loop approval for critical decisions
- Memory integration (short + long-term)

## 💾 Memory System

### Short-Term Memory
- **Scope**: Current session/task context
- **Purpose**: Immediate context for LLM
- **Retention**: ~50 recent entries per session
- **Use**: Active task state, recent decisions

### Long-Term Memory
- **Scope**: Project history and learnings
- **Purpose**: Past solutions and patterns
- **Retention**: Persistent (JSON storage)
- **Use**: Learn from past tasks, apply patterns

### Example Usage:
```python
from memory.memory_system import AgentMemory

memory = AgentMemory()

# Add to short-term
memory.short_term.add(
    content="User requested feature X",
    tags=["feature", "requirement"],
    importance=0.9
)

# Add to long-term
memory.long_term.add(
    content="Task: Build API. Solution: FastAPI with async",
    memory_type=MemoryType.EPISODIC,
    tags=["api", "backend"],
    importance=0.85
)

# Learn from past
memory.long_term.add_learning(
    key="best_api_framework",
    value="FastAPI for Python"
)

# Retrieve context
context = memory.get_full_context()
```

## 🛠️ Toolkit Features

### 1. Code Execution
```python
toolkit.code_exec.execute_python(code, timeout=30)
# Returns: success, output, error, execution_time
```

### 2. Git Operations
```python
toolkit.git.clone_repo(url, target_dir)
toolkit.git.create_commit(message, files)
toolkit.git.get_file_diff(file_path)
```

### 3. Web Search
```python
results = toolkit.web_search.search(query, num_results=5)
```

### 4. Codebase RAG
```python
toolkit.rag.index_codebase()
results = toolkit.rag.search_codebase(query, limit=5)
```

## 🔄 Workflow States

```
receive_prompt
     ↓
analyze_prompt ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← error_handler
     ↓
create_roadmap
     ↓
validate_plan
     ↓
request_approval
     ↓
execute_tasks
     ↓
monitor_progress ← ← ← handle_failures ← ← ← ← ┐
     ↓                                          │
  [COMPLETE?]                                   │
     ├─ YES → complete_project → END            │
     ├─ FAILED → handle_failures ─ ─ ─ ─ ─ ─ ─ ┘
     ├─ ERROR → error_handler → END
     └─ IN_PROGRESS → monitor_progress (loop)
```

## 🚀 Getting Started

### 1. Setup Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Groq API
```bash
# Copy and edit .env
cp .env.example .env

# Add your Groq API key
# Get it from: https://console.groq.com
```

### 4. Run Autonomous Test
```bash
python main.py
```

### 5. Observe Workflow
The orchestrator will:
1. Receive your prompt
2. Analyze requirements
3. Create a roadmap with tasks
4. Request your approval
5. Execute tasks with agents
6. Monitor progress
7. Complete project
8. Store learnings in memory

## 📊 Example Workflow Run

```
============================================================================
🚀 DevSwarm - Autonomous AI Agent System
============================================================================

✓ Using Groq API as LLM backend
  API Key: gsk_...

============================================================================
📋 AVAILABLE TEST PROMPTS:
============================================================================

1. Create a Python CLI tool that...

2. Build a REST API for a TODO application...

============================================================================
🤖 AUTONOMOUS MODE - Running first test prompt
============================================================================

Client Request:
Create a Python CLI tool that reads CSV files, performs data analysis...

📥 Receiving client prompt...
🔍 CEO Agent analyzing prompt...
🗺️  Creating roadmap...
✓ Validating roadmap...

============================================================================
🤝 HUMAN APPROVAL REQUIRED
============================================================================

PROJECT ROADMAP FOR APPROVAL:
Objective: Build Python CSV analysis CLI tool
Total Tasks: 6

TASKS:
  [task_0] Setup project structure (Priority: 5)
  [task_1] Implement CSV reading functionality (Priority: 5)
  [task_2] Build data analysis module (Priority: 4)
  [task_3] Create charting functionality (Priority: 3)
  ...

============================================================================
✅ PROJECT COMPLETED SUCCESSFULLY!
============================================================================

Final Status:
  Total Tasks: 6
  Completed: 6
  Failed: 0

Final Progress: 100.0%
```

## 🔮 Future Enhancements

### Agents to Implement:
- **CodeWriter** - Implements features
- **CodeReviewer** - Reviews code quality
- **Debugger** - Fixes bugs
- **Documentor** - Writes documentation
- **Tester** - Writes tests

### Features:
- [ ] Persistent workflow state
- [ ] WebSocket connection to UI
- [ ] Real-time progress streaming
- [ ] Advanced RAG with embeddings
- [ ] SWE-bench evaluation
- [ ] Distributed task execution
- [ ] Advanced conflict resolution
- [ ] Multi-project management

## ⚙️ Configuration

Edit `main.py` to:
- Change LLM model (other Groq models available)
- Adjust temperature/creativity
- Set timeout values
- Enable/disable features

Available Groq Models:
- `mixtral-8x7b-32768` (Fast, balanced)
- `gemma-7b-it` (Optimized for instruction)
- `llama2-70b-4096` (Powerful)

## 🧪 Testing

### Run all tests
```bash
python -m pytest tests/
```

### Run specific agent test
```bash
python -m pytest tests/agents/test_ceo_agent.py
```

### Test with custom prompt
```python
import asyncio
from langchain_groq import ChatGroq
from workflows.orchestrator import DevSwarmOrchestrator

llm = ChatGroq(model="mixtral-8x7b-32768", groq_api_key="your_key")
orchestrator = DevSwarmOrchestrator(llm)

result = asyncio.run(orchestrator.run("Your custom prompt here"))
```

## 📝 Logging

Configure logging in environment:
```bash
LOG_LEVEL=DEBUG  # For verbose output
LOG_LEVEL=INFO   # For standard output
```

## 🤝 Contributing

To add a new agent:
1. Create `agents/new_agent.py`
2. Inherit from `BaseAgent`
3. Implement required methods
4. Register in orchestrator
5. Add tests

## 📚 Resources

- [LangChain Docs](https://python.langchain.com)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Groq API Docs](https://console.groq.com/docs)
- [SWE-bench](https://www.swebench.com/) - Evaluation standard

## 📄 License

DevSwarm - MIT License

---

**Status**: 🚧 Under Active Development

Next: Implementing specialized agents and full workflow integration.
