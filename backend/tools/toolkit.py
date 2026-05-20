"""
Tools for DevSwarm Agents
Includes: Code execution, Git operations, Web search, RAG on codebase
"""

from typing import Any, Dict, List, Optional
import subprocess
import json
import os
from datetime import datetime


class CodeExecutionTool:
    """Execute code safely and capture output"""
    
    def __init__(self, sandbox_dir: str = "sandbox"):
        self.sandbox_dir = sandbox_dir
        os.makedirs(sandbox_dir, exist_ok=True)
    
    def execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code in sandbox
        Returns: {"success": bool, "output": str, "error": str, "execution_time": float}
        """
        import time
        
        file_path = os.path.join(self.sandbox_dir, f"exec_{datetime.now().timestamp()}.py")
        
        try:
            # Write code to file
            with open(file_path, 'w') as f:
                f.write(code)
            
            start_time = time.time()
            result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "execution_time": execution_time,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Code execution timed out after {timeout} seconds",
                "execution_time": timeout,
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": 0,
                "return_code": -1
            }
        finally:
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def execute_bash(self, command: str, timeout: int = 30, cwd: str = None) -> Dict[str, Any]:
        """Execute bash command"""
        import time
        
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True,
                cwd=cwd
            )
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "execution_time": execution_time,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "execution_time": timeout,
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": 0,
                "return_code": -1
            }


class GitOperationsTool:
    """Handle Git operations"""
    
    @staticmethod
    def clone_repo(repo_url: str, target_dir: str) -> Dict[str, Any]:
        """Clone a Git repository"""
        try:
            result = subprocess.run(
                ["git", "clone", repo_url, target_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "message": result.stdout or result.stderr,
                "repo_path": target_dir if result.returncode == 0 else None
            }
        except Exception as e:
            return {"success": False, "message": str(e), "repo_path": None}
    
    @staticmethod
    def get_file_diff(file_path: str, repo_path: str = ".") -> Dict[str, Any]:
        """Get Git diff for a file"""
        try:
            result = subprocess.run(
                ["git", "diff", file_path],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            return {
                "success": result.returncode == 0,
                "diff": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }
        except Exception as e:
            return {"success": False, "diff": "", "error": str(e)}
    
    @staticmethod
    def create_commit(message: str, files: List[str] = None, repo_path: str = ".") -> Dict[str, Any]:
        """Create a Git commit"""
        try:
            # Add files
            if files:
                subprocess.run(["git", "add"] + files, cwd=repo_path, check=True)
            else:
                subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            return {
                "success": result.returncode == 0,
                "message": result.stdout or result.stderr,
                "commit_hash": result.stdout.split()[-1] if "commit" in result.stdout else None
            }
        except Exception as e:
            return {"success": False, "message": str(e), "commit_hash": None}


class WebSearchTool:
    """Search web for documentation and latest info"""
    
    @staticmethod
    def search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documentation and resources
        Note: Requires integration with search API (Brave, Google, Bing)
        """
        # Placeholder - would integrate with actual search API
        return [
            {
                "title": f"Result for: {query}",
                "url": "https://docs.example.com",
                "snippet": "Documentation snippet would go here",
                "source": "docs"
            }
        ]


class CodebaseRAGTool:
    """RAG (Retrieval Augmented Generation) on codebase"""
    
    def __init__(self, codebase_path: str):
        self.codebase_path = codebase_path
        self.indexed_files = {}
    
    def index_codebase(self, file_extensions: List[str] = None):
        """Index codebase files"""
        if file_extensions is None:
            file_extensions = ['.py', '.ts', '.tsx', '.js', '.jsx', '.json']
        
        for root, dirs, files in os.walk(self.codebase_path):
            # Skip hidden and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            self.indexed_files[file_path] = {
                                "content": content,
                                "lines": len(content.split('\n')),
                                "indexed_at": datetime.now().isoformat()
                            }
                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")
    
    def search_codebase(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search indexed codebase"""
        results = []
        query_lower = query.lower()
        
        for file_path, data in self.indexed_files.items():
            if query_lower in data["content"].lower():
                # Find relevant lines
                lines = data["content"].split('\n')
                relevant_lines = [
                    (i, line) for i, line in enumerate(lines)
                    if query_lower in line.lower()
                ]
                
                if relevant_lines:
                    results.append({
                        "file": file_path,
                        "lines_of_code": data["lines"],
                        "relevant_lines": relevant_lines[:3],
                        "match_count": len(relevant_lines)
                    })
        
        return sorted(results, key=lambda x: -x["match_count"])[:limit]
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get full content of indexed file"""
        if file_path in self.indexed_files:
            return self.indexed_files[file_path]["content"]
        return None


class Toolkit:
    """Unified toolkit for agents"""
    
    def __init__(self, codebase_path: str = "."):
        self.code_exec = CodeExecutionTool()
        self.git = GitOperationsTool()
        self.web_search = WebSearchTool()
        self.rag = CodebaseRAGTool(codebase_path)
    
    def get_tools_description(self) -> str:
        """Get description of available tools for LLM"""
        return """
Available Tools:
1. code_execution - Execute Python/bash code
2. git_operations - Clone, commit, diff operations
3. web_search - Search for documentation
4. codebase_rag - Search and retrieve from codebase
"""
