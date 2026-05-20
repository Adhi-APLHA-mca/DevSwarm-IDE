import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import FileExplorer from './components/FileExplorer';
import Editor from './components/Editor';
import ChatPanel from './components/ChatPanel';
import TabBar from './components/TabBar';
import ResizeHandle from './components/ResizeHandle';
import './App.css';

interface OpenFile {
  id: string;
  path: string;
  name: string;
  content: string;
  isDirty: boolean;
}

export default function App() {
  const [openFiles, setOpenFiles] = useState<OpenFile[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState('explorer');
  const [leftPanelWidth, setLeftPanelWidth] = useState(250);
  const [rightPanelWidth, setRightPanelWidth] = useState(300);

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
          <h2>Chat (Coming Soon)</h2>
        </div>
        <ChatPanel />
        <ResizeHandle onResize={handleRightResize} direction="horizontal" />
      </div>
    </div>
  );
}
