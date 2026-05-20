/**
 * Conversation Panel - Displays chat messages and agent responses
 */
import "../styles/ConversationPanel.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export interface Message {
  id: string;
  type: "user" | "agent" | "question" | "system" | "greeting";
  content: string;
  timestamp: number;
  agentName?: string;
  agentType?: string;
}

interface ConversationPanelProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function ConversationPanel({
  messages,
  isLoading = false,
}: ConversationPanelProps) {
  return (
    <div className="conversation-panel">
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"></div>
            <h2>DevSwarm Intelligence Platform</h2>
            <p><strong></strong></p>
            <ul style={{ textAlign: 'left', fontSize: '13px', color: '#a0d8ff', lineHeight: '1.6' }}>
            </ul>
            <p className="empty-hint" style={{ marginTop: '12px' }}>Start by describing what you want to build...</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.type}`}>
              {msg.type === "question" && (
                <div className="message-icon">❓</div>
              )}
              {msg.type === "agent" && (
                <div className="message-icon">🤖</div>
              )}
              {msg.type === "greeting" && (
                <div className="message-icon">🚀</div>
              )}
              {msg.type === "user" && (
                <div className="message-icon">👤</div>
              )}
              {msg.type === "system" && (
                <div className="message-icon">⚙️</div>
              )}

              <div className="message-content">
                {msg.agentName && msg.type !== "user" && (
                  <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#5ba3d0', marginBottom: '4px' }}>
                    {msg.agentName}
                  </div>
                )}
                {/* Render markdown for agent responses, plain text for others */}
                {(msg.type === "agent" || msg.type === "system") && msg.content.includes("#") ? (
                  <div className="markdown-content">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({node, ...props}) => <h1 style={{ fontSize: '1.8em', marginTop: '12px', marginBottom: '8px' }} {...props} />,
                        h2: ({node, ...props}) => <h2 style={{ fontSize: '1.4em', marginTop: '10px', marginBottom: '6px' }} {...props} />,
                        h3: ({node, ...props}) => <h3 style={{ fontSize: '1.2em', marginTop: '8px', marginBottom: '4px' }} {...props} />,
                        p: ({node, ...props}) => <p style={{ marginBottom: '8px', lineHeight: '1.5' }} {...props} />,
                        ul: ({node, ...props}) => <ul style={{ marginLeft: '20px', marginBottom: '8px' }} {...props} />,
                        ol: ({node, ...props}) => <ol style={{ marginLeft: '20px', marginBottom: '8px' }} {...props} />,
                        li: ({node, ...props}) => <li style={{ marginBottom: '4px' }} {...props} />,
                        table: ({node, ...props}) => <table style={{ borderCollapse: 'collapse', marginBottom: '8px', width: '100%' }} {...props} />,
                        th: ({node, ...props}) => <th style={{ border: '1px solid #444', padding: '8px', textAlign: 'left', backgroundColor: '#1a2332' }} {...props} />,
                        td: ({node, ...props}) => <td style={{ border: '1px solid #444', padding: '8px' }} {...props} />,
                        code: ({node, inline, ...props}: any) => inline ? 
                          <code style={{ backgroundColor: '#1a2332', padding: '2px 6px', borderRadius: '3px', color: '#5ba3d0' }} {...props} /> :
                          <code style={{ backgroundColor: '#1a2332', padding: '8px', borderRadius: '3px', display: 'block', marginBottom: '8px', overflow: 'auto' }} {...props} />,
                        blockquote: ({node, ...props}) => <blockquote style={{ borderLeft: '4px solid #5ba3d0', paddingLeft: '12px', marginLeft: '0', marginBottom: '8px', color: '#a0d8ff' }} {...props} />,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="message message-system loading">
            <div className="loading-spinner"></div>
            <p>Processing...</p>
          </div>
        )}
      </div>
    </div>
  );
}
