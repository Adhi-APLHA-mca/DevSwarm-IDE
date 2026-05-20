"""
Memory Management System for DevSwarm Agents
Handles both short-term (current task) and long-term (project history) memory
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import json


class MemoryType(str, Enum):
    """Types of memory in the system"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"  # Individual events/tasks
    SEMANTIC = "semantic"  # Learned facts/patterns


class MemoryEntry(BaseModel):
    """Single memory entry"""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance_score: float = 0.5  # 0-1, for prioritization
    tags: List[str] = Field(default_factory=list)


class ShortTermMemory:
    """
    Current task/conversation context
    - Active project state
    - Current task progress
    - Recent decisions
    """
    
    def __init__(self, max_entries: int = 50):
        self.entries: List[MemoryEntry] = []
        self.max_entries = max_entries
        self.context = {}  # Current session context
    
    def add(self, content: str, metadata: Dict = None, tags: List[str] = None, importance: float = 0.5):
        """Add entry to short-term memory"""
        entry = MemoryEntry(
            id=f"st_{len(self.entries)}_{datetime.now().timestamp()}",
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            metadata=metadata or {},
            importance_score=importance,
            tags=tags or []
        )
        self.entries.append(entry)
        
        # Keep only recent entries
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)
        
        return entry.id
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context for LLM"""
        return {
            "current_entries": len(self.entries),
            "context": self.context,
            "recent_memories": [
                {"content": e.content, "tags": e.tags}
                for e in self.entries[-10:]
            ]
        }
    
    def update_context(self, key: str, value: Any):
        """Update session context"""
        self.context[key] = value
    
    def clear(self):
        """Clear short-term memory at session end"""
        self.entries.clear()
        self.context.clear()


class LongTermMemory:
    """
    Project history and learnings
    - Past tasks and solutions
    - Project patterns
    - Learned best practices
    - Performance metrics
    """
    
    def __init__(self, storage_path: str = "memory/long_term.json"):
        self.storage_path = storage_path
        self.entries: List[MemoryEntry] = []
        self.learnings: Dict[str, Any] = {}
        self.load()
    
    def add(self, content: str, memory_type: MemoryType, metadata: Dict = None, 
            tags: List[str] = None, importance: float = 0.5):
        """Add entry to long-term memory"""
        entry = MemoryEntry(
            id=f"lt_{len(self.entries)}_{datetime.now().timestamp()}",
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
            importance_score=importance,
            tags=tags or []
        )
        self.entries.append(entry)
        self.save()
        return entry.id
    
    def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search long-term memory by content/tags"""
        results = []
        query_lower = query.lower()
        
        for entry in self.entries:
            if (query_lower in entry.content.lower() or 
                any(query_lower in tag.lower() for tag in entry.tags)):
                results.append(entry)
        
        # Sort by importance and recency
        results.sort(key=lambda x: (-x.importance_score, -x.timestamp.timestamp()))
        return results[:limit]
    
    def add_learning(self, key: str, value: Any):
        """Store learned pattern or best practice"""
        self.learnings[key] = {
            "value": value,
            "learned_at": datetime.now().isoformat(),
            "usage_count": 0
        }
        self.save()
    
    def get_learning(self, key: str) -> Optional[Any]:
        """Retrieve learned pattern"""
        if key in self.learnings:
            self.learnings[key]["usage_count"] += 1
            self.save()
            return self.learnings[key]["value"]
        return None
    
    def get_all_learnings(self) -> Dict[str, Any]:
        """Get all learnings for context"""
        return self.learnings
    
    def save(self):
        """Persist to disk"""
        try:
            with open(self.storage_path, 'w') as f:
                data = {
                    "entries": [e.dict() for e in self.entries],
                    "learnings": self.learnings
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving long-term memory: {e}")
    
    def load(self):
        """Load from disk"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                # Load entries
                self.entries = [MemoryEntry(**e) for e in data.get("entries", [])]
                self.learnings = data.get("learnings", {})
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading long-term memory: {e}")


class AgentMemory:
    """
    Combined memory system for agents
    Provides unified interface for both short and long-term memory
    """
    
    def __init__(self, long_term_path: str = "memory/long_term.json"):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(long_term_path)
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get complete memory context for LLM"""
        return {
            "short_term": self.short_term.get_context(),
            "long_term_learnings": self.long_term.get_all_learnings(),
            "recent_similar_tasks": [
                e.dict() for e in self.long_term.search("task", limit=3)
            ]
        }
    
    def remember_task(self, task_description: str, solution: str, success: bool, 
                     metadata: Dict = None):
        """
        Remember completed task for future reference
        """
        entry_id = self.long_term.add(
            content=f"Task: {task_description}\nSolution: {solution}",
            memory_type=MemoryType.EPISODIC,
            metadata={
                "success": success,
                "task_description": task_description,
                **(metadata or {})
            },
            tags=["task", "completed"],
            importance=0.8 if success else 0.5
        )
        return entry_id
