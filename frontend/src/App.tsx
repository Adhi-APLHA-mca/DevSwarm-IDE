import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import FileExplorer from './components/FileExplorer';
import Editor from './components/Editor';
import ChatPanel from './components/ChatPanel';
import ConversationPanel, { Message } from './components/ConversationPanel';
import TabBar from './components/TabBar';
import ResizeHandle from './components/ResizeHandle';
import { apiClient } from './services/api';
import './App.css';

interface OpenFile {
  id: string;
  path: string;
  name: string;
  content: string;
  isDirty: boolean;
}

// Multi-Agent Types
type AgentType = 'ceo' | 'ba' | 'developer' | 'reviewer' | 'debugger';

interface Agent {
  id: AgentType;
  name: string;
  icon: string;
  description: string;
}

const AGENTS: Agent[] = [
  { id: 'ceo', name: 'CEO/Orchestrator', icon: '👔', description: 'Project planning & orchestration' },
  { id: 'ba', name: 'Business Analyst', icon: '📊', description: 'Requirements & analysis' },
  { id: 'developer', name: 'Developer', icon: '💻', description: 'Code writing' },
  { id: 'reviewer', name: 'Code Reviewer', icon: '🔍', description: 'Code review & QA' },
  { id: 'debugger', name: 'Debugger', icon: '🐛', description: 'Bug fixing' },
];

