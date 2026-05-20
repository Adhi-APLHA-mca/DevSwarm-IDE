import Editor from '@monaco-editor/react';

interface EditorProps {
  filePath: string | null;
  content: string;
  onContentChange?: (content: string) => void;
}

export default function EditorComponent({ filePath, content, onContentChange }: EditorProps) {
  const getLanguage = (path: string | null): string => {
    if (!path) return 'plaintext';
    const ext = path.split('.').pop();
    const languageMap: { [key: string]: string } = {
      ts: 'typescript',
      tsx: 'typescript',
      js: 'javascript',
      jsx: 'javascript',
      py: 'python',
      json: 'json',
      html: 'html',
      css: 'css',
      md: 'markdown',
    };
    return languageMap[ext || ''] || 'plaintext';
  };

  if (!filePath) {
    return (
      <div className="editor-welcome">
        <div className="welcome-content">
          <h1>DevSwarm IDE</h1>
          <p>Select a file from the explorer to start editing</p>
        </div>
      </div>
    );
  }

  return (
    <Editor
      height="100%"
      defaultLanguage={getLanguage(filePath)}
      value={content}
      onChange={(value) => onContentChange?.(value || '')}
      theme="vs-dark"
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        lineHeight: 1.5,
        scrollBeyondLastLine: false,
        fontFamily: "'Fira Code', 'Consolas', monospace",
        wordWrap: 'on',
        automaticLayout: true,
      }}
    />
  );
}

// Styling
import '../styles/Editor.css';