export default function App() {
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState('explorer');
  const [leftPanelWidth, setLeftPanelWidth] = useState(250);
  const [rightPanelWidth, setRightPanelWidth] = useState(300);
  
  // Multi-Agent Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [currentQuestions, setCurrentQuestions] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAgent, setCurrentAgent] = useState<AgentType>('ba');
  const [showAgentSelector, setShowAgentSelector] = useState(true);
  const [conversationStarted, setConversationStarted] = useState(false);
  const [projectGoal, setProjectGoal] = useState<string>('');

  const activeFile = openFiles.find(f => f.id === activeFileId);

  const handleFileSelect = (filePath: string, content: string) => {
    const fileId = filePath;
    const existingFile = openFiles.find(f => f.id === fileId);

    if (existingFile) {
      // File already open, just activate it
      setActiveFileId(fileId);
    } else {
      // New file, add to open files
      const fileName = filePath.split(/[\\\/]/).pop() || 'Untitled';
      const newFile: OpenFile = {
        id: fileId,
        path: filePath,
        name: fileName,
        content,
        isDirty: false,
      };
      setOpenFiles([...openFiles, newFile]);
      setActiveFileId(fileId);
    }
  };

  const handleContentChange = (newContent: string) => {
    if (!activeFileId) return;

    setOpenFiles(openFiles.map(file =>
      file.id === activeFileId
        ? { ...file, content: newContent, isDirty: true }
        : file
    ));
  };

  const handleTabClose = (fileId: string) => {
    const newFiles = openFiles.filter(f => f.id !== fileId);
    setOpenFiles(newFiles);

    if (activeFileId === fileId) {
      setActiveFileId(newFiles.length > 0 ? newFiles[newFiles.length - 1].id : null);
    }
  };

  const handleSaveFile = async (fileId: string) => {
    const file = openFiles.find(f => f.id === fileId);
    if (!file) return;

    try {
      const result = await window.electronAPI.writeFile(file.path, file.content);
      if (result.success) {
        setOpenFiles(openFiles.map(f =>
          f.id === fileId ? { ...f, isDirty: false } : f
        ));
      } else {
        console.error('Failed to save file:', result.error);
      }
    } catch (error) {
      console.error('Error saving file:', error);
    }
  };

  const handleSaveAll = async () => {
    for (const file of openFiles) {
      if (file.isDirty) {
        await handleSaveFile(file.id);
      }
    }
  };

  // Keyboard shortcut: Ctrl+S to save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (activeFileId) {
          handleSaveFile(activeFileId);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeFileId, openFiles]);

  const handleLeftResize = (delta: number) => {
    const newWidth = Math.max(200, Math.min(500, leftPanelWidth + delta));
    setLeftPanelWidth(newWidth);
  };

  const handleRightResize = (delta: number) => {
    const newWidth = Math.max(250, Math.min(500, rightPanelWidth - delta));
    setRightPanelWidth(newWidth);
  };

  // Chat handlers
  const handleInitiateChat = async (userMessage: string) => {
    if (!userMessage.trim()) return;

    setIsLoading(true);
    
    // Store project goal for later use
    setProjectGoal(userMessage);

    // Add greeting if first message
    if (!conversationStarted) {
      const greetingMsg: Message = {
        id: Date.now() + '-greeting',
        type: 'greeting',
        content: 'Welcome to DevSwarm! I\'m the Business Analyst Agent. I\'ll help you gather requirements and understand your project needs through intelligent questioning.',
        agentName: 'Business Analyst',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, greetingMsg]);
      setConversationStarted(true);
    }

    // Add user message to chat
    const userMsg: Message = {
      id: Date.now() + '-user',
      type: 'user',
      content: userMessage,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const agentName = AGENTS.find(a => a.id === currentAgent)?.name || 'Agent';
      
      // Initiate conversation with user message
      const response = await apiClient.initiate(userMessage);
      
      // Store questions and show first one
      setCurrentQuestions(response.questions);
      setCurrentQuestionIndex(0);
      setSessionActive(true);

      // Add first question to chat with agent name
      const questionMsg: Message = {
        id: Date.now() + '-q0',
        type: 'question',
        content: response.questions[0],
        agentName: 'Business Analyst',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, questionMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: Date.now() + '-error',
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to initiate chat'}`,
        agentName: 'Business Analyst',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerQuestion = async (answer: string) => {
    if (!answer.trim() || !sessionActive) return;

    setIsLoading(true);

    // Add user answer to chat
    const answerMsg: Message = {
      id: Date.now() + '-answer',
      type: 'user',
      content: answer,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, answerMsg]);

    try {
      // Submit answer to backend
      const response = await apiClient.submitAnswer(currentQuestionIndex, answer);

      // Check if all questions are answered
      if (response.is_complete) {
        const completeMsg: Message = {
          id: Date.now() + '-complete',
          type: 'system',
          content: 'All questions answered! Processing requirements and generating strategic development plan...',
          agentName: 'Business Analyst',
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, completeMsg]);

        // Process requirements
        const reqResponse = await apiClient.processRequirements();
        
        // Generate CEO development plan
        const devPlan = await apiClient.generateDevelopmentPlan(reqResponse.requirements, projectGoal);
        
        const ceoMsg: Message = {
          id: Date.now() + '-ceo-plan',
          type: 'agent',
          content: devPlan,
          agentName: 'CEO/Orchestrator',
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, ceoMsg]);

        setSessionActive(false);
      } else {
        // Show next question
        const nextIndex = response.next_question_index || currentQuestionIndex + 1;
        setCurrentQuestionIndex(nextIndex);

        if (nextIndex < currentQuestions.length) {
          const nextQuestionMsg: Message = {
            id: Date.now() + '-q' + nextIndex,
            type: 'question',
            content: currentQuestions[nextIndex],
            agentName: 'Business Analyst',
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, nextQuestionMsg]);
        }
      }
    } catch (error) {
      const errorMsg: Message = {
        id: Date.now() + '-error',
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to submit answer'}`,
        agentName: 'Business Analyst',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <Sidebar activePanel={activePanel} onPanelChange={setActivePanel} />

      {/* Left Panel - File Explorer */}
      <div className="panel left-panel" style={{ width: `${leftPanelWidth}px` }}>
        <div className="panel-header">
          <h2>Explorer</h2>
        </div>
        {activePanel === 'explorer' && (
          <FileExplorer onFileSelect={handleFileSelect} />
        )}
        {activePanel !== 'explorer' && (
          <div className="panel-content">
            <div style={{ padding: '16px', color: '#858585' }}>
              {activePanel === 'search' && <p>Search panel coming soon...</p>}
              {activePanel === 'scm' && <p>Source control panel coming soon...</p>}
              {activePanel === 'debug' && <p>Debug panel coming soon...</p>}
              {activePanel === 'extensions' && <p>Extensions panel coming soon...</p>}
            </div>
          </div>
        )}
        <ResizeHandle onResize={handleLeftResize} direction="horizontal" />
      </div>

      {/* Middle Panel - Editor */}
      <div className="panel middle-panel">
        <TabBar
          tabs={openFiles.map(f => ({
            id: f.id,
            path: f.path,
            name: f.name,
            isDirty: f.isDirty,
          }))}
          activeTabId={activeFileId}
          onTabClick={setActiveFileId}
          onTabClose={handleTabClose}
          onSaveTab={handleSaveFile}
        />
        <div className="panel-header editor-header">
          {activeFile ? (
            <h2>
              {activeFile.name}
              {activeFile.isDirty && <span className="unsaved-indicator">●</span>}
            </h2>
          ) : (
            <h2>Welcome</h2>
          )}
        </div>
        {activeFile ? (
          <Editor
            key={activeFile.id}
            filePath={activeFile.path}
            content={activeFile.content}
            onContentChange={handleContentChange}
          />
        ) : (
          <div className="welcome-screen">
            <h1>DevSwarm IDE</h1>
            <p>Open a folder to get started</p>
            <p className="welcome-hint">Ctrl+S to save • Click tabs to switch files</p>
          </div>
        )}
      </div>

      {/* Right Panel - Chat */}
      <div className="panel right-panel" style={{ width: `${rightPanelWidth}px` }}>
        <div className="panel-header">
          <h2>Chat</h2>
        </div>
        
        {/* Chat Area */}
        <ConversationPanel messages={messages} isLoading={isLoading} />
        
        {/* Chat Input */}
        <ChatPanel 
          onSendInitial={handleInitiateChat}
          onSendAnswer={handleAnswerQuestion}
          isSessionActive={sessionActive}
          isLoading={isLoading}
        />
        
        <ResizeHandle onResize={handleRightResize} direction="horizontal" />
      </div>
    </div>
  );
}
